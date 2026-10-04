# ADR 0004 — Nightly batch export worker

Date: 2025-10-08. Owner: Rafa Lindqvist. Status: retired 2026-01-22 by adr/0011. Kept for history.

## Context

Beta customers want board archives: a nightly snapshot of every board as files they can pull first thing each day.

## Decision

One batch job at 02:30 UTC renders every board to a zip archive (PNG tiles plus one CSV per tile) and pushes it to object storage under `exports/<date>/`. The window is up to 6 hours. Boards that fail retry the next night.

## Consequences

- Archives are always one day stale, which the design partners accepted in writing on 2025-10-02.
- A big estate — 300 or more boards — saturates the single render node for the whole window; one poisoned board can starve the rest.
- Retry granularity is per night, which proved far too coarse by December: the audit found 11 boards failing five or more nights in a row with no signal to anyone. See adr/0011 for the replacement.

---

**Retired 2026-01-22 by adr/0011-streaming-export. Do not build on the nightly job.**
