"""Deterministic dev/test split assignment for bench/queries.jsonl.

split = "dev" when int(sha256(id)) % 10 < 3 (about 30%), else "test".
Assignment depends only on the query id, so it is stable across runs,
re-ordering, and edits to other fields.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


def split_for(query_id: str) -> str:
    digest = hashlib.sha256(query_id.encode("utf-8")).hexdigest()
    return "dev" if int(digest, 16) % 10 < 3 else "test"


def assign_splits(queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for query in queries:
        query["split"] = split_for(query["id"])
    return queries


def assign_splits_in_file(path: Path) -> Dict[str, int]:
    queries = read_queries(path)
    assign_splits(queries)
    write_queries(path, queries)
    counts: Dict[str, int] = {}
    for query in queries:
        counts[query["split"]] = counts.get(query["split"], 0) + 1
    return counts


def read_queries(path: Path) -> List[Dict[str, Any]]:
    queries: List[Dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        queries.append(json.loads(line))
    return queries


def write_queries(path: Path, queries: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for query in queries:
            handle.write(json.dumps(query, ensure_ascii=False, sort_keys=True) + "\n")
