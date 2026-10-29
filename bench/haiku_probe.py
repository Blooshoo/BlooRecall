"""CLI: python -m bench.haiku_probe [--config bench/config.bench.json]

A stress probe for rank fusion: 40 haiku and, for each, a query that describes it without
sharing a content word (bench/haiku/README.md). BM25 has nothing true to match, so the gap
between `dense` and `hybrid-rrf` is what keyword noise costs the fused ranking. Not part of the
benchmark: no splits, no labels beyond the one poem each query describes.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

from bloorecall.util import PROJECT_ROOT

from bench import metrics
from bench.run import load_bench_config
from bench.splits import read_queries
from bench.systems import BlooRecallSystem

PROBE_DIR = PROJECT_ROOT / "bench" / "haiku"
MIRROR_NAME = "bloorecall-bench-haiku"
# (system id, bench policy, embeds the query)
SYSTEMS = (("bm25", "bench-bm25", False), ("dense", "bench-dense", True), ("hybrid-rrf", "hybrid-rrf-v1", True))
REPORTED = ("recall@1", "recall@5", "mrr@10")


def probe(config: Dict[str, Any], *, embedder: Any = None) -> Dict[str, Dict[str, float]]:
    """Index the poems once and score each system; returns {system: {metric: value}}."""
    # Mirrored like bench/corpus (BlooRecall will not index its own project directory), with one
    # shared mtime: the poems were written seconds apart, and recency would reward that order.
    mirror = Path(tempfile.gettempdir()) / MIRROR_NAME
    if mirror.exists():
        shutil.rmtree(mirror)
    shutil.copytree(PROBE_DIR / "corpus", mirror)
    for poem in mirror.iterdir():
        os.utime(poem, (1_760_000_000, 1_760_000_000))
    config = {
        **config,
        "corpus_roots": [{"path": str(mirror), "label": "haiku", "max_files": 100}],
        "index_path": "var/bench-haiku/index.sqlite3",
    }
    queries = read_queries(PROBE_DIR / "queries.jsonl")
    scores: Dict[str, Dict[str, float]] = {}
    for position, (system_id, policy, embed_query) in enumerate(SYSTEMS):
        system = BlooRecallSystem(
            config, system_id, policy_name=policy, embed_query=embed_query, corpus_root=mirror
        )
        system.setup(fresh=position == 0, embedder=embedder)
        rows = []
        for query in queries:
            ranked = [path.rsplit("/", 1)[-1] for path in system.search(query["query"], top_k=10)]
            rows.append(metrics.per_query_metrics(ranked, {query["answer"]: 2}))
        system.close()
        scores[system_id] = metrics.aggregate(rows)
    return scores


def format_table(scores: Dict[str, Dict[str, float]]) -> str:
    lines = ["| system | " + " | ".join(REPORTED) + " |", "|---|" + "---|" * len(REPORTED)]
    for system_id, row in scores.items():
        lines.append(f"| {system_id} | " + " | ".join(f"{row[name]:.3f}" for name in REPORTED) + " |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.haiku_probe", description="Rank-fusion stress probe: haiku vs queries sharing no word"
    )
    parser.add_argument("--config", default="bench/config.bench.json")
    args = parser.parse_args(argv)
    config = load_bench_config(PROJECT_ROOT / args.config)
    print(f"haiku probe, {config['embedding']['model']}, 40 queries")
    print(format_table(probe(config)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
