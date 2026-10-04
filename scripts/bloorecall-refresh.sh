#!/usr/bin/env bash
# Nightly incremental refresh. Safe to run repeatedly: unchanged files are skipped
# and unchanged chunk text is served from the embedding cache.
#
# Example crontab line (owner decides whether to install it):
#   17 4 * * * /path/to/bloorecall/scripts/bloorecall-refresh.sh
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/var/refresh-logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/refresh-$(date -u +%Y%m%d).log"

{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) bloorecall refresh ==="
  "${PROJECT_ROOT}/bin/bloorecall" refresh --json
} >>"${LOG_FILE}" 2>&1

# Keep two weeks of logs; nothing outside this project is ever touched.
find "${LOG_DIR}" -name 'refresh-*.log' -mtime +14 -delete
