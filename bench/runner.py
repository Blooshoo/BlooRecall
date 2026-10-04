"""Run one or more systems over one split and write bench/results/<system>.<split>.json.

Determinism contract: for a fixed corpus (content + manifest mtimes), fixed
queries, fixed embedding model and fixed code, the output JSON is byte-stable
except for latency and index-build timings (hardware noise). Metrics and
bootstrap CIs are fully deterministic (seeded resampling).
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

from bloorecall.util import PROJECT_ROOT

from bench import metrics
from bench.splits import read_queries
from bench.systems import CORPUS_SOURCE, CORPUS_PREFIX, index_key_for, make_systems, prepare_corpus_mirror

RESULTS_DIR = PROJECT_ROOT / "bench" / "results"
WARMUP_QUERIES = 1


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def environment_info() -> Dict[str, str]:
    """Hardware/software context so latency and embeddings are interpretable."""
    import platform

    cpu = ""
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": cpu or platform.processor(),
        "python": platform.python_version(),
        "notes": "single process, warm Ollama keep_alive, one warmup query excluded from latency",
    }


def validate_queries(queries: List[Dict[str, Any]], corpus_files: set[str]) -> List[str]:
    problems: List[str] = []
    ids: set[str] = set()
    for query in queries:
        qid = query.get("id", "<missing>")
        if qid in ids:
            problems.append(f"{qid}: duplicate id")
        ids.add(qid)
        graded = query.get("graded") or {}
        relevant = query.get("relevant") or []
        if not graded and not relevant:
            problems.append(f"{qid}: no labels")
        if not query.get("category"):
            problems.append(f"{qid}: missing category")
        for path in graded:
            if path not in corpus_files:
                problems.append(f"{qid}: graded path not in corpus: {path}")
        for path in relevant:
            if int(graded.get(path, 0)) < 1:
                problems.append(f"{qid}: relevant path {path} missing from graded labels (or graded < 1)")
        for path, grade in graded.items():
            if grade not in (1, 2):
                problems.append(f"{qid}: grade must be 1 or 2, got {grade} for {path}")
    return problems


def corpus_files_from_source() -> set[str]:
    """Repo-relative paths of the versioned corpus ('bench/corpus/...')."""
    files: set[str] = set()
    for path in CORPUS_SOURCE.rglob("*"):
        if path.is_file() and path.suffix.casefold() in {".md", ".txt", ".rst"}:
            files.add(f"{CORPUS_PREFIX}/{path.relative_to(CORPUS_SOURCE).as_posix()}")
    return files


def run_system(
    system: Any,
    queries: List[Dict[str, Any]],
    *,
    split: str,
    top_k: int,
    fresh_index: bool,
    build_time_by_key: Dict[str, float],
    corpus_stats: Dict[str, int],
    model_name: str,
) -> Dict[str, Any]:
    build_key = index_key_for(system.system_id)
    # One fresh build per index key per invocation: the shared main index is
    # not rebuilt (or re-embedded) once any variant has built it this run.
    build_fresh = fresh_index and build_key not in build_time_by_key
    setup_summary = system.setup(fresh=build_fresh)
    build_seconds = float(setup_summary.get("elapsed_seconds", 0.0) or 0.0)
    if build_seconds:
        build_time_by_key[build_key] = build_seconds

    rows: List[Dict[str, Any]] = []
    latencies: List[float] = []
    for position, query in enumerate(queries):
        started = time.perf_counter()
        ranked = system.search(query["query"], top_k=top_k)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if position >= WARMUP_QUERIES:
            latencies.append(elapsed_ms)
        rows.append(
            {
                "id": query["id"],
                "category": query["category"],
                "metrics": metrics.per_query_metrics(ranked, query["graded"]),
                "ranked": ranked,
            }
        )

    overall = metrics.evaluate_group(rows)
    categories = sorted({row["category"] for row in rows})
    by_category = {
        category: metrics.evaluate_group([row for row in rows if row["category"] == category])
        for category in categories
    }

    result: Dict[str, Any] = {
        "system": system.system_id,
        "split": split,
        "n_queries": len(rows),
        "git_commit": git_commit(),
        "embedding_model": model_name,
        "environment": environment_info(),
        "corpus": corpus_stats,
        "index_build_seconds": round(build_time_by_key.get(build_key, 0.0), 3),
        "index_build_mode": "full" if build_fresh else "reused",
        "index_key": build_key,
        "latency_ms": metrics.latency_percentiles(latencies),
        "metrics": {"overall": overall, "by_category": by_category},
        "per_query": [
            {"id": row["id"], "category": row["category"], **{name: round(row["metrics"][name], 4) for name in metrics.METRIC_NAMES}}
            for row in rows
        ],
    }
    return result


def write_result(result: Dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{result['system']}.{result['split']}.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run(
    config: Dict[str, Any],
    queries_path: Path,
    *,
    systems: List[str],
    split: str,
    top_k: int = 10,
    fresh: bool = False,
) -> List[Path]:
    queries = read_queries(queries_path)
    if split != "both":
        queries = [q for q in queries if q.get("split") == split]
    else:
        raise SystemExit("run one split at a time (write separate files per split)")

    corpus_files = corpus_files_from_source()
    corpus_stats = {"files": len(corpus_files)}

    problems = validate_queries(queries, corpus_files)
    if problems:
        for problem in problems:
            print(f"QUERY PROBLEM: {problem}")
        raise SystemExit(f"{len(problems)} query problem(s); fix bench/queries.jsonl first")
    if not queries:
        raise SystemExit(f"no queries with split={split!r} in {queries_path}")

    mirror = prepare_corpus_mirror()
    all_systems = make_systems(config, mirror)
    unknown = [s for s in systems if s not in all_systems]
    if unknown:
        raise SystemExit(f"unknown system(s): {', '.join(unknown)}; known: {', '.join(sorted(all_systems))}")

    model_name = config["embedding"]["model"]
    build_times: Dict[str, float] = {}
    outputs: List[Path] = []
    try:
        for system_id in systems:
            system = all_systems[system_id]
            result = run_system(
                system,
                queries,
                split=split,
                top_k=top_k,
                fresh_index=fresh,
                build_time_by_key=build_times,
                corpus_stats=corpus_stats,
                model_name=model_name,
            )
            outputs.append(write_result(result))
    finally:
        for system in all_systems.values():
            system.close()
    return outputs
