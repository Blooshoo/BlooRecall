from __future__ import annotations

import io
import json
import math
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bloorecall import store  # noqa: E402
from bloorecall.config import active_policy, index_path, load_config, manifest_path  # noqa: E402
from bloorecall.corpus import chunk_markdown, chunk_text, secret_reason, walk_corpus  # noqa: E402
from bloorecall.embeddings import EmbeddingUnavailable, OllamaEmbedder  # noqa: E402
from bloorecall.indexer import refresh  # noqa: E402
from bloorecall.search import (  # noqa: E402
    PrivateQueryRefused,
    SearchEngine,
    _dense_scale,
    _rrf,
    keyword_terms,
    snippet_for,
)
from bloorecall.util import PROJECT_ROOT, TOKENIZER_VERSION, ensure_write_target, tokens  # noqa: E402


class FakeEmbedder:
    """Deterministic bag-of-words vectors: no network, but real lexical geometry."""

    model = "fake-embed:test"
    batch_size = 8
    dimension = 64

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in tokens(text):
            vector[hash_token(token) % self.dimension] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector] if magnitude else vector


class DownEmbedder(FakeEmbedder):
    """Simulates Ollama being stopped: every query embedding fails."""

    def embed_one(self, text: str) -> list[float]:
        raise EmbeddingUnavailable("ollama is not running")


def hash_token(token: str) -> int:
    total = 0
    for character in token:
        total = (total * 131 + ord(character)) % 1_000_003
    return total


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class CorpusHarness(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = Path(tempfile.mkdtemp(prefix="bloorecall-corpus-"))
        # The index must live under the project root (ensure_write_target), and var/ is gitignored,
        # so it may not exist in a fresh clone — create it before carving out a temp index dir.
        (PROJECT_ROOT / "var").mkdir(exist_ok=True)
        self.index_dir = Path(tempfile.mkdtemp(prefix="bloorecall-index-", dir=PROJECT_ROOT / "var"))
        self.addCleanup(shutil.rmtree, self.corpus, True)
        self.addCleanup(shutil.rmtree, self.index_dir, True)
        write(
            self.corpus / "docs" / "websocket-retry.md",
            "# WebSocket retry\n\nThe gateway reconnects with exponential backoff and jitter.\n"
            "\n\nRetry budget is capped at five attempts before the socket is dropped.\n",
        )
        write(
            self.corpus / "docs" / "backup-runbook.md",
            "# Backup runbook\n\nRestic snapshots run nightly against the estate repository.\n",
        )
        write(self.corpus / "notes" / "grocery.txt", "milk, oat flour, chilli oil\n")
        self.config = self.make_config()

    def make_config(self, **overrides) -> dict:
        config = {
            "config_version": "test",
            "index_format": "bloorecall-sqlite-v2",
            "parse_version": "bloorecall-chunker-v1",
            "index_path": str((self.index_dir / "index.sqlite3").relative_to(PROJECT_ROOT)),
            "embedding": {"model": FakeEmbedder.model, "batch_size": 8},
            "corpus_roots": [{"path": str(self.corpus), "label": "testcorpus", "max_files": 50}],
            "allowed_extensions": [".md", ".txt"],
            "max_file_bytes": 262144,
            "chunk_chars": 400,
            "chunk_overlap_chars": 60,
            "exclusions": {
                "denied_path_parts": ["secrets", "node_modules"],
                "denied_name_fragments": [".env", "credential"],
                "denied_globs": ["*/skipme/*"],
            },
            "active_policy": "baseline-v0",
            "policies": {
                "baseline-v0": {
                    "policy_id": "baseline-v0",
                    "dense_weight": 0.55,
                    "recency_weight": 0.05,
                    "metadata_weight": 0.15,
                    "rerank_budget": 20,
                    "top_k": 10,
                }
            },
            "search_defaults": {"top_k": 5, "max_top_k": 20, "snippet_chars": 200},
            "vector_cache_days": 14,
            "_config_path": "test",
        }
        config.update(overrides)
        return config

    def refresh(self, **kwargs) -> dict:
        return refresh(self.config, embedder=FakeEmbedder(), **kwargs)

    def engine(self) -> SearchEngine:
        return SearchEngine(self.config, embedder=FakeEmbedder())


class TestExclusions(CorpusHarness):
    def test_safety_gates_reject_sensitive_material(self) -> None:
        write(self.corpus / "secrets" / "vault.md", "nothing to see")
        write(self.corpus / ".env.md", "TOKEN=abc")
        write(self.corpus / "credential-notes.md", "notes")
        write(self.corpus / "skipme" / "ignored.md", "ignored")
        write(self.corpus / "code.py", "print('not a doc')")
        result = walk_corpus(self.config)
        paths = {source.path.name for source in result.sources}
        self.assertEqual(paths, {"websocket-retry.md", "backup-runbook.md", "grocery.txt"})
        reasons = {row["reason"] for row in result.rejections}
        self.assertIn("denied path segment: secrets", reasons)
        self.assertIn("sensitive filename", reasons)
        self.assertIn("denied glob", reasons)

    def test_symlinks_are_not_followed(self) -> None:
        target = write(self.corpus / "docs" / "websocket-retry.md", "x" * 50)
        link = self.corpus / "docs" / "alias.md"
        os.symlink(target, link)
        result = walk_corpus(self.config)
        self.assertNotIn("alias.md", {source.path.name for source in result.sources})

    def test_secret_content_is_blocked_and_evicted(self) -> None:
        self.refresh()
        leak = write(self.corpus / "docs" / "backup-runbook.md", "key\n\nAKIA1234567890ABCDEF is live\n")
        summary = self.refresh()
        self.assertEqual(summary["secret_blocked"], 1)
        self.assertEqual(summary["removed"], 1)
        connection = store.connect_read(index_path(self.config))
        try:
            remaining = {row[0] for row in connection.execute("SELECT canonical_path FROM sources")}
        finally:
            connection.close()
        self.assertNotIn(str(leak), remaining)

    def test_secret_reason_detects_known_shapes(self) -> None:
        self.assertIsNotNone(secret_reason("-----BEGIN OPENSSH PRIVATE KEY-----"))
        self.assertIsNone(secret_reason("this document merely mentions keys"))

    def test_writes_outside_the_project_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            ensure_write_target(Path("/tmp/bloorecall-escape.sqlite3"))


class TestChunker(CorpusHarness):
    def test_paragraph_packing_is_deterministic(self) -> None:
        text = "\n\n".join(f"paragraph {number} " + "word " * 30 for number in range(6))
        first = chunk_text(text, 400, 60)
        self.assertEqual(first, chunk_text(text, 400, 60))
        self.assertTrue(all(len(chunk) <= 400 for chunk in first))

    def test_oversized_paragraph_is_split(self) -> None:
        chunks = chunk_text("z" * 1000, 400, 60)
        self.assertGreater(len(chunks), 1)

    def test_markdown_chunks_carry_their_heading_breadcrumb(self) -> None:
        doc = "# Design\n\nIntro.\n\n## Phased build\n\n### P0\n\nrun it this weekend.\n"
        chunks = chunk_markdown(doc, 400, 60)
        deepest = next(chunk for chunk in chunks if "run it this weekend" in chunk)
        self.assertTrue(deepest.startswith("Design > Phased build > P0\n"))
        # Every chunk stays within the configured size including its breadcrumb line.
        self.assertTrue(all(len(chunk) <= 400 for chunk in chunks))

    def test_markdown_without_headings_falls_back_to_plain_chunks(self) -> None:
        body = "Just a paragraph.\n\nAnd another one.\n"
        self.assertEqual(chunk_markdown(body, 400, 60), chunk_text(body, 400, 60))


class TestTokenizer(unittest.TestCase):
    def test_a_sentence_ending_word_is_the_same_token(self) -> None:
        self.assertEqual(tokens("Uses backoff. Status: done."), ["uses", "backoff", "status", "done"])

    def test_identifiers_stay_whole(self) -> None:
        text = "set retry_policy.max_attempts in docs/setup.md (v1.2.3), see ERR_QUOTA_429."
        self.assertEqual(
            tokens(text),
            ["set", "retry_policy.max_attempts", "in", "docs/setup.md", "v1.2.3", "see", "err_quota_429"],
        )


class TestRefresh(CorpusHarness):
    def test_first_run_indexes_everything(self) -> None:
        summary = self.refresh()
        self.assertEqual(summary["source_count"], 3)
        self.assertEqual(summary["added"], 3)
        self.assertGreater(summary["chunk_count"], 0)
        self.assertTrue(manifest_path(self.config).exists())
        rows = [
            json.loads(line)
            for line in manifest_path(self.config).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["permissions"] == "local_owner_only" for row in rows))
        self.assertTrue(all(row["content_hash"] and row["project"] for row in rows))

    def test_second_run_is_idempotent(self) -> None:
        first = self.refresh()
        second = self.refresh()
        self.assertEqual(second["unchanged"], 3)
        self.assertEqual(second.get("added", 0), 0)
        self.assertEqual(second["chunks_embedded"], 0)
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
        self.assertEqual(first["chunk_count"], second["chunk_count"])

    def test_changed_file_is_reindexed_and_deleted_file_is_dropped(self) -> None:
        first = self.refresh()
        changed = self.corpus / "docs" / "websocket-retry.md"
        write(changed, "# WebSocket retry\n\nNow documents a fixed one second retry delay.\n")
        os.utime(changed, (1_760_000_000, 1_760_000_000))
        second = self.refresh()
        self.assertEqual(second["reindexed"], 1)
        self.assertEqual(second["unchanged"], 2)
        self.assertNotEqual(first["manifest_sha256"], second["manifest_sha256"])

        (self.corpus / "notes" / "grocery.txt").unlink()
        third = self.refresh()
        self.assertEqual(third["removed"], 1)
        self.assertEqual(third["source_count"], 2)

    def test_touch_without_edit_does_not_reembed(self) -> None:
        self.refresh()
        os.utime(self.corpus / "docs" / "backup-runbook.md", (1_770_000_000, 1_770_000_000))
        summary = self.refresh()
        self.assertEqual(summary["touched"], 1)
        self.assertEqual(summary["chunks_embedded"], 0)

    def test_embedding_cache_serves_repeated_text(self) -> None:
        self.refresh()
        original = (self.corpus / "docs" / "websocket-retry.md").read_text(encoding="utf-8")
        write(self.corpus / "docs" / "websocket-retry-copy.md", original)
        summary = self.refresh()
        self.assertEqual(summary["added"], 1)
        self.assertEqual(summary["chunks_embedded"], 0)
        self.assertGreater(summary["chunks_reused_from_cache"], 0)

    def test_missing_root_does_not_delete_indexed_files(self) -> None:
        self.refresh()
        self.config["corpus_roots"].append({"path": "/nonexistent/bloorecall-root", "label": "gone"})
        summary = self.refresh()
        self.assertEqual(summary["removed"], 0)
        self.assertEqual(summary["source_count"], 3)
        self.assertIn("/nonexistent/bloorecall-root", summary["missing_roots"])

    def test_full_rebuild_reproduces_the_manifest(self) -> None:
        first = self.refresh()
        second = self.refresh(full=True)
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])

    def test_editing_a_long_untouched_file_reembeds_only_the_changed_chunk(self) -> None:
        long_doc = write(
            self.corpus / "docs" / "long.md",
            "# Long\n\n" + "\n\n".join(f"Paragraph {n}. " + "filler words " * 25 for n in range(6)),
        )
        first = self.refresh()
        self.assertGreater(first["chunk_count"], 6)
        # Three weeks without edits: every cache entry expires (vector_cache_days is 14).
        connection = sqlite3.connect(index_path(self.config))
        connection.execute("UPDATE vectors SET last_used = last_used - 21 * 86400")
        connection.commit()
        connection.close()
        self.assertGreater(self.refresh()["vectors_pruned"], 0)
        long_doc.write_text(long_doc.read_text().replace("Paragraph 3.", "Paragraph three."))
        summary = self.refresh()
        self.assertEqual(summary["reindexed"], 1)
        self.assertEqual(summary["chunks_embedded"], 1)

    def test_an_index_from_the_old_tokenizer_is_retokenized_without_reembedding(self) -> None:
        self.refresh()
        # Rewind the index to v1.1: trailing punctuation kept in stored terms, no version stamp.
        connection = sqlite3.connect(index_path(self.config))
        for chunk_id, text in connection.execute("SELECT chunk_id, text FROM chunks").fetchall():
            old = {}
            for token in __import__("re").findall(r"[a-z0-9][a-z0-9_./:-]*", text.casefold()):
                old[token] = old.get(token, 0) + 1
            connection.execute(
                "UPDATE chunks SET term_counts_json = ?, token_count = ? WHERE chunk_id = ?",
                (json.dumps(old), sum(old.values()), chunk_id),
            )
        connection.execute("DELETE FROM metadata WHERE key = 'tokenizer_version'")
        connection.commit()
        connection.close()

        # "jitter" only ever ends a sentence in the corpus, so v1.1 stored it as "jitter.".
        down = SearchEngine(self.config, embedder=DownEmbedder())
        paths = [row["path"] for row in down.search("jitter")["results"]]
        self.assertTrue(paths and paths[0].endswith("websocket-retry.md"))

        summary = self.refresh()
        self.assertEqual(summary["retokenized"], summary["chunk_count"])
        self.assertEqual(summary["chunks_embedded"], 0)
        connection = store.connect_read(index_path(self.config))
        try:
            self.assertEqual(store.read_metadata(connection)["tokenizer_version"], TOKENIZER_VERSION)
            stored = " ".join(row[0] for row in connection.execute("SELECT term_counts_json FROM chunks"))
        finally:
            connection.close()
        self.assertIn('"jitter"', stored)
        self.assertNotIn('"jitter."', stored)

    def test_a_root_dropped_from_the_config_takes_its_files_with_it(self) -> None:
        other = Path(tempfile.mkdtemp(prefix="bloorecall-other-"))
        self.addCleanup(shutil.rmtree, other, True)
        write(other / "kitchen.md", "# Kitchen\n\nThe oven runs hot.\n")
        self.config["corpus_roots"].append({"path": str(other), "label": "other"})
        self.assertEqual(self.refresh()["source_count"], 4)
        self.config["corpus_roots"].pop()
        summary = self.refresh()
        self.assertEqual(summary["removed"], 1)
        self.assertEqual(summary["source_count"], 3)


class TestSearch(CorpusHarness):
    def test_query_finds_the_right_file(self) -> None:
        self.refresh()
        payload = self.engine().search("websocket reconnect backoff", top_k=3)
        self.assertTrue(payload["results"])
        self.assertTrue(payload["results"][0]["path"].endswith("websocket-retry.md"))
        self.assertTrue(payload["results"][0]["snippet"])
        self.assertEqual(payload["results"][0]["project"], "testcorpus/docs")

    def test_results_are_deterministic_and_deduplicated_by_path(self) -> None:
        self.refresh()
        engine = self.engine()
        first = engine.search("restic nightly snapshots", top_k=5)
        second = engine.search("restic nightly snapshots", top_k=5)
        self.assertEqual(
            [row["path"] for row in first["results"]], [row["path"] for row in second["results"]]
        )
        paths = [row["path"] for row in first["results"]]
        self.assertEqual(len(paths), len(set(paths)))

    def test_top_k_is_clamped_to_the_configured_maximum(self) -> None:
        self.refresh()
        payload = self.engine().search("retry", top_k=999)
        self.assertEqual(payload["top_k"], 20)

    def test_project_filter_narrows_results(self) -> None:
        self.refresh()
        payload = self.engine().search("retry backoff", project="notes")
        self.assertTrue(all("notes" in row["project"] for row in payload["results"]))

    def test_project_filter_never_starves_a_small_project(self) -> None:
        # Many strong matches in docs/ used to fill the over-fetch window, so a
        # filtered search for the one weaker match in notes/ came back empty.
        for index in range(30):
            write(
                self.corpus / "docs" / f"retry-{index}.md",
                f"# Retry note {index}\n\nretry retry retry backoff retry jitter retry\n",
            )
        write(self.corpus / "notes" / "retry-todo.txt", "remember to look at the retry setting\n")
        self.refresh()
        payload = self.engine().search("retry", top_k=1, project="notes")
        self.assertEqual(len(payload["results"]), 1)
        self.assertTrue(payload["results"][0]["path"].endswith("retry-todo.txt"))

    def test_search_falls_back_to_keyword_only_when_embeddings_are_down(self) -> None:
        self.refresh()
        engine = SearchEngine(self.config, embedder=DownEmbedder())
        payload = engine.search("websocket retry backoff")
        self.assertEqual(payload["retrieval"], "keyword-only")
        self.assertTrue(payload["results"][0]["path"].endswith("websocket-retry.md"))
        self.assertEqual(self.engine().search("websocket retry backoff")["retrieval"], "hybrid")

    def test_credential_shaped_queries_are_refused(self) -> None:
        self.refresh()
        with self.assertRaises(PrivateQueryRefused):
            self.engine().search("where is the discord api key")

    def test_index_reloads_after_a_refresh(self) -> None:
        self.refresh()
        engine = self.engine()
        self.assertEqual(len(engine.search("retry", top_k=10)["results"]), 3)
        write(self.corpus / "docs" / "new-note.md", "# Kafka consumer lag\n\nLag alerts fire at 5k.\n")
        self.refresh()
        paths = [row["path"] for row in engine.search("kafka consumer lag", top_k=10)["results"]]
        self.assertTrue(any(path.endswith("new-note.md") for path in paths))

    def test_minmax_fusion_lets_meaning_beat_a_lone_keyword_hit(self) -> None:
        # A paraphrase in miniature: the query's meaning (its vector) is the websocket note,
        # but its only keyword hits the backup runbook. Recency, metadata and re-rank are
        # off so the blend itself decides.
        self.refresh()
        index = self.engine().index
        vector = FakeEmbedder().embed_one(
            "WebSocket retry gateway reconnects exponential backoff jitter budget attempts socket"
        )
        policy = {
            "policy_id": "t", "dense_weight": 0.55, "recency_weight": 0.0,
            "metadata_weight": 0.0, "rerank_budget": 0, "top_k": 3,
        }

        def top(fusion: str) -> str:
            return index.rank("restic", vector, {**policy, "fusion": fusion})[0]["path"]

        # (cos+1)/2 hands every chunk at least ~0.5 of the dense weight, so BM25's max-normalized
        # 1.0 on the keyword hit outweighs a perfect embedding match.
        self.assertTrue(top("raw").endswith("backup-runbook.md"))
        self.assertTrue(top("minmax").endswith("websocket-retry.md"))

    def test_policy_without_fusion_ranks_exactly_like_raw(self) -> None:
        self.refresh()
        index = self.engine().index
        policy = active_policy(self.config)
        vector = FakeEmbedder().embed_one("websocket backoff")
        legacy = index.rank("websocket backoff", vector, policy)
        explicit = index.rank("websocket backoff", vector, {**policy, "fusion": "raw"})
        self.assertEqual(legacy, explicit)

    def test_rrf_policy_finds_the_right_file(self) -> None:
        policy = {
            "policy_id": "hybrid-rrf-v1", "fusion": "rrf", "dense_weight": 0.5, "rrf_k": 60,
            "recency_weight": 0.05, "metadata_weight": 0.15, "rerank_budget": 20, "top_k": 10,
        }
        self.config = self.make_config(active_policy="hybrid-rrf-v1", policies={"hybrid-rrf-v1": policy})
        self.refresh()
        payload = self.engine().search("websocket reconnect backoff", top_k=3)
        self.assertEqual(payload["policy"], "hybrid-rrf-v1")
        self.assertTrue(payload["results"][0]["path"].endswith("websocket-retry.md"))

    def test_path_terms_are_words_below_the_corpus_root(self) -> None:
        self.refresh()
        index = self.engine().index
        websocket = next(path for path in index.path_terms if path.endswith("websocket-retry.md"))
        # Project label and folders/stem under the root; nothing from the temp dir above it.
        self.assertEqual(index.path_terms[websocket], {"testcorpus", "docs", "websocket", "retry"})

    def test_a_folder_named_in_the_query_breaks_a_tie(self) -> None:
        for folder in ("gateway", "kitchen"):
            note = write(self.corpus / folder / "notes.md", "# Notes\n\nThe retry budget is five attempts.\n")
            os.utime(note, (1_760_000_000, 1_760_000_000))
        self.refresh()
        top = self.engine().search("kitchen retry budget", top_k=2)["results"][0]
        self.assertTrue(top["path"].endswith("kitchen/notes.md"))

    def test_keyword_only_search_does_not_pad_with_unmatched_files(self) -> None:
        self.refresh()
        payload = SearchEngine(self.config, embedder=DownEmbedder()).search("xylophone quartet")
        self.assertEqual(payload["retrieval"], "keyword-only")
        self.assertEqual(payload["results"], [])

    def test_an_index_from_another_model_falls_back_to_keyword_only(self) -> None:
        self.refresh()

        class OtherModel(FakeEmbedder):
            model = "other-embed:test"

        payload = SearchEngine(self.config, embedder=OtherModel()).search("websocket backoff")
        self.assertEqual(payload["retrieval"], "keyword-only")
        self.assertIn("refresh --full", payload["warning"])
        self.assertTrue(payload["results"][0]["path"].endswith("websocket-retry.md"))

    def test_a_query_vector_of_the_wrong_size_falls_back_to_keyword_only(self) -> None:
        self.refresh()

        class Resized(FakeEmbedder):
            dimension = 32

        payload = SearchEngine(self.config, embedder=Resized()).search("websocket backoff")
        self.assertEqual(payload["retrieval"], "keyword-only")
        self.assertIn("dimensions", payload["warning"])

    def test_snippet_windows_around_the_match(self) -> None:
        text = "alpha " * 100 + "the websocket retry budget is five " + "omega " * 100
        snippet = snippet_for(text, "websocket retry budget", 80)
        self.assertIn("websocket", snippet)
        self.assertLessEqual(len(snippet), 82)

    def test_snippet_follows_rare_terms_not_the_first_common_word(self) -> None:
        # Four common query words open the chunk; the two rare ones sit far below. Centring on
        # the median first mention (v1.1) showed the opening and cut the answer off.
        text = "how you get the " + "filler " * 60 + "kiln checkpoint costs 840 ms " + "filler " * 60
        weights = {"how": 0.2, "you": 0.2, "get": 0.2, "the": 0.1, "kiln": 4.0, "checkpoint": 3.5}
        snippet = snippet_for(text, "how do you get the kiln checkpoint", 120, weights)
        self.assertIn("kiln checkpoint costs 840 ms", snippet)
        self.assertLessEqual(len(snippet), 122)

    def test_term_weights_rank_rare_words_above_common_ones(self) -> None:
        self.refresh()
        weights = self.engine().index.term_weights("the restic")
        self.assertGreater(weights["restic"], weights["the"])


class TestEmbedder(unittest.TestCase):
    def test_ollama_error_text_is_passed_on(self) -> None:
        body = io.BytesIO(b'{"error":"model \\"nomic\\" not found, try pulling it first"}')
        refusal = urllib.error.HTTPError("http://x/api/embed", 404, "Not Found", {}, body)
        with mock.patch("urllib.request.urlopen", side_effect=refusal):
            with self.assertRaisesRegex(EmbeddingUnavailable, "HTTP 404: model .nomic. not found"):
                OllamaEmbedder("nomic").embed_one("hello")

    def test_a_dropped_connection_is_embedding_unavailable(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=ConnectionResetError("reset by peer")):
            with self.assertRaises(EmbeddingUnavailable):
                OllamaEmbedder("nomic").embed_one("hello")


class TestFusion(unittest.TestCase):
    # Chunk 0 is dense's pick, chunk 1 is BM25's. Cosines sit in a narrow band and BM25 spans a
    # wide one, which is exactly the shape real embedders produce.
    SIMILARITY = np.array([0.80, 0.70], dtype=np.float32)
    LEXICAL = np.array([1.0, 10.0], dtype=np.float32)

    def test_dense_weight_decides_which_list_wins(self) -> None:
        self.assertEqual(int(np.argmax(_rrf(self.SIMILARITY, self.LEXICAL, 0.9, 60))), 0)
        self.assertEqual(int(np.argmax(_rrf(self.SIMILARITY, self.LEXICAL, 0.1, 60))), 1)

    def test_raw_score_blend_lets_bm25_overrule_a_heavy_dense_weight(self) -> None:
        # The v1.0 failure RRF fixes: at 90% dense weight the linear blend still picks BM25's chunk.
        linear = 0.9 * (self.SIMILARITY + 1) / 2 + 0.1 * self.LEXICAL / self.LEXICAL.max()
        self.assertEqual(int(np.argmax(linear)), 1)

    def test_best_chunk_scores_one_and_non_matches_tie_on_keywords(self) -> None:
        fused = _rrf(np.array([0.9, 0.5, 0.1]), np.array([0.0, 0.0, 0.0]), 0.5, 60)
        self.assertAlmostEqual(float(fused.max()), 1.0, places=6)
        self.assertEqual([int(i) for i in np.argsort(-fused)], [0, 1, 2])
        self.assertTrue(np.isfinite(_rrf(np.zeros(3), np.zeros(3), 0.0, 60)).all())

    def test_no_keyword_match_ranks_like_the_weakest_match_not_below_it(self) -> None:
        # Chunk 0 is dense's clear pick but shares no word with the query; 1 and 2 share one weak
        # word each. Scoring 0 from BM25 (v1.1) put chunk 0 last, behind both weak matches.
        fused = _rrf(np.array([0.9, 0.2, 0.1]), np.array([0.0, 0.3, 0.2]), 0.5, 60)
        self.assertEqual([int(i) for i in np.argsort(-fused, kind="stable")], [1, 0, 2])

    def test_function_words_are_not_keyword_evidence(self) -> None:
        self.assertEqual(keyword_terms("How do we retry a dropped socket?"), ["retry", "dropped", "socket"])
        self.assertEqual(keyword_terms("what is it"), ["what", "is", "it"])


class TestConfig(unittest.TestCase):
    def test_shipped_example_config_loads_and_validates(self) -> None:
        # config.json is user-local (gitignored); the shipped example must stay valid.
        config = load_config(PROJECT_ROOT / "config.example.json")
        self.assertIn(config["active_policy"], config["policies"])
        self.assertTrue(str(index_path(config)).startswith(str(PROJECT_ROOT)))

    def test_missing_policy_is_rejected(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(
                {
                    "index_format": "x",
                    "parse_version": "x",
                    "index_path": "var/x.sqlite3",
                    "embedding": {"model": "m"},
                    "corpus_roots": [],
                    "allowed_extensions": [".md"],
                    "exclusions": {},
                    "active_policy": "nope",
                    "policies": {"baseline-v0": {}},
                    "search_defaults": {},
                },
                handle,
            )
            path = handle.name
        self.addCleanup(os.unlink, path)
        with self.assertRaises(RuntimeError):
            load_config(path)

    def test_unknown_fusion_is_rejected(self) -> None:
        config = json.loads((PROJECT_ROOT / "config.example.json").read_text(encoding="utf-8"))
        config["policies"][config["active_policy"]]["fusion"] = "vibes"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(config, handle)
            path = handle.name
        self.addCleanup(os.unlink, path)
        with self.assertRaisesRegex(RuntimeError, "fusion 'vibes'"):
            load_config(path)

    def test_minmax_scaling_handles_a_flat_query(self) -> None:
        flat = np.full(4, 0.3, dtype=np.float32)
        self.assertEqual(_dense_scale(flat, "minmax").tolist(), [0.0] * 4)
        spread = _dense_scale(np.array([0.2, 0.6, 0.4], dtype=np.float32), "minmax")
        np.testing.assert_allclose(spread, [0.0, 1.0, 0.5], atol=1e-6)


class TestLaunchers(unittest.TestCase):
    def test_launcher_ignores_a_bloorecall_package_in_the_working_directory(self) -> None:
        import subprocess

        decoy = Path(tempfile.mkdtemp(prefix="bloorecall-decoy-"))
        self.addCleanup(shutil.rmtree, decoy, True)
        write(decoy / "bloorecall" / "__init__.py", "raise SystemExit('decoy package imported')\n")
        result = subprocess.run(
            [str(PROJECT_ROOT / "bin" / "bloorecall"), "--help"],
            cwd=decoy, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("decoy", result.stdout + result.stderr)


class TestMcpServer(unittest.TestCase):
    def test_server_exposes_bloorecall_search(self) -> None:
        import asyncio

        from bloorecall.mcp_server import build_server

        server = build_server(str(PROJECT_ROOT / "config.example.json"))
        tools = asyncio.run(server.list_tools())
        names = {tool.name for tool in tools}
        self.assertEqual(names, {"bloorecall_search"})
        tool = next(tool for tool in tools if tool.name == "bloorecall_search")
        # mcp 1.x spells it inputSchema, 2.x input_schema.
        schema = getattr(tool, "input_schema", None) or tool.inputSchema
        self.assertIn("query", schema["properties"])
        self.assertIn("top_k", schema["properties"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
