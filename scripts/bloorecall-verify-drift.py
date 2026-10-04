#!/usr/bin/env python3
"""Standalone read-only drift audit for BlooRecall.

Walks every indexed source against disk, re-hashes (deep mode catches
size+mtime-preserving rewrites), checks ownership, and detects orphans /
unindexed files.  Exit codes: 0 clean, 1 drift, 2 error.

Usage:
  python3 scripts/bloorecall-verify-drift.py [--config PATH] [--no-deep] [--json]

Crontab example (add to crontab -e if desired):
  0 6 * * *  /path/to/bloorecall/scripts/bloorecall-verify-drift.sh >> /path/to/bloorecall/var/verify-logs/cron.log 2>&1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from bloorecall.config import load_config  # noqa: E402
from bloorecall.verify_drift import run_drift_audit  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BlooRecall read-only drift audit (Heimdall verify --deep ported)"
    )
    parser.add_argument("--config", help="path to config.json (default: project config.json)")
    parser.add_argument(
        "--deep",
        dest="deep",
        action="store_true",
        default=True,
        help="re-hash every source even if mtime/size match (default)",
    )
    parser.add_argument(
        "--no-deep",
        dest="deep",
        action="store_false",
        help="only stat-check (faster, misses silent content rewrites)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args()

    config = load_config(args.config)
    return run_drift_audit(config, deep=args.deep, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
