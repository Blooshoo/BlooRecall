#!/usr/bin/env python3
"""Tests for the Heimdall-style trust verdicts and the drift audit.

These tests reuse the CorpusHarness from test_bloorecall: a temp corpus, a real
SQLite index built with a fake embedder, no network.
"""
from __future__ import annotations

import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bloorecall import store  # noqa: E402
from bloorecall.config import index_path, load_config, manifest_path  # noqa: E402
from bloorecall.corpus import walk_corpus  # noqa: E402
from bloorecall.embeddings import OllamaEmbedder  # noqa: E402
from bloorecall.trust import TrustVerdict, verify_path  # noqa: E402
from bloorecall.verify_drift import EXIT_CLEAN, EXIT_DRIFT, EXIT_ERROR, run_drift_audit  # noqa: E402
from bloorecall.util import sha256_file, sha256_bytes, PROJECT_ROOT  # noqa: E402

# Reuse the fake embedder and harness from the main test file
from test_bloorecall import FakeEmbedder, CorpusHarness, write  # noqa: E402


class TestTrustVerdictEnum(unittest.TestCase):
    """Unit-test the TrustVerdict enum and verify_path() logic in isolation."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="bloorecall-trust-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, True))

    def test_enum_values(self) -> None:
        self.assertEqual(TrustVerdict.STRONG.value, "strong")
        self.assertEqual(TrustVerdict.WEAK.value, "weak")
        self.assertEqual(TrustVerdict.REBUILT.value, "rebuilt")
        self.assertEqual(TrustVerdict.STALE.value, "stale")
        self.assertTrue(issubclass(TrustVerdict, str))

    def test_stale_when_file_missing(self) -> None:
        path = self.tmp / "gone.md"
        result = verify_path(
            path=str(path),
            indexed_hash="abc",
            indexed_at=100.0,
            refreshed_at=100.0,
        )
        self.assertEqual(result.verdict, TrustVerdict.STALE)
        self.assertFalse(result.file_exists)
        self.assertEqual(result.reason, "file missing from disk")

    def test_strong_when_everything_matches(self) -> None:
        path = self.tmp / "present.md"
        content = b"hello world"
        path.write_bytes(content)
        content_hash = sha256_bytes(content)
        result = verify_path(
            path=str(path),
            indexed_hash=content_hash,
            indexed_at=50.0,
            refreshed_at=200.0,
        )
        self.assertEqual(result.verdict, TrustVerdict.STRONG)
        self.assertTrue(result.file_exists)
        self.assertFalse(result.just_rebuilt)

    def test_rebuilt_when_indexed_at_matches_refresh(self) -> None:
        path = self.tmp / "fresh.md"
        content = b"fresh content"
        path.write_bytes(content)
        content_hash = sha256_bytes(content)
        result = verify_path(
            path=str(path),
            indexed_hash=content_hash,
            indexed_at=1000.0,
            refreshed_at=1000.0,
        )
        self.assertEqual(result.verdict, TrustVerdict.REBUILT)
        self.assertTrue(result.just_rebuilt)

    def test_weak_on_hash_mismatch(self) -> None:
        path = self.tmp / "drifted.md"
        content = b"original"
        path.write_bytes(content)
        result = verify_path(
            path=str(path),
            indexed_hash="deadbeef" + "0" * 54,
            indexed_at=50.0,
            refreshed_at=200.0,
        )
        self.assertEqual(result.verdict, TrustVerdict.WEAK)
        self.assertIn("content hash mismatch", result.reason)


class TestSearchTrustVerdict(CorpusHarness):
    """End-to-end: search results carry a verified trust verdict."""

    def test_results_carry_trust_field(self) -> None:
        self.refresh()
        payload = self.engine().search("websocket reconnect backoff", top_k=3)
        self.assertTrue(payload["results"])
        for row in payload["results"]:
            self.assertIn("trust", row)
            self.assertIn("verdict", row["trust"])
            self.assertIn(row["trust"]["verdict"], {"strong", "rebuilt", "weak", "stale"})

    def test_verdict_is_stale_after_file_delete_without_reindex(self) -> None:
        self.refresh()
        payload = self.engine().search("websocket reconnect backoff", top_k=3)
        hit = payload["results"][0]
        self.assertIn(hit["trust"]["verdict"], {"strong", "rebuilt"})

        # Delete the top hit's file without re-indexing
        deleted = Path(hit["path"])
        deleted.unlink()

        payload2 = self.engine().search("websocket reconnect backoff", top_k=3)
        stale_hit = next(row for row in payload2["results"] if row["path"] == hit["path"])
        self.assertEqual(stale_hit["trust"]["verdict"], "stale")
        self.assertFalse(stale_hit["trust"]["file_exists"])

    def test_verdict_is_weak_after_silent_content_change_without_reindex(self) -> None:
        self.refresh()
        payload = self.engine().search("websocket retry", top_k=3)
        hit = payload["results"][0]
        original_verdict = hit["trust"]["verdict"]
        self.assertIn(original_verdict, {"strong", "rebuilt"})

        # Rewrite the file's bytes (same mtime tricks won't help — verify re-hashes)
        target = Path(hit["path"])
        target.write_text("tampered content that differs entirely from original\n")

        payload2 = self.engine().search("websocket retry", top_k=3)
        weak_hit = next(row for row in payload2["results"] if row["path"] == hit["path"])
        self.assertEqual(weak_hit["trust"]["verdict"], "weak")
        self.assertIn("content hash mismatch", weak_hit["trust"].get("reason", "") + "")

    def test_verdict_stays_strong_once_the_vector_cache_expires(self) -> None:
        # v1.1 read an expired cache entry as drift, so every file left unedited for
        # vector_cache_days (14) came back "weak" even though nothing had changed.
        self.refresh()
        connection = sqlite3.connect(index_path(self.config))
        connection.execute("UPDATE vectors SET last_used = last_used - 15 * 86400")
        connection.commit()
        connection.close()
        summary = self.refresh()
        self.assertGreater(summary["vectors_pruned"], 0)
        payload = self.engine().search("websocket reconnect backoff", top_k=3)
        self.assertIn(payload["results"][0]["trust"]["verdict"], {"strong", "rebuilt"})


class TestDriftAudit(CorpusHarness):
    """End-to-end: the drift audit script detects and reports drift."""

    def test_clean_index_exits_zero(self) -> None:
        self.refresh()
        code = run_drift_audit(self.config, deep=True, as_json=False)
        self.assertEqual(code, EXIT_CLEAN)

    def test_clean_index_json_output(self) -> None:
        self.refresh()
        from io import StringIO
        from contextlib import redirect_stdout
        buf = StringIO()
        with redirect_stdout(buf):
            code = run_drift_audit(self.config, deep=True, as_json=True)
        self.assertEqual(code, EXIT_CLEAN)
        data = json.loads(buf.getvalue().strip())
        self.assertIn("checked", data)
        self.assertIn("ghosts", data)
        self.assertEqual(data["ghosts"], [])
        self.assertEqual(data["hash_drift"], [])

    def test_deleted_file_detected_as_ghost(self) -> None:
        self.refresh()
        victim = self.corpus / "docs" / "backup-runbook.md"
        victim.unlink()
        code = run_drift_audit(self.config, deep=True, as_json=False)
        self.assertEqual(code, EXIT_DRIFT)

    def test_silent_content_rewrite_detected_as_hash_drift(self) -> None:
        self.refresh()
        # Rewrite a file without re-indexing (simulates mtime-preserving edit)
        target = self.corpus / "docs" / "websocket-retry.md"
        target.write_bytes(b"completely different bytes that were not re-indexed\n")
        code = run_drift_audit(self.config, deep=True, as_json=False)
        self.assertEqual(code, EXIT_DRIFT)

    def test_shallow_mode_misses_silent_rewrite(self) -> None:
        self.refresh()
        target = self.corpus / "docs" / "websocket-retry.md"
        before = target.stat()
        original = target.read_bytes()
        # Same size, mtime put back: only a re-hash can tell, and shallow mode only stats.
        target.write_bytes(original.replace(b"jitter", b"JITTER"))
        os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(run_drift_audit(self.config, deep=False, as_json=False), EXIT_CLEAN)
        self.assertEqual(run_drift_audit(self.config, deep=True, as_json=False), EXIT_DRIFT)

    def test_shallow_mode_catches_an_ordinary_edit(self) -> None:
        self.refresh()
        write(self.corpus / "docs" / "websocket-retry.md", "# WebSocket retry\n\nNow a fixed delay.\n")
        self.assertEqual(run_drift_audit(self.config, deep=False, as_json=False), EXIT_DRIFT)

    def test_files_refresh_refuses_are_not_unindexed_drift(self) -> None:
        write(self.corpus / "docs" / "aws.md", "# Keys\n\nAKIA1234567890ABCDEF is live\n")
        write(self.corpus / "docs" / "blank.md", "\n   \n")
        summary = self.refresh()
        self.assertEqual(summary["secret_blocked"], 1)
        self.assertEqual(run_drift_audit(self.config, deep=True, as_json=False), EXIT_CLEAN)

    def test_doctor_verify_drift_runs_the_audit(self) -> None:
        from bloorecall.cli import main

        self.refresh()
        config_file = self.index_dir / "config.json"
        config_file.write_text(json.dumps(self.config), encoding="utf-8")
        (self.corpus / "notes" / "grocery.txt").unlink()

        def doctor(*flags: str) -> int:
            with mock.patch.object(OllamaEmbedder, "embed_one", FakeEmbedder().embed_one):
                with redirect_stdout(io.StringIO()):
                    return main(["--config", str(config_file), "doctor", *flags])

        self.assertEqual(doctor(), 0)
        self.assertEqual(doctor("--verify-drift"), 1)

    def test_missing_index_exits_error(self) -> None:
        # Point at a non-existent index
        bad_config = dict(self.config)
        bad_config["index_path"] = "var/nonexistent.sqlite3"
        bad_config["_config_path"] = "test-bad"
        code = run_drift_audit(bad_config, deep=True, as_json=False)
        self.assertEqual(code, EXIT_ERROR)


if __name__ == "__main__":
    unittest.main(verbosity=2)
