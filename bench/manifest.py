"""Corpus manifest tooling for the benchmark.

- merge: combine bench/corpus/<project>/manifest.json files written by the
  corpus subagents into one bench/corpus/MANIFEST.json (sorted, validated).
- validate: schema + existence checks, superseded-mtime ordering.
- apply: set each file's mtime from the manifest (os.utime) so recency/superseded
  behavior is reproducible. This is the harness step the study prompt requires.

The manifest is the only source of truth for file times; nothing reads a file's
"natural" mtime.
"""
from __future__ import annotations

import calendar
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from bloorecall.util import PROJECT_ROOT

CORPUS_DIR = PROJECT_ROOT / "bench" / "corpus"
MANIFEST_PATH = CORPUS_DIR / "MANIFEST.json"
ALLOWED_EXTENSIONS = {".md", ".txt", ".rst"}
ALLOWED_TAGS = {
    "vocabulary-gap",
    "exact-identifier",
    "heading-context",
    "near-duplicate",
    "long-deep-answer",
    "superseded",
    "vague-recall",
    "distractor",
}


def parse_iso(timestamp: str) -> float:
    moment = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return calendar.timegm(moment.utctimetuple()) + moment.microsecond / 1e6


def load_project_manifests() -> Dict[str, List[Dict[str, Any]]]:
    projects: Dict[str, List[Dict[str, Any]]] = {}
    for path in sorted(CORPUS_DIR.glob("*/manifest.json")):
        projects[path.parent.name] = json.loads(path.read_text(encoding="utf-8"))
    return projects


def merge() -> Dict[str, Any]:
    projects = load_project_manifests()
    merged: Dict[str, Dict[str, Any]] = {}
    for project, entries in projects.items():
        for entry in entries:
            path = entry["path"]
            if path in merged:
                raise SystemExit(f"duplicate manifest path: {path}")
            if not path.startswith(f"bench/corpus/{project}/"):
                raise SystemExit(f"entry {path} lives outside its project dir bench/corpus/{project}/")
            merged[path] = entry
    ordered = [merged[path] for path in sorted(merged)]
    MANIFEST_PATH.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"projects": len(projects), "entries": len(ordered), "path": str(MANIFEST_PATH)}


def load_merged() -> List[Dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        raise SystemExit("bench/corpus/MANIFEST.json missing; run: python -m bench.manifest merge")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def validate() -> List[str]:
    entries = load_merged()
    problems: List[str] = []
    seen_paths = set()
    by_path: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        path = entry.get("path", "")
        seen_paths.add(path)
        by_path[path] = entry
        absolute = PROJECT_ROOT / path
        if not absolute.is_file():
            problems.append(f"missing file: {path}")
            continue
        if absolute.suffix not in ALLOWED_EXTENSIONS:
            problems.append(f"unexpected extension: {path}")
        for field in ("project", "intended_mtime"):
            if not entry.get(field):
                problems.append(f"{path}: missing field '{field}'")
        try:
            parse_iso(entry["intended_mtime"])
        except Exception as error:  # noqa: BLE001
            problems.append(f"{path}: bad intended_mtime ({error})")
        bad_tags = set(entry.get("planted", [])) - ALLOWED_TAGS
        if bad_tags:
            problems.append(f"{path}: unknown planted tags {sorted(bad_tags)}")
    # Every corpus file must be manifested; manifest entries must exist.
    for path in sorted(CORPUS_DIR.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.json" and path.name != "manifest.json":
            relative = f"bench/corpus/{path.relative_to(CORPUS_DIR).as_posix()}"
            if relative not in seen_paths:
                problems.append(f"unmanifested corpus file: {relative}")
    # Superseded docs must be older than the doc that overrides them.
    for path, entry in by_path.items():
        overrides = entry.get("overridden_by")
        if not overrides:
            continue
        if overrides not in by_path:
            problems.append(f"{path}: overridden_by target missing from manifest: {overrides}")
            continue
        if parse_iso(entry["intended_mtime"]) >= parse_iso(by_path[overrides]["intended_mtime"]):
            problems.append(f"{path}: superseded doc is not older than {overrides}")
    return problems


def apply() -> Dict[str, Any]:
    problems = validate()
    if problems:
        for problem in problems:
            print(f"PROBLEM: {problem}", file=sys.stderr)
        raise SystemExit(f"{len(problems)} manifest problem(s); refusing to apply mtimes")
    entries = load_merged()
    changed = 0
    for entry in entries:
        timestamp = parse_iso(entry["intended_mtime"])
        os.utime(PROJECT_ROOT / entry["path"], (timestamp, timestamp))
        changed += 1
    return {"applied": changed, "elapsed_seconds": 0.0, "applied_at": time.time()}


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if action == "merge":
        print(json.dumps(merge(), indent=2))
    elif action == "validate":
        problems = validate()
        for problem in problems:
            print(f"PROBLEM: {problem}")
        print("ok" if not problems else f"{len(problems)} problem(s)")
        raise SystemExit(1 if problems else 0)
    elif action == "apply":
        print(json.dumps(apply(), indent=2))
    else:
        raise SystemExit(f"unknown action: {action} (use merge|validate|apply)")
