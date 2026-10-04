# Build matrix — components, tiers, cadence

Author: Rosa Lindqvist. Date: 2026-06-22. Maintained by the tools owner (currently Rosa, per handoffs/2026-07-10-tools-handoff.md).

## Current component versions

| Component | Version | Notes |
|---|---|---|
| driftline | **v0.16.3** | Festival candidate 1, cut 2026-06-22 from the 0.16 line |
| ridgeline | **0.10.1** | Engine pinned to this for the demo; no engine churn during content freeze |
| toolpack | **3.5.0** | Editor, importer, tile tools. The trim-handle snapping bug fix lands in 3.5.1 (pending, see the handoff doc) |

The nightly build tag format is `dl-nightly-YYYYMMDD` (local cut date). Candidate tags get `-rcN` suffixes; exactly one candidate carries the festival tag at a time and the ship checklist (meetings/2026-08-24-ship-checklist.md) says which.

## Hardware tiers

| Tier | Machine | Role |
|---|---|---|
| Reference box | 4-core x86 mini-PC, integrated GPU, 16 GB, lab shelf 2 | Every gate in plans/demo-build-plan.md closes on this box or not at all |
| Laptop tier | 2-core, 8 GB, the oldest laptop that survives the route | Existence check only — if it cannot finish the route, that is a bug; if it is ugly, that is the tier |
| Show-floor box | Hardened mini-PC in the padded flight case, image frozen per candidate | Gets its build one full week before travel, then the case closes |

## Cadence

- Nightly: 02:00, automatic, from the main line. Fails loud to the tools owner.
- Weekly candidate: Thursdays from 2026-08-10, cut by hand, gate list attached.
- The festival build: one candidate, blessed by Priya, installed on the show-floor box, case closed. No travel-day installs — this rule is written in the demo plan and repeated here because it is the one everyone tries to negotiate at the airport.

## Ownership

Builds, the cutter for attract mode, the capture tooling, and this matrix: the tools owner. Until 2026-07-10 that was informal (Tomás); after the handoff it is Rosa's explicitly. If the nightly fails twice in a row, escalation is Priya, not silence — the March double-failure went unreported for four days and cost the team a week of late builds.
