# Changelog

All notable changes to lumen-web. Dates are ship dates (UTC).

## lumen-web v4.3.0-rc.1 — 2026-09-22

- New query planner behind the `PLANNER_V2` flag (see adr/0018).
- Focus mode: single-tile full-viewport view with dimmed surrounding frame.
- Compaction overhaul dry-run build for the November scale test.

## lumen-web v4.2.0 — 2026-06-18

- Boards hydrate tile-by-tile; first paint lands roughly 40% earlier on 20-tile boards.
- Watcher snooze from the tile menu (30 minutes, 2 hours, rest of day).
- New compact trend tile: single series, dense mode, 120 px default width.
- Scheduled summaries support "top movers only" cards.

### lumen-web v4.2.4 — 2026-08-27

- Fix: hour buckets straddling a DST jump rendered with a 1-hour skew in viewer-local mode.
- Fix: range picker thumb could stick after drag on touch devices.

## lumen-web v4.1.0 — 2026-03-05

- Static copy pipeline GA: tiles as PNG, boards as paginated A4 documents.
- Board master strip for syncing pickers across tiles.

### lumen-web v4.1.1 — 2026-03-09

- Palette refactor rollout, first half of the token migration.

### lumen-web v4.1.2 — 2026-03-15

- Hotfix: reverted the 4.1.1 palette rollout after the accent regression (see incidents/2026-03-14).
- Adds the screenshot-diff gate for palette-affecting changes.

### lumen-web v4.1.3 — 2026-03-20

- Notifier collapse window exposed per watcher.

## lumen-web v4.0.0 — 2026-01-15

- Columnar store rev 2 grain plan: 10-second base tier (adr/0009 rev 2).
- Streaming on-demand artifacts replace the nightly batch worker (adr/0011).
- Boards: tile-to-tile narrowing GA.

## lumen-web v3.9.0 — 2025-10-28

- First GA of threshold watchers.
- Fixed 12-column board grid.

### lumen-web v3.9.4 — 2025-11-10

- Hotfix: sampler coalescer skips-and-marks instead of emitting zeros (see incidents/2025-11-08).

## lumen-web v3.8.0 — 2025-09-30

- First private beta: boards, tiles, CSV ingest, Monday summary email.
