# Runbook — ERR_TILE_5042 (hydration budget exceeded)

First seen: 2026-02-14. Owner: Juno Park. Severity: usually cosmetic; page the frontend tier if it is widespread.

## What it means

A tile failed to fetch and render its data within its 8-second hydration budget, two attempts in a row. The board marks the tile stale and keeps showing the last good frame with a "stale" chip.

Typical log line:

`{"code":"ERR_TILE_5042","budget_ms":8000,"attempt":2,"tile":"rev-parity-7"}`

## Triage

1. One tile on one board: usually a heavy query. Check the tile's series count against the fan-out cap in the board query cache spec.
2. Many tiles on many boards between 06:15 and 07:50 UTC: you are inside the compaction lock window and the warmup crawler has not reached those boards yet. Wait; do not restart anything.
3. Everything, everywhere: check the ingest bus backlog first, then page the data tier (Rafa).

## Recovery

Stale tiles recover on their next refresh; no manual action needed. If one specific tile stays stale longer than 30 minutes, re-save it (edit, then save unchanged) to force a fresh plan.

## Escalate when

More than 5 boards show stale chips at the same moment and the compaction window is not the cause. Attach three affected tile ids to the page.
