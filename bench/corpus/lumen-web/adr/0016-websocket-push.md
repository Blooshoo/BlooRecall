# ADR 0016 — Push channel for live tiles

Date: 2026-04-15. Owner: Juno Park. Status: accepted.

## Context

Live tiles polled every 15 seconds. A 20-tile live board issued 80 requests per minute per viewer, and p95 update freshness was 19 seconds — the number felt laggy in every demo.

## Options

1. Keep polling, tune intervals per tile. Cheapest; the freshness ceiling stays.
2. One push socket per tab, fan-out from the ingest bus through a small gateway. More moving parts; freshness drops to about a second.
3. Server-sent events. Simpler, but reconnect semantics on flaky networks cost more than the socket API saves.

## Decision

Option 2. One socket per tab, multiplexed by series set. The ingest bus fans out to a stateless push gateway; any gateway node can serve any tab. Reconnect resumes from the last grain watermark, and after three consecutive failures the tab falls back to 15-second polling until the socket holds for 60 seconds.

## Consequences

- Update freshness p95 target: 1.2 s (validated 2026-04-28 on the replay estate).
- Polling code stays forever — it is the fallback and the load-shedding floor.
- The gateway holds no session state, so deploys are rolling with zero visible reconnects.
