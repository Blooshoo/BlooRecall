# Alert thresholds (v1)

Status: **kept as baseline.** The live values moved to
`runbooks/alert-thresholds-v2.md` in February 2026; this sheet is retained
so future-threshold arguments have a starting point. Do not edit.

Board: `weathervane`, house dashboard. Alerts route to the household board
only — no phones, no email. Anything that cannot survive until someone
walks past the board does not belong on this list; that is what the UPS
shutdown scripts are for.

## Storage (bramble)

| Gauge | Warn | Critical |
|---|---|---|
| `pool_util_pct` | 85 | 95 |
| scrub age (days) | 35 | 45 |
| mirror job green-streak broken | immediately | — |

Notes: 85 percent was picked because the pool grew ~3 GB/day at 2025 rates
and 85 gave "months" of runway. Scrub age critical at 45 because a scrub
runs monthly; two missed scrubs means something is wrong with the box
itself, not the calendar.

## Compute

| Gauge | Warn | Critical |
|---|---|---|
| CPU (any box, 5-min avg) | 90 | 97 |
| load/1 (marquee) | 4 | 8 |
| resolver response p95 (ms) | 200 | 1000 |

The CPU numbers exist mostly to catch runaway transcodes; the resolver p95
is the early-warning for the provider brownouts that eventually produced
`runbooks/dns-caching-layer.md`.

## Network

| Gauge | Warn | Critical |
|---|---|---|
| WAN loss pct (10-min) | 2 | 10 |
| storage VLAN latency p95 (ms) | 15 | 60 |
| switch port flap count (hour) | 3 | 10 |

Port flap warn at 3/hour was set after the PoE injector summer of 2025;
ten in an hour means something is physically wrong on the run.

## Review cadence

Reviewed whenever a threshold fires more than twice in a month without
producing an action. v2 exists because exactly that happened to the pool
gauge in January.
