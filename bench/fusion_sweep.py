"""Dev-split fusion sweep: the evidence behind the hybrid-rrf-v1 default.

    python3 -m bench.fusion_sweep        (after `python3 -m bench.run` has built the index)

Prints (1) how far apart the dense and BM25 scores sit among each query's top
dense candidates, which is why the v1.0 linear blend let BM25 win whatever
dense_weight said, and (2) dev metrics for linear and RRF fusion at a few
settings, all through the shipped BlooRecallIndex.rank(). It reads only the
dev split, by design: the test split is for confirming a choice, not making it.
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from bloorecall.config import active_policy, index_path
from bloorecall.embeddings import OllamaEmbedder
from bloorecall.search import BlooRecallIndex
from bloorecall.util import PROJECT_ROOT, tokens

from bench import metrics
from bench.run import load_bench_config
from bench.splits import read_queries
from bench.systems import CORPUS_PREFIX, prepare_corpus_mirror, resolve_config

CANDIDATES = 20
VARIANTS = [
    ("linear", 0.55, None),
    ("linear", 0.7, None),
    ("linear", 0.9, None),
    ("linear", 1.0, None),
    ("rrf", 0.3, 60),
    ("rrf", 0.5, 60),
    ("rrf", 0.7, 60),
    ("rrf", 0.5, 10),
    ("rrf", 0.5, 200),
]


def score_spreads(index: BlooRecallIndex, question: str, vector: np.ndarray) -> tuple[float, float]:
    """Max-min of each normalized score over the query's top dense candidates."""
    lexical, _ = index._bm25(tokens(question))
    dense = (index.matrix @ vector + 1.0) / 2.0
    bm25 = lexical / (float(lexical.max()) or 1.0)
    head = np.argsort(-dense, kind="stable")[:CANDIDATES]
    return float(np.ptp(dense[head])), float(np.ptp(bm25[head]))


def main() -> int:
    config = load_bench_config(PROJECT_ROOT / "bench" / "config.bench.json")
    mirror = prepare_corpus_mirror()
    resolved = resolve_config(config, mirror)
    path = index_path(resolved)
    if not path.exists():
        sys.exit(f"no bench index at {path}; run `python3 -m bench.run --split dev` first")
    index = BlooRecallIndex(path)
    queries = [q for q in read_queries(PROJECT_ROOT / "bench" / "queries.jsonl") if q["split"] == "dev"]
    embedder = OllamaEmbedder.from_config(resolved)
    vectors = [np.asarray(embedder.embed_one(q["query"]), dtype=np.float32) for q in queries]

    spreads = [score_spreads(index, q["query"], v) for q, v in zip(queries, vectors)]
    print(f"Score spread over each query's top {CANDIDATES} dense candidates (dev, median):")
    print(f"  dense (cos+1)/2   {statistics.median(s[0] for s in spreads):.3f}")
    print(f"  bm25 / max        {statistics.median(s[1] for s in spreads):.3f}\n")

    base = active_policy(resolved, "hybrid-rrf-v1")
    print(f"{'fusion':8s} {'dense_w':>7s} {'k':>4s}  R@1    R@5    MRR@10 nDCG@10")
    for fusion, weight, k in VARIANTS:
        policy: Dict[str, Any] = {**base, "fusion": fusion, "dense_weight": weight, "top_k": 10}
        if k is not None:
            policy["rrf_k"] = k
        rows: List[Dict[str, Any]] = []
        for query, vector in zip(queries, vectors):
            ranked = [
                f"{CORPUS_PREFIX}/{Path(row['path']).relative_to(mirror).as_posix()}"
                for row in index.rank(query["query"], vector.tolist(), policy)
            ]
            rows.append({"metrics": metrics.per_query_metrics(ranked, query["graded"])})
        overall = metrics.aggregate([row["metrics"] for row in rows])
        print(
            f"{fusion:8s} {weight:7.2f} {k if k is not None else '-':>4}  "
            f"{overall['recall@1']:.3f}  {overall['recall@5']:.3f}  {overall['mrr@10']:.3f}  {overall['ndcg@10']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
