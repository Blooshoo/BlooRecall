"""Tests for the benchmark harness: metrics, grep baseline, splits, manifest,
the chunker_override ablation switch, and BlooRecallSystem end-to-end with a
fake embedder (no Ollama needed).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench import metrics  # noqa: E402
from bench.grep_baseline import FilenameBaseline, GrepBaseline, query_terms  # noqa: E402
from bench.manifest import parse_iso, validate  # noqa: E402
from bench.splits import read_queries, split_for  # noqa: E402

from tests.test_bloorecall import FakeEmbedder, write  # noqa: E402


class MetricsTest(unittest.TestCase):
    def test_recall_at_k(self) -> None:
        graded = {"a.md": 2, "b.md": 1}
        self.assertEqual(metrics.recall_at_k(["a.md"], graded, 1), 1.0)
        self.assertEqual(metrics.recall_at_k(["x.md", "b.md"], graded, 1), 0.0)
        self.assertEqual(metrics.recall_at_k(["x.md", "b.md"], graded, 2), 1.0)

    def test_mrr_at_k(self) -> None:
        graded = {"a.md": 1}
        self.assertEqual(metrics.mrr_at_k(["a.md"], graded), 1.0)
        self.assertEqual(metrics.mrr_at_k(["x.md", "y.md", "a.md"], graded), 1 / 3)
        self.assertEqual(metrics.mrr_at_k(["x.md"] * 12, graded), 0.0)

    def test_ndcg_at_k_graded(self) -> None:
        # Perfect ranking of {best: 2, good: 1}: DCG = (3 + 1/log2(3)) / same = 1.
        graded = {"a.md": 2, "b.md": 1}
        self.assertAlmostEqual(metrics.ndcg_at_k(["a.md", "b.md"], graded), 1.0)
        # Swapped order is penalized.
        swapped = metrics.ndcg_at_k(["b.md", "a.md"], graded)
        self.assertLess(swapped, 1.0)
        self.assertGreater(swapped, 0.0)
        # A grade-2 doc alone beats a grade-1 doc alone.
        self.assertGreater(
            metrics.ndcg_at_k(["a.md"], graded), metrics.ndcg_at_k(["b.md"], graded)
        )

    def test_per_query_metric_keys(self) -> None:
        row = metrics.per_query_metrics(["a.md"], {"a.md": 1})
        self.assertEqual(sorted(row), sorted(metrics.METRIC_NAMES))

    def test_bootstrap_ci_deterministic_and_sane(self) -> None:
        rows = [
            {"metrics": metrics.per_query_metrics(["a.md"], {"a.md": 1})} for _ in range(30)
        ] + [{"metrics": metrics.per_query_metrics([], {})} for _ in range(20)]
        flat = [row["metrics"] for row in rows]
        first = metrics.bootstrap_ci(flat)
        second = metrics.bootstrap_ci(flat)
        self.assertEqual(first, second)
        for name in metrics.METRIC_NAMES:
            low, high = first[name]
            point = metrics.aggregate(flat)[name]
            self.assertLessEqual(low, point + 1e-9, name)
            self.assertGreaterEqual(high, point - 1e-9, name)
            self.assertLessEqual(low, high, name)

    def test_latency_percentiles(self) -> None:
        stats = metrics.latency_percentiles([10.0, 20.0, 30.0, 40.0, 100.0])
        self.assertEqual(stats["p50"], 30.0)
        self.assertEqual(stats["p95"], 100.0)
        self.assertAlmostEqual(stats["mean"], 40.0)


class QueryTermsTest(unittest.TestCase):
    def test_stopwords_dropped(self) -> None:
        terms = query_terms("How do we retry a dropped socket?")
        self.assertEqual(terms, ["retry", "dropped", "socket"])

    def test_identifiers_survive(self) -> None:
        self.assertIn("err_quota_429", query_terms("what is ERR_QUOTA_429 again"))


class GrepBaselineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = Path(tempfile.mkdtemp(prefix="bench-grep-"))
        self.addCleanup(shutil.rmtree, self.corpus, True)
        write(self.corpus / "docs" / "retry.md", "# Retry\n\nthe gateway uses backoff\nand backoff again\n")
        write(self.corpus / "docs" / "socket.md", "# Socket\n\nsocket plumbing only, no retries here\n")
        write(self.corpus / "docs" / "unrelated.md", "# Other\n\nnothing to see\n")
        self.grep = GrepBaseline([self.corpus], [".md"])
        self.grep.setup(self.corpus)

    def test_distinct_terms_beat_total_hits(self) -> None:
        ranked = self.grep.search("retry backoff", top_k=10)
        # socket.md says "retries" — no substring hit for "retry" — so only
        # retry.md matches both terms and nothing else matches any.
        self.assertEqual(ranked, ["docs/retry.md"])

    def test_more_distinct_terms_win_over_more_hits(self) -> None:
        corpus = Path(tempfile.mkdtemp(prefix="bench-grep2-"))
        self.addCleanup(shutil.rmtree, corpus, True)
        write(corpus / "many-hits-one-term.md", "retry\nretry\nretry\nretry\n")
        write(corpus / "one-hit-two-terms.md", "retry and backoff\n")
        grep = GrepBaseline([corpus], [".md"])
        grep.setup(corpus)
        ranked = grep.search("retry backoff", top_k=10)
        self.assertEqual(ranked[0], "one-hit-two-terms.md")

    def test_case_insensitive(self) -> None:
        write(self.corpus / "docs" / "caps.md", "RETRY the thing\n")
        self.grep.setup(self.corpus)
        self.assertIn("docs/caps.md", self.grep.search("retry", top_k=10))

    def test_filename_baseline(self) -> None:
        write(self.corpus / "docs" / "kangaroo-notes.md", "nothing relevant inside\n")
        baseline = FilenameBaseline([self.corpus], [".md"])
        baseline.setup(self.corpus)
        ranked = baseline.search("kangaroo", top_k=10)
        self.assertEqual(ranked, ["docs/kangaroo-notes.md"])


class SplitsTest(unittest.TestCase):
    def test_split_is_id_only(self) -> None:
        self.assertEqual(split_for("q-001"), split_for("q-001"))

    def test_split_is_roughly_30_70(self) -> None:
        ids = [f"q-{i:03d}" for i in range(1000)]
        dev = sum(1 for qid in ids if split_for(qid) == "dev")
        self.assertGreater(dev, 250)
        self.assertLess(dev, 350)

    def test_read_queries_skips_blank_lines(self) -> None:
        path = Path(tempfile.mkstemp(suffix=".jsonl")[1])
        path.write_text('{"id": "a"}\n\n{"id": "b"}\n', encoding="utf-8")
        self.assertEqual([q["id"] for q in read_queries(path)], ["a", "b"])
        path.unlink()


class ManifestTest(unittest.TestCase):
    def test_parse_iso(self) -> None:
        self.assertEqual(parse_iso("2026-01-02T03:04:05Z"), parse_iso("2026-01-02T03:04:05+00:00"))
        self.assertLess(parse_iso("2025-10-01T00:00:00Z"), parse_iso("2026-03-01T00:00:00Z"))

    def test_validate_flags_superseded_ordering(self) -> None:
        import bench.manifest as manifest_module

        corpus = Path(tempfile.mkdtemp(prefix="bench-manifest-"))
        self.addCleanup(shutil.rmtree, corpus, True)
        write(corpus / "old.md", "old")
        write(corpus / "new.md", "new")
        entries = [
            {
                "path": "old.md",
                "project": "toy",
                "intended_mtime": "2026-05-01T00:00:00Z",
                "planted": ["superseded"],
                "overridden_by": "new.md",
            },
            {
                "path": "new.md",
                "project": "toy",
                "intended_mtime": "2026-01-01T00:00:00Z",
                "planted": [],
            },
        ]
        original_corpus, original_manifest = manifest_module.CORPUS_DIR, manifest_module.MANIFEST_PATH
        manifest_module.CORPUS_DIR = corpus
        manifest_module.MANIFEST_PATH = corpus / "MANIFEST.json"
        manifest_module.MANIFEST_PATH.write_text(json.dumps(entries), encoding="utf-8")
        try:
            problems = validate()
        finally:
            manifest_module.CORPUS_DIR, manifest_module.MANIFEST_PATH = original_corpus, original_manifest
        self.assertTrue(any("superseded doc is not older" in p for p in problems))


class ChunkerOverrideTest(unittest.TestCase):
    """The opt-in plain-chunk switch used by the hybrid-noheadings ablation."""

    def setUp(self) -> None:
        self.corpus = Path(tempfile.mkdtemp(prefix="bench-override-"))
        self.addCleanup(shutil.rmtree, self.corpus, True)
        from bloorecall.util import PROJECT_ROOT

        (PROJECT_ROOT / "var").mkdir(exist_ok=True)
        self.index_dir = Path(tempfile.mkdtemp(prefix="bench-index-", dir=PROJECT_ROOT / "var"))
        self.addCleanup(shutil.rmtree, self.index_dir, True)
        write(
            self.corpus / "note.md",
            "# Outer\n\nintro paragraph\n\n## Breadcrumbs\n\nthe topic words live here\n",
        )
        from bloorecall.config import default_config

        self.config = default_config([{"path": str(self.corpus), "label": "toy", "max_files": 100}])
        self.config["index_path"] = str(self.index_dir / "index.sqlite3")
        self.config["_config_path"] = str(self.index_dir / "config.json")

    def _refresh(self) -> list[str]:
        from bloorecall.indexer import refresh

        refresh(self.config, full=True, embedder=FakeEmbedder())
        from bloorecall.search import BlooRecallIndex
        from bloorecall.config import index_path

        index = BlooRecallIndex(index_path(self.config))
        return index.texts

    def test_default_chunker_adds_breadcrumbs(self) -> None:
        texts = self._refresh()
        self.assertTrue(any("Outer > Breadcrumbs" in text for text in texts))

    def test_plain_override_drops_breadcrumbs(self) -> None:
        self.config["chunker_override"] = "plain"
        texts = self._refresh()
        self.assertFalse(any(" > " in text for text in texts))
        self.assertTrue(any("the topic words live here" in text for text in texts))

    def test_unknown_override_raises(self) -> None:
        self.config["chunker_override"] = "bogus"
        from bloorecall.indexer import refresh

        with self.assertRaises(ValueError):
            refresh(self.config, full=True, embedder=FakeEmbedder())


class BlooRecallSystemTest(unittest.TestCase):
    """End-to-end through the bench system interface, fake embedder, no Ollama."""

    def setUp(self) -> None:
        from bloorecall.util import PROJECT_ROOT

        # Corpus OUTSIDE the project (BlooRecall refuses self-ingestion), index
        # under var/ (ensure_write_target requires that) — the same shape as
        # the real benchmark run, which mirrors bench/corpus to a temp dir.
        self.corpus = Path(tempfile.mkdtemp(prefix="bench-system-corpus-"))
        self.addCleanup(shutil.rmtree, self.corpus, True)
        (PROJECT_ROOT / "var").mkdir(exist_ok=True)
        self.work = Path(tempfile.mkdtemp(prefix="bench-system-", dir=PROJECT_ROOT / "var"))
        self.addCleanup(shutil.rmtree, self.work, True)
        self.index_dir = self.work / "index"
        write(
            self.corpus / "a.md",
            "# Retry policy\n\nThe gateway reconnects with exponential backoff and jitter.\n",
        )
        write(self.corpus / "b.md", "# Recipes\n\nSourdough hydration sits at seventy percent.\n")
        from bench.systems import BlooRecallSystem, resolve_config

        raw = json.loads((PROJECT_ROOT / "bench" / "config.bench.json").read_text(encoding="utf-8"))
        raw["corpus_roots"] = [{"path": str(self.corpus), "label": "toy", "max_files": 100}]
        raw["index_path"] = str(self.index_dir / "index.sqlite3")
        raw["_config_path"] = str(self.index_dir / "config.json")
        self.config = raw
        self.resolve_config = resolve_config
        self.BlooRecallSystem = BlooRecallSystem

    def test_hybrid_ranks_the_right_file_first(self) -> None:
        system = self.BlooRecallSystem(
            self.config, "hybrid", policy_name="baseline-v0", embed_query=True
        )
        summary = system.setup(fresh=True, embedder=FakeEmbedder())
        self.assertFalse(summary.get("reused_existing", False))
        ranked = system.search("how does the gateway retry a dropped connection", top_k=2)
        self.assertEqual(ranked[0], "bench/corpus/a.md")

    def test_bm25_runs_without_an_embedder(self) -> None:
        system = self.BlooRecallSystem(
            self.config, "bm25", policy_name="bench-bm25", embed_query=False
        )
        system.setup(fresh=True, embedder=FakeEmbedder())
        self.assertIsNone(system.embedder)
        ranked = system.search("sourdough hydration", top_k=2)
        self.assertEqual(ranked[0], "bench/corpus/b.md")


if __name__ == "__main__":
    unittest.main()
