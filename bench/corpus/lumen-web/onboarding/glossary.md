# Glossary

Short definitions, the way we actually use these words. Written 2026-01-08 by Dot; argue in the ops channel.

## Boards

A titled arrangement of charts and numbers — the main screen. It has an owner, a range, and (since early 2026) a master strip.

## Tiles

The smallest unit on a board: one visual, one query, one refresh cadence. It can be pinned, snoozed, or narrowed by its neighbors.

## Watchers

A rule that compares a series against a threshold and pages when the condition holds for enough consecutive checks. Cadence and hysteresis live in the rev 2 specification.

## Rollups

Pre-aggregated series at 10-second, minute and coarser grain. Charts read these instead of raw ticks beyond 30 days; the columnar store holds them.

## Digests

The Monday morning email: state changes per rule, totals per board, plus the "top movers" card. The decline rate is tracked monthly (22% as of January).

## The estate

Our collective name for everything one deployment covers: clusters, series, and every titled surface in between. "Estate shape" appears in every capacity table and means the same shape each time.
