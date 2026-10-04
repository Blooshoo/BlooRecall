# Engine-scope config keys

Author: Rosa Lindqvist. Date: 2026-03-16. Scope: engine-scope keys only — the ones Ridgeline itself reads at startup. Feature keys belong to their feature specs (the capture ring's length key is in specs/replay-format.md, the trail emitter's rate is in specs/sparkline-trails.md) and are deliberately not repeated here.

## The keys

| Key | Default | Meaning |
|---|---|---|
| `max_inflight_frames` | 3 | Delivered frames the pipeline may run ahead of presentation. Above 3, input attribution latency (specs/input-latency.md) degrades measurably; below 3, the pipeline starves on the laptop tier. Do not tune this per scene |
| `atlas_pressure_ceiling` | 0.85 | Fraction of the atlas budget (256 MB) at which eviction turns aggressive. Below the ceiling, eviction runs only on admission demand. Raising it trades stalls for residency — we measured 0.90 as strictly worse on every trace |
| `cling_decay_rate` | 60 | Downward creep acceleration (u/s²) applied after the soft phase of a wall cling ends — the number behind specs/wallride.md's decay curve. Gameplay-tunable, engine-read |
| `coast_solver_iters` | 4 | Refinement passes per tick for the slope coast fit (specs/toboggan-hack.md). 3 passes lost the switchback crests in the traces; 5 cost 0.1 ms for no measurable fit gain |
| `input_buffer_depth` | 8 | Simulation ticks of press-side buffer. Pairs with the press-side grace in specs/coyote-time-v2.md (80 ms ≈ 5 ticks; 8 leaves headroom for attributed-tick edge cases) |

## Rules

- Engine keys are read once at startup; nothing here may change mid-session. If a feature needs runtime variation, that is a feature key, and it lives in the feature spec.
- New engine keys need: an owner, a default with a measured justification, and a line in this table. Rosa rejects keys with "tune it later" defaults — later never comes and the default becomes lore.
- The overrides file (profile-local, applied last) uses the same key names; it exists for test rigs and accessibility overrides, not for shipping configurations.

## Provenance notes

- `atlas_pressure_ceiling` was 0.75 during 0.9–0.11; the January traces showed it evicting pages the route needed 40 frames later. 0.85 with the pin list (specs/fox-sprite-cache.md) closed that without growing the budget.
- `cling_decay_rate` shipped at 90 in 0.10.0 and moved to 60 after the kiln playtests read the old value as "the wall gives up on you".
