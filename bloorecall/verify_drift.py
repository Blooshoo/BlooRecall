"""Read-only drift audit: compares the BlooRecall index against disk.

Heimdall's ``verify --deep`` compares the journal against the filesystem and exits
non-zero on drift (CI-safe).  This module ports that idea to BlooRecall v1's
SQLite + manifest model.

Checks performed
----------------
* **Ghost / missing** — a source row whose file is gone from disk.
* **Hash drift** — a source row whose on-disk SHA-256 no longer matches the
  indexed ``content_hash`` (catches size+mtime-preserving rewrites, which
  BlooRecall's mtime+size skip would otherwise miss — this is the ``--deep``
  guarantee).
* **Orphan** — a source whose canonical path is not under any *walked* corpus
  root (analogous to Heimdall's exact-ownership invariant).
* **Unindexed** — a walkable file that is on disk but absent from the index.
* **Ownership** — a source whose on-disk file is not owned by the local user.

Exit codes
----------
* ``0`` — clean (index matches disk)
* ``1`` — drift detected (ghost, hash drift, orphan, or unindexed)
* ``2`` — error (could not open index, missing config, etc.)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from . import store
from .config import index_path
from .corpus import Exclusions, walk_corpus
from .util import sha256_file

EXIT_CLEAN = 0
EXIT_DRIFT = 1
EXIT_ERROR = 2


@dataclass
class DriftReport:
    """Aggregate results of a drift audit."""

    checked: int = 0
    clean: int = 0
    ghosts: list[dict[str, Any]] = field(default_factory=list)
    hash_drift: list[dict[str, Any]] = field(default_factory=list)
    orphans: list[dict[str, Any]] = field(default_factory=list)
    unindexed: list[dict[str, Any]] = field(default_factory=list)
    ownership_issues: list[dict[str, Any]] = field(default_factory=list)
    missing_roots: list[str] = field(default_factory=list)
    index_age_seconds: float | None = None
    index_refreshed_at_iso: str | None = None
    manifest_sha256: str | None = None

    @property
    def has_drift(self) -> bool:
        return bool(
            self.ghosts or self.hash_drift or self.orphans
            or self.unindexed or self.ownership_issues
        )

    @property
    def exit_code(self) -> int:
        return EXIT_DRIFT if self.has_drift else EXIT_CLEAN

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _current_uid() -> int:
    return os.getuid() if hasattr(os, "getuid") else 0


def _file_owner(path: Path) -> int | None:
    try:
        return os.stat(path).st_uid
    except OSError:
        return None


def _covered_root_set(roots: list[str]) -> set[Path]:
    """Set of resolved root paths for orphan checking."""
    return {Path(root).resolve() for root in roots if Path(root).resolve().exists()}


def _is_under_root(path: str, resolved_roots: set[Path]) -> bool:
    resolved = Path(path).resolve()
    return any(resolved == root or root in resolved.parents for root in resolved_roots)


def _load_indexed_sources(connection) -> dict[str, tuple[str, int, float]]:
    """Return {canonical_path: (content_hash, byte_count, indexed_at)} from the index."""
    rows = connection.execute(
        "SELECT canonical_path, content_hash, byte_count, indexed_at FROM sources"
    ).fetchall()
    return {row[0]: (row[1], row[2], row[3]) for row in rows}


def run_drift_audit(
    config: dict[str, Any],
    *,
    deep: bool = True,
    as_json: bool = False,
) -> int:
    """Run a read-only drift audit against the on-disk index.

    Parameters
    ----------
    config
        Loaded BlooRecall config dict.
    deep
        If ``True`` (default), always re-hash every source — the ``--deep``
        guarantee that catches size+mtime-preserving rewrites.  If ``False``,
        only stat-check (cheaper, catches missing/ownership but not silent
        content rewrites).
    as_json
        Emit a JSON summary on stdout.
    """
    target = index_path(config)
    if not target.exists():
        if as_json:
            print(json.dumps({"error": f"index not found at {target}", "exit_code": EXIT_ERROR}))
        else:
            print(f"error: index not found at {target}", file=sys.stderr)
            print("run 'bloorecall refresh' first", file=sys.stderr)
        return EXIT_ERROR

    try:
        connection = store.connect_read(target)
    except Exception as error:  # noqa: BLE001
        if as_json:
            print(json.dumps({"error": str(error), "exit_code": EXIT_ERROR}))
        else:
            print(f"error: cannot open index: {error}", file=sys.stderr)
        return EXIT_ERROR

    local_uid = _current_uid()
    report = DriftReport()

    try:
        metadata = store.read_metadata(connection)
        indexed_at = float(metadata.get("refreshed_at", 0) or 0)
        report.index_refreshed_at_iso = (
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(indexed_at)) if indexed_at else None
        )
        report.index_age_seconds = round(time.time() - indexed_at, 1) if indexed_at else None
        report.manifest_sha256 = metadata.get("manifest_sha256")
        sources = _load_indexed_sources(connection)
    finally:
        connection.close()

    report.missing_roots = [
        entry["path"]
        for entry in config["corpus_roots"]
        if not Path(entry["path"]).expanduser().exists()
    ]
    covered_roots = _covered_root_set([entry["path"] for entry in config["corpus_roots"]])
    report.checked = len(sources)

    # Phase 1: verify each indexed source against disk
    for canonical, (content_hash, byte_count, indexed_at_src) in sorted(sources.items()):
        file_path = Path(canonical)
        try:
            exists = file_path.exists()
        except OSError:
            exists = False

        if not exists:
            report.ghosts.append({
                "canonical_path": canonical,
                "content_hash": content_hash,
                "indexed_at": indexed_at_src,
                "reason": "file missing from disk",
            })
            continue

        # Ownership check
        on_disk_owner = _file_owner(file_path)
        if on_disk_owner is not None and on_disk_owner != local_uid:
            report.ownership_issues.append({
                "canonical_path": canonical,
                "indexed_owner": "local_owner_only",
                "on_disk_uid": on_disk_owner,
                "local_uid": local_uid,
                "reason": "file not owned by local user",
            })

        # Orphan check: not under any walked root
        if not _is_under_root(canonical, covered_roots):
            report.orphans.append({
                "canonical_path": canonical,
                "reason": "indexed source not under a walked corpus root",
            })

        # Hash drift check (the --deep guarantee)
        if deep:
            try:
                on_disk_hash = sha256_file(file_path)
            except OSError:
                report.ghosts.append({
                    "canonical_path": canonical,
                    "content_hash": content_hash,
                    "reason": "file unreadable on disk",
                })
                continue
            if on_disk_hash != content_hash:
                report.hash_drift.append({
                    "canonical_path": canonical,
                    "indexed_hash": content_hash,
                    "on_disk_hash": on_disk_hash,
                    "reason": "SHA-256 mismatch (content changed without re-index)",
                })
            else:
                report.clean += 1
        else:
            report.clean += 1

    # Phase 2: walk corpus roots and find files that should be indexed but aren't
    walk_result = walk_corpus(config)
    indexed_canonical = set(sources.keys())
    for source_file in walk_result.sources:
        canonical = str(source_file.path)
        if canonical not in indexed_canonical:
            try:
                content_hash = sha256_file(source_file.path)
            except OSError:
                content_hash = "unreadable"
            report.unindexed.append({
                "canonical_path": canonical,
                "content_hash": content_hash,
                "reason": "file under walked root but missing from index",
            })

    if as_json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        _print_human(report, deep)

    return report.exit_code


def _print_human(report: DriftReport, deep: bool) -> None:
    mode = "deep" if deep else "shallow"
    print(f"BlooRecall drift audit ({mode})")
    print(f"  checked   {report.checked} indexed sources")
    print(f"  healthy   {report.clean} sources match disk")
    if report.ghosts:
        print(f"  ghosts    {len(report.ghosts)} indexed sources missing from disk")
        for item in report.ghosts[:10]:
            print(f"    X {item['canonical_path']}")
        if len(report.ghosts) > 10:
            print(f"    ...{len(report.ghosts) - 10} more")
    if report.hash_drift:
        print(f"  drift     {len(report.hash_drift)} content-hash mismatches")
        for item in report.hash_drift[:10]:
            print(f"    X {item['canonical_path']}")
        if len(report.hash_drift) > 10:
            print(f"    ...{len(report.hash_drift) - 10} more")
    if report.orphans:
        print(f"  orphans   {len(report.orphans)} sources not under a walked root")
        for item in report.orphans[:10]:
            print(f"    ? {item['canonical_path']}")
    if report.unindexed:
        print(f"  unindexed {len(report.unindexed)} walkable files missing from index")
        for item in report.unindexed[:10]:
            print(f"    + {item['canonical_path']}")
        if len(report.unindexed) > 10:
            print(f"    ...{len(report.unindexed) - 10} more")
    if report.ownership_issues:
        print(f"  ownership {len(report.ownership_issues)} files not owned by local user")
        for item in report.ownership_issues[:10]:
            print(f"    ! {item['canonical_path']} (uid {item['on_disk_uid']})")
    if report.missing_roots:
        print(f"  missing   {len(report.missing_roots)} configured roots do not exist")
        for root in report.missing_roots:
            print(f"    ! {root}")
    if report.index_age_seconds is not None:
        print(f"  age       index {report.index_age_seconds}s old")
    if report.manifest_sha256:
        print(f"  manifest  {report.manifest_sha256[:16]}...")

    if report.has_drift:
        print(f"\n  RESULT: DRIFT detected (exit 1)")
    else:
        print(f"\n  RESULT: clean (exit 0)")

