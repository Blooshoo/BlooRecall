# Alert thresholds (v2)

Status: **current** (since 2026-02-02). Replaces
`runbooks/alert-thresholds-v1.md`, kept as baseline. Change summary at the
bottom.

Board: `weathervane`, house dashboard. Alerts route to the household board
only — no phones, no email. Anything that cannot survive until someone
walks past the board does not belong on this list; that is what the UPS
shutdown scripts are for.

## Storage (bramble)

| Gauge | Warn | Critical |
|---|---|---|
| `pool_util_pct` (sustained 15 min) | 80 | 90 |
| scrub age (days) | 35 | 45 |
| mirror job green-streak broken | immediately | — |

Notes: warn moved 85 → 80 and critical 95 → 90 after the January
near-miss, where the pool crossed the old warn line during a single
weekend of large imports and the first page nobody saw was the useful one.
New in v2: the 15-minute sustain. Without it, every bulk copy to the pool
alerted for exactly as long as the copy ran, and alert fatigue set in
within a week.

## Compute

| Gauge | Warn | Critical |
|---|---|---|
| CPU (any box, 5-min avg) | 90 | 97 |
| load/1 (marquee) | 4 | 8 |
| resolver response p95 (ms) | 200 | 1000 |

Unchanged from v1; they earn their keep quietly.

## Network

| Gauge | Warn | Critical |
|---|---|---|
| WAN loss pct (10-min) | 2 | 10 |
| storage VLAN latency p95 (ms) | 15 | 60 |
| **new:** `zvol_lat_ms` (read, 5-min) | 40 | 120 |
| switch port flap count (hour) | 3 | 10 |

`zvol_lat_ms` is new in v2 and exists specifically because of the January
evening contention problem (recordings job vs sessions): pool-level
utilization was flat while session latency spiked. This gauge is the one
that actually sees that class of problem.

## Review cadence

Same rule as v1: reviewed whenever a threshold fires more than twice in a
month without producing an action.

## Changes from v1

- pool warn 85→80, critical 95→90, 15-minute sustain added.
- read-latency gauge added to the network table.
- everything else untouched on purpose; v2 is a correction, not a rewrite.
