"""Ranking metrics with bootstrap confidence intervals.

Definitions used across the benchmark (documented in bench/REPORT.md):

- A document is *relevant* to a query when its graded label is >= 1.
- recall@k: 1 if any relevant document appears in the top k, else 0.
  (Every query has a small relevant set, so this is the standard
  success@k formulation of recall for this task.)
- mrr@k: 1 / rank of the first relevant document within the top k, else 0.
- ndcg@k: binary-relevance DCG with graded gains 2**rel - 1 over the top k,
  normalized by the ideal DCG of the query's own graded labels.

The bootstrap resamples queries with replacement (fixed seed), so results are
deterministic for a fixed set of queries.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Sequence

METRIC_NAMES = ("recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@10")
BOOTSTRAP_SEED = 20261003
BOOTSTRAP_SAMPLES = 1000


def is_relevant(graded: Dict[str, int], path: str) -> bool:
    return int(graded.get(path, 0)) >= 1


def recall_at_k(ranked: Sequence[str], graded: Dict[str, int], k: int) -> float:
    top = ranked[:k]
    return 1.0 if any(is_relevant(graded, path) for path in top) else 0.0


def mrr_at_k(ranked: Sequence[str], graded: Dict[str, int], k: int = 10) -> float:
    for position, path in enumerate(ranked[:k], start=1):
        if is_relevant(graded, path):
            return 1.0 / position
    return 0.0


def _dcg(gains: Sequence[int]) -> float:
    return sum((2**gain - 1) / math.log2(position + 2) for position, gain in enumerate(gains))


def ndcg_at_k(ranked: Sequence[str], graded: Dict[str, int], k: int = 10) -> float:
    gains = [int(graded.get(path, 0)) for path in ranked[:k]]
    ideal = sorted((int(grade) for grade in graded.values()), reverse=True)[:k]
    ideal_dcg = _dcg(ideal)
    if ideal_dcg <= 0:
        return 0.0
    return _dcg(gains) / ideal_dcg


def per_query_metrics(ranked: Sequence[str], graded: Dict[str, int]) -> Dict[str, float]:
    return {
        "recall@1": recall_at_k(ranked, graded, 1),
        "recall@5": recall_at_k(ranked, graded, 5),
        "recall@10": recall_at_k(ranked, graded, 10),
        "mrr@10": mrr_at_k(ranked, graded, 10),
        "ndcg@10": ndcg_at_k(ranked, graded, 10),
    }


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate(rows: List[Dict[str, float]]) -> Dict[str, float]:
    return {name: mean([row[name] for row in rows]) for name in METRIC_NAMES}


def bootstrap_ci(
    rows: List[Dict[str, float]],
    samples: int = BOOTSTRAP_SAMPLES,
    seed: int = BOOTSTRAP_SEED,
    confidence: float = 0.95,
) -> Dict[str, List[float]]:
    """Percentile bootstrap CI per metric, resampling queries with replacement."""
    if not rows:
        return {name: [0.0, 0.0] for name in METRIC_NAMES}
    rng = random.Random(seed)
    n = len(rows)
    resampled: Dict[str, List[float]] = {name: [] for name in METRIC_NAMES}
    for _ in range(samples):
        indices = [rng.randrange(n) for _ in range(n)]
        for name in METRIC_NAMES:
            resampled[name].append(mean([rows[i][name] for i in indices]))
    alpha = (1.0 - confidence) / 2.0
    result: Dict[str, List[float]] = {}
    for name in METRIC_NAMES:
        ordered = sorted(resampled[name])
        low = ordered[max(0, int(math.ceil((alpha) * len(ordered))) - 1)]
        high = ordered[min(len(ordered) - 1, int(math.floor((1 - alpha) * len(ordered))))]
        result[name] = [round(low, 4), round(high, 4)]
    return result


def evaluate_group(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """rows: [{'metrics': per-query dict, ...}] -> point estimates plus CI95."""
    metric_rows = [row["metrics"] for row in rows]
    point = aggregate(metric_rows)
    ci = bootstrap_ci(metric_rows)
    return {
        "n_queries": len(rows),
        **{name: round(value, 4) for name, value in point.items()},
        "ci95": ci,
    }


def latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "mean": 0.0}
    ordered = sorted(latencies_ms)

    def percentile(fraction: float) -> float:
        position = min(len(ordered) - 1, int(math.ceil(fraction * len(ordered))) - 1)
        return ordered[max(0, position)]

    return {
        "p50": round(percentile(0.50), 2),
        "p95": round(percentile(0.95), 2),
        "mean": round(sum(ordered) / len(ordered), 2),
    }
