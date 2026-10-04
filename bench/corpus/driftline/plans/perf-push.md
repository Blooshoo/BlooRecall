# Performance push — May/June 2026

Owner: Marisol Vega, with Tomás Iriarte. Date: 2026-05-25. Follows the 2026-05-18 war room. Closes when the gate below is green on the reference box.

## The gate

**p95 delivered frame ≤ 16.6 ms on the reference box, running the full Kiln Run descent (nodes K-01–K-12) with two concurrent sparklines at full detail and all vent emitters live.** Not the average — the p95. The average has been under the line since April; the tail is what players feel as unevenness, and the tail is what this push is for.

## Where the tail came from (war-room data)

Ranked by contribution to the 21.4 ms p95 measured on the kiln descent, 2026-05-14 build:

1. Particle simulation overruns (emitters unbounded during vent storms) — ~2.1 ms of tail.
2. Atlas service stalls colliding with pose solves — ~1.4 ms.
3. Batch rebuilds on world transitions — ~0.9 ms.

## Actions

| Action | Owner | Due | Notes |
|---|---|---|---|
| Emitter retirement: protect newest 2, shed detail from the rest | Marisol | 2026-06-01 | ships in 0.15.0 |
| Atlas service admission cap enforcement (2 pages/frame, hard) | Marisol | 2026-06-01 | already specced in specs/fox-sprite-cache.md; enforce at the service, not the caller |
| Prewarm tie-in: route-critical pages never admitted mid-route | Tomás | 2026-06-08 | extends specs/cold-start.md |
| Batch sort-key simplification (drop the 3rd key tier) | Marisol | 2026-06-08 | measured win, invisible cost |
| Budget doc with the final numbers | Marisol | 2026-06-18 | becomes specs/rendering-pipeline.md |

## Memory ceiling

### Resident budget

We hold the line at **1.8 GB resident on the demo route**. Above that line, the smallest atlas tier starts getting dropped, then the prewarm list truncates to route-critical pages only, then — and only then — do we talk about cutting content. The tiers fire in that order and no other; ad hoc cuts during a push are how projects ship with mysterious holes.

## Rules for the push

- No optimization lands without a before/after p95 recording on the reference box, attached to the build note.
- Nothing in this push may change gameplay-visible behavior. If an optimization would, it becomes a design conversation, not a perf commit.
- The gate is re-measured after *every* action lands, not just at the end — a push that only measures at the end cannot tell you which action broke it.
