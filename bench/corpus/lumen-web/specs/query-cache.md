# Board query cache and grain selection

Author: Rafa Lindqvist, 2026-04-20. Status: current.

## Cache shape

Results memoize per (series set, range, grain) at the board level, not per tile — tiles sharing a series set share one fetch. Hit rate on the replay estate: 61% (measured 2026-04-14 across 2,400 queries).

## Staleness

`query.cache_stale_ms` bounds how long a memoized result serves before a background refresh kicks off. Default 45,000. Live tiles bypass the memo entirely; they ride the push channel.

## Fan-out cap

`rollup.max_series` caps how many series a single tile query may fan out over. Default 3,000. Beyond the cap, the query layer steps the grain coarser until the fan-out fits; if it never fits, the tile renders its top 3,000 series by latest value and shows a "truncated" chip.

## Why a cap and not an error

The 2026-02-24 review showed wildcard series picks regularly exceeding 10,000. An error trained nobody; a coarser grain with a visible chip keeps the board honest and the estate alive.

## Tuning table

| Estate shape | rollup.max_series | query.cache_stale_ms |
| --- | --- | --- |
| Small, under 100 boards | 3000 | 45000 |
| Wildcard-heavy | 1500 | 30000 |
| Executive summaries | 6000 | 120000 |

Changed values need a restart of the service tier only; the web tier picks them up within one staleness window.
