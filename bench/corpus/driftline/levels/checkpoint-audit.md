# Kiln Run node audit — respawn costs and placement

Author: Dev Okonkwo. Date: 2026-04-27. Audited against the 0.14.0 build on the reference box. Companion to plans/checkpoint-policy-v2.md; this is the measurement that policy's placement rules lean on.

## Method

For each of the 22 kiln nodes: 10 respawns from the node, instrumented fade-out to control-return, p95 reported. Ten restorations per node (the delta-encoding load path), plus one full-route sweep to catch interaction effects. Runs done 2026-04-21 through 2026-04-24.

## Results by node (p95, ms)

| Node | p95 | Note |
|---|---|---|
| K-01 | 610 | |
| K-02 | 640 | |
| K-03 | 690 | |
| K-04 | 700 | |
| K-05 | 720 | |
| K-06 | 750 | long vent, more live entity deltas to restore |
| K-07 | 1,080 | **over the line pre-fix** |
| K-08 | 1,120 | **over the line pre-fix** |
| K-09 | 780 | |
| K-10 | 760 | |
| K-11 | 740 | |
| K-12 | 1,050 | **over the line pre-fix** |
| K-13 | 800 | |
| K-14 | 810 | |
| K-15–K-22 | 690–840 | shelves, no offenders |

## What the offenders had in common

### Respawn cost

From fade-out start to control return, the p95 across the audited nodes is 840 ms on the reference box, measured on the April build. The three over the line (K-07, K-08, K-12) all sat in cling-heavy sections where the pre-node world deltas included vent columns and broken-tile state; their restoration sets ran 3–4× the median delta count. The fix was not engine work — Dev slimmed each node's pre-node delta set (vent columns restore from column state, not per-entity state) and all three dropped under 900 ms on the re-run (K-07: 860, K-08: 870, K-12: 850).

## Placement conformance

- Every node passes the "reachable into at 480 u/s without a forced stop" rule after two moves (K-04 shifted back to the shelf, K-19 likewise).
- Every node sits on trusted flat ground; zero slope-top nodes, per policy v2 rule 2.
- Spacing conformance: all inter-node expected-path gaps land in the 60–75 s band except K-09→K-10 (58 s, accepted — the flue exit is where it is).

## Standing rule

Any node edit re-runs the 10-respawn measurement for that node before it ships. The 900 ms p95 line is a ship gate (plans/demo-build-plan.md, gate 2). The audit tooling Rosa wrapped around this (build 0.14.0+) makes the re-run a five-minute job; there is no excuse.
