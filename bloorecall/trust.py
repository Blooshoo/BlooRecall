"""Trust verdicts for search hits, inspired by Heimdall's per-result disk verification.

Before any top hit is returned to the caller, :func:`verify_path` stats the file on
disk and re-computes its SHA-256, comparing against the hash stored at index
time.  The resulting :class:`TrustVerdict` is attached to every result so the
agent always knows how much to believe it.

Verdicts (Heimdall's four, adapted to BlooRecall's prose index):

  STRONG  — file exists and its on-disk content hash matches the index.
  REBUILT — file matches disk and was (re-)indexed in the most recent refresh
           pass — freshly verified, freshly anchored.
  WEAK    — file exists on disk but its content hash drifted since indexing.
  STALE   — file is gone from disk (missing, or deleted-then-not-yet-removed).

A verdict is about the file, not the embedding cache: every indexed chunk keeps its
own vector, and the cache only spares re-embedding text seen before, so an expired
cache entry says nothing about whether a hit is current. (v1.1 read it as drift,
which flagged every file left unedited for `vector_cache_days`.)
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from pathlib import Path

from .util import sha256_file

# Tolerance (seconds) between a source's indexed_at and the index metadata's
# refreshed_at to consider it "just re-indexed this pass."
REBUILD_WINDOW_SECONDS = 1.0


class TrustVerdict(str, enum.Enum):
    """Per-result disk-verification verdict."""

    STRONG = "strong"
    WEAK = "weak"
    REBUILT = "rebuilt"
    STALE = "stale"


@dataclass
class TrustCheck:
    """Result of verifying a single search hit against the filesystem."""

    verdict: TrustVerdict
    reason: str
    indexed_hash: str
    on_disk_hash: str | None
    file_exists: bool
    just_rebuilt: bool


def verify_path(
    path: str,
    indexed_hash: str,
    indexed_at: float,
    refreshed_at: float,
    *,
    rebuild_window_seconds: float = REBUILD_WINDOW_SECONDS,
) -> TrustCheck:
    """Verify a single search hit against disk before the agent sees it.

    Parameters
    ----------
    path
        Absolute canonical path of the file behind the hit.
    indexed_hash
        SHA-256 of the file bytes as recorded at index time.
    indexed_at
        Timestamp the source was last written (indexed or touched).
    refreshed_at
        Timestamp of the most recent refresh pass (index metadata).
    """
    file_path = Path(path)
    if not file_path.exists():
        return TrustCheck(
            verdict=TrustVerdict.STALE,
            reason="file missing from disk",
            indexed_hash=indexed_hash,
            on_disk_hash=None,
            file_exists=False,
            just_rebuilt=False,
        )

    on_disk_hash = sha256_file(file_path)
    just_rebuilt = abs(indexed_at - refreshed_at) < rebuild_window_seconds

    if on_disk_hash != indexed_hash:
        return TrustCheck(
            verdict=TrustVerdict.WEAK,
            reason="content hash mismatch",
            indexed_hash=indexed_hash,
            on_disk_hash=on_disk_hash,
            file_exists=True,
            just_rebuilt=just_rebuilt,
        )

    if just_rebuilt:
        return TrustCheck(
            verdict=TrustVerdict.REBUILT,
            reason="re-indexed in current refresh pass",
            indexed_hash=indexed_hash,
            on_disk_hash=on_disk_hash,
            file_exists=True,
            just_rebuilt=True,
        )

    return TrustCheck(
        verdict=TrustVerdict.STRONG,
        reason="disk hash matches",
        indexed_hash=indexed_hash,
        on_disk_hash=on_disk_hash,
        file_exists=True,
        just_rebuilt=False,
    )
