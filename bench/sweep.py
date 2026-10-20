"""CLI: python -m bench.sweep [--fresh] [--weights 0.4,0.5,0.55,0.7,0.85,1.0]

Grid-search fusion mode x dense_weight on the DEV split, so a policy change is
chosen on dev and confirmed once on test (bench.run --split test), never tuned
on test. Each query is embedded once and re-ranked per grid cell, so the sweep
costs one embedding pass however large the grid is.

It also records how far apart the dense and BM25 scores sit among each query's
top dense candidates: the scale gap that made the v0 "raw" blend let BM25 win
whatever dense_weight said, and the reason hybrid-rrf-v1 fuses ranks instead.

Every other policy field comes from baseline-v0, so a cell differs from the
shipped hybrid only in the two swept knobs. Writes bench/results/sweep/dev.json
(a subdirectory, so bench.report's per-system loader never mistakes it for a
system result).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import median
from typing import Any, Dict, List

import numpy as np

from bloorecall.config import FUSION_MODES, active_policy
from bloorecall.util import PROJECT_ROOT, tokens

from bench import metrics
from bench.run import load_bench_config
from bench.runner import RESULTS_DIR, corpus_files_from_source, git_commit, validate_queries
from bench.splits import read_queries
from bench.systems import BlooRecallSystem, prepare_corpus_mirror, resolve_config

SPLIT = "dev"
DEFAULT_WEIGHTS = (0.4, 0.5, 0.55, 0.7, 0.85, 1.0)
BASE_POLICY = "baseline-v0"
REPORTED = ("recall@1", "recall@5", "mrr@10", "ndcg@10")
SPREAD_CANDIDATES = 20


def score_spread(index: Any, question: str, vector: List[float]) -> Dict[str, float]:
    """Max-min of v0's dense and BM25 scores over the query's top dense candidates."""
    lexical, _ = index._bm25(tokens(question))
    dense = (index.matrix @ np.asarray(vector, dtype=np.float32) + 1.0) / 2.0
    bm25 = lexical / (float(lexical.max()) or 1.0)
    head = np.argsort(-dense, kind="stable")[:SPREAD_CANDIDATES]
    return {"dense": float(np.ptp(dense[head])), "bm25": float(np.ptp(bm25[head]))}


def sweep(
    config: Dict[str, Any],
    queries: List[Dict[str, Any]],
    weights: List[float],
    *,
    fresh: bool,
    corpus_root: Path,
    embedder: Any = None,
    top_k: int = 10,
) -> Dict[str, Any]:
    system = BlooRecallSystem(
        resolve_config(config, corpus_root), "sweep", policy_name=BASE_POLICY, embed_query=True,
        corpus_root=corpus_root,
    )
    system.setup(fresh=fresh, embedder=embedder)
    assert system.index is not None and system.embedder is not None
    vectors = [system.embedder.embed_one(query["query"]) for query in queries]
    base = active_policy(config, BASE_POLICY)
    spreads = [score_spread(system.index, q["query"], v) for q, v in zip(queries, vectors)]

    cells: List[Dict[str, Any]] = []
    for fusion in FUSION_MODES:
        for weight in weights:
            policy = {**base, "fusion": fusion, "dense_weight": weight, "top_k": top_k}
            rows = []
            for query, vector in zip(queries, vectors):
                ranked = system.search_with_vector(query["query"], vector, policy)
                rows.append({"metrics": metrics.per_query_metrics(ranked, query["graded"])})
            overall = metrics.evaluate_group(rows)
            cells.append(
                {"fusion": fusion, "dense_weight": weight, **{name: overall[name] for name in REPORTED}}
            )
    system.close()
    return {
        "split": SPLIT,
        "n_queries": len(queries),
        "base_policy": BASE_POLICY,
        "git_commit": git_commit(),
        "embedding_model": config["embedding"]["model"],
        "score_spread_median": {
            "candidates": SPREAD_CANDIDATES,
            "dense": round(median(spread["dense"] for spread in spreads), 4),
            "bm25": round(median(spread["bm25"] for spread in spreads), 4),
        },
        "cells": cells,
    }


def format_table(result: Dict[str, Any], *, advice: bool = True) -> str:
    spread = result["score_spread_median"]
    lines = [
        f"{result['split']} split, {result['n_queries']} queries, other fields from {result['base_policy']}",
        f"median score spread over each query's top {spread['candidates']} dense candidates: "
        f"dense (cos+1)/2 {spread['dense']:.3f}, bm25/max {spread['bm25']:.3f}",
        "",
        "| fusion | dense_weight | " + " | ".join(REPORTED) + " |",
        "|---|---|" + "---|" * len(REPORTED),
    ]
    best = max(result["cells"], key=lambda cell: (cell["mrr@10"], cell["recall@5"]))
    for cell in result["cells"]:
        marker = " ←" if cell is best else ""
        values = " | ".join(f"{cell[name]:.3f}" for name in REPORTED)
        lines.append(f"| {cell['fusion']} | {cell['dense_weight']:.2f} | {values} |{marker}")
    lines += ["", "← best MRR@10 (ties broken by Recall@5)." + (" Confirm it once on test before shipping it." if advice else "")]
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bench.sweep", description=__doc__.split("\n\n")[1])
    parser.add_argument("--config", default="bench/config.bench.json")
    parser.add_argument("--queries", default="bench/queries.jsonl")
    parser.add_argument("--weights", default=",".join(str(w) for w in DEFAULT_WEIGHTS))
    parser.add_argument("--fresh", action="store_true", help="rebuild the index from scratch first")
    args = parser.parse_args(argv)

    config = load_bench_config(PROJECT_ROOT / args.config)
    weights = [float(part) for part in args.weights.split(",") if part.strip()]
    queries = [q for q in read_queries(PROJECT_ROOT / args.queries) if q.get("split") == SPLIT]
    problems = validate_queries(queries, corpus_files_from_source())
    if problems:
        raise SystemExit("\n".join(f"QUERY PROBLEM: {problem}" for problem in problems))

    result = sweep(config, queries, weights, fresh=args.fresh, corpus_root=prepare_corpus_mirror())
    target = RESULTS_DIR / "sweep" / f"{SPLIT}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(format_table(result))
    print(f"\nwrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
