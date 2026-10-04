#!/usr/bin/env bash
# Read-only drift audit: re-hash indexed sources against disk, detect ghosts,
# orphans, unindexed files, and ownership mismatches.
#
# Exit codes: 0 clean, 1 drift, 2 error.
# Safe to run repeatedly from cron/CI — never writes to the index or corpus.
#
# Example crontab line (owner decides whether to install it):
#   0 6 * * *  /path/to/bloorecall/scripts/bloorecall-verify-drift.sh >> /path/to/bloorecall/var/verify-logs/cron.log 2>&1
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/var/verify-logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/verify-$(date -u +%Y%m%dT%H%M%SZ).json"

# Run the audit in deep mode; capture exit code without killing the script.
python3 "${PROJECT_ROOT}/scripts/bloorecall-verify-drift.py" --json > "${LOG_FILE}" 2>&1
EXIT_CODE=$?

cat "${LOG_FILE}"

# Keep 30 days of verify logs.
find "${LOG_DIR}" -name 'verify-*.json' -mtime +30 -delete

exit "${EXIT_CODE}"
