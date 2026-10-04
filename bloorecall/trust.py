"""Trust verdicts for search hits, inspired by Heimdall's per-result disk verification.

Before any top hit is returned to the caller, :func:`verify_path` stats the file on
disk and re-computes its SHA-256, comparing against the hash stored at index
time.  The resulting :class:`TrustVerdict` is attached to every result so the
agent always knows how much to believe it.

Verdicts (Heimdall's four, adapted to BlooRecall's prose index):

  STRONG  — file exists, on-disk content hash matches the index, embedding
           text-cache is fresh, and the source was *not* touched in the most
           recent refresh pass.
  REBUILT — file matches disk, but was re-indexed (added or touched) in the
           current refresh pass — freshly verified, freshly anchored.
  WEAK    — file exists on disk but the content hash drifted or the embedding
           cache is stale for one of the hit's chunks.
  STALE   — file is gone from disk (missing, or deleted-then-not-yet-removed).
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
    embedding_fresh: bool
    just_rebuilt: bool


def verify_path(
    path: str,
    indexed_hash: str,
    indexed_at: float,
    refreshed_at: float,
    cached_text_hashes: set[str],
    path_text_hashes: list[str],
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
    cached_text_hashes
        Set of text_hash values that have a vector in the ``vectors`` cache
        for the active embedding model.
    path_text_hashes
        text_hash values of the chunks backing this particular hit (usually
        just the single best chunk).
    """
    file_path = Path(path)
    if not file_path.exists():
        return TrustCheck(
            verdict=TrustVerdict.STALE,
            reason="file missing from disk",
            indexed_hash=indexed_hash,
            on_disk_hash=None,
            file_exists=False,
            embedding_fresh=False,
            just_rebuilt=False,
        )

    on_disk_hash = sha256_file(file_path)
    hash_match = on_disk_hash == indexed_hash
    embedding_fresh = bool(path_text_hashes) and all(
        text_hash in cached_text_hashes for text_hash in path_text_hashes
    )
    just_rebuilt = abs(indexed_at - refreshed_at) < rebuild_window_seconds

    if not hash_match or not embedding_fresh:
        reasons: list[str] = []
        if not hash_match:
            reasons.append("content hash mismatch")
        if not embedding_fresh:
            reasons.append("stale embedding cache")
        return TrustCheck(
            verdict=TrustVerdict.WEAK,
            reason="; ".join(reasons),
            indexed_hash=indexed_hash,
            on_disk_hash=on_disk_hash,
            file_exists=True,
            embedding_fresh=embedding_fresh,
            just_rebuilt=just_rebuilt,
        )

    if just_rebuilt:
        return TrustCheck(
            verdict=TrustVerdict.REBUILT,
            reason="re-indexed in current refresh pass",
            indexed_hash=indexed_hash,
            on_disk_hash=on_disk_hash,
            file_exists=True,
            embedding_fresh=True,
            just_rebuilt=True,
        )

    return TrustCheck(
        verdict=TrustVerdict.STRONG,
        reason="disk hash matches; embedding cache fresh",
        indexed_hash=indexed_hash,
        on_disk_hash=on_disk_hash,
        file_exists=True,
        embedding_fresh=True,
        just_rebuilt=False,
    )
