from __future__ import annotations

import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bloorecall import store  # noqa: E402
from bloorecall.config import index_path, load_config, manifest_path  # noqa: E402
from bloorecall.corpus import chunk_markdown, chunk_text, secret_reason, walk_corpus  # noqa: E402
from bloorecall.embeddings import EmbeddingUnavailable  # noqa: E402
from bloorecall.indexer import refresh  # noqa: E402
from bloorecall.search import PrivateQueryRefused, SearchEngine, snippet_for  # noqa: E402
from bloorecall.util import PROJECT_ROOT, ensure_write_target, tokens  # noqa: E402


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

    def test_snippet_windows_around_the_match(self) -> None:
        text = "alpha " * 100 + "the websocket retry budget is five " + "omega " * 100
        snippet = snippet_for(text, "websocket retry budget", 80)
        self.assertIn("websocket", snippet)
        self.assertLessEqual(len(snippet), 82)


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


class TestMcpServer(unittest.TestCase):
    def test_server_exposes_bloorecall_search(self) -> None:
        import asyncio

        from bloorecall.mcp_server import build_server

        server = build_server(str(PROJECT_ROOT / "config.example.json"))
        tools = asyncio.run(server.list_tools())
        names = {tool.name for tool in tools}
        self.assertEqual(names, {"bloorecall_search"})
        schema = next(tool for tool in tools if tool.name == "bloorecall_search").inputSchema
        self.assertIn("query", schema["properties"])
        self.assertIn("top_k", schema["properties"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
