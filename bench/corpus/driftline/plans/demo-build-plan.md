# Demo festival build — plan

Owner: Priya Raman. Date: 2026-06-08. The demo is the whole company's fall; this plan is the single source of truth for what is in it.

## Scope

- **Lowline Quarries, complete**: all 14 nodes, including the two damper-crate tests and the beam-hop finale.
- **Kiln Run, first half**: nodes K-01 through K-08, ending on the flue overlook. K-09+ is walled behind a "continues in the full game" board, not an invisible wall — testers said invisible walls read as bugs.
- Route length target: **18–22 minutes** for a first-time player at expected skill.

## Content freeze

**2026-07-20.** After the freeze, only crash fixes, latency fixes, and copy changes. Level changes require Priya's sign-off plus a re-run of the respawn-cost audit (levels/checkpoint-audit.md) for any touched node.

## The route

Intro overlook → quarry teach sequence (run, pads, crates) → beam hops → kiln entry → vertical descent to the flue overlook. One Quick Capture moment is staged per act (three total) so new players *see* the capture button used; the attract loop before the title is cut from starred captures, 90 s, refreshed from each nightly build's playtests.

## Builds and cadence

Rosa cuts the nightly; candidate builds are tagged weekly from 2026-08-10. The festival candidate is whichever candidate passes the gate list below with zero open crash bugs. The show-floor box gets its build one full week before travel — no travel-day installs, that rule exists because of what happened to the last project.

## Gate list (all must be green)

1. p95 frame ≤ 16.6 ms on the reference box over the full route (the perf-push gate, unchanged).
2. Respawn-cost p95 ≤ 900 ms at every node on the route.
3. Cold p95 tail ≤ 600 ms on the reference box (the prewarm gate from specs/cold-start.md).
4. Zero first-use admission warnings on the route (the prewarm log from specs/cold-start.md).
5. Latency rig: 45 ms p95 press-to-response, re-run on the final candidate.
6. Telemetry opt-in screen: readable in under 10 seconds, skippable, no dark patterns (Priya owns the copy).

## Explicitly out

Marrow Flats (full game), Northgale (see levels/pitch-idea.md — not scoped, do not ask), any cloud feature, achievements. The demo has one job: make a stranger want the full game in 20 minutes.
