"""CLI: python -m bench.run --config bench/config.bench.json --queries bench/queries.jsonl \
        --system hybrid --split test [--fresh] [--list-systems]

Writes bench/results/<system>.<split>.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bloorecall.util import PROJECT_ROOT

from bench.runner import run


def load_bench_config(path: Path) -> dict:
    from bloorecall.config import load_config

    return load_config(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bench.run", description="BlooRecall retrieval benchmark")
    parser.add_argument("--config", default="bench/config.bench.json")
    parser.add_argument("--queries", default="bench/queries.jsonl")
    parser.add_argument("--system", default="all", help="comma-separated system ids, or 'all'")
    parser.add_argument("--split", default="test", choices=["dev", "test"])
    parser.add_argument("--fresh", action="store_true", help="rebuild indexes from scratch first")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--list-systems", action="store_true")
    args = parser.parse_args(argv)

    config = load_bench_config(PROJECT_ROOT / args.config)
    from bench.systems import make_systems

    known = sorted(make_systems(config, PROJECT_ROOT / "bench" / "corpus"))
    if args.list_systems:
        print("\n".join(known))
        return 0
    systems = known if args.system == "all" else [part.strip() for part in args.system.split(",") if part.strip()]

    paths = run(
        config,
        PROJECT_ROOT / args.queries,
        systems=systems,
        split=args.split,
        top_k=args.top_k,
        fresh=args.fresh,
    )
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
