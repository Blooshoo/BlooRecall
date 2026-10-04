# Ridgeline engine API — notes for driftline

Author: Tomás Iriarte and Marisol Vega. Date: 2026-01-12. Living notes; the engine is in-house so the API is ours to fix, which means these notes age. When something here is wrong, fix the engine or fix the note — do not let both drift.

## Gameplay-facing calls

### `resolve_coyote_window(speed_at_leave) -> ms`

The single source of truth for the grace window. Gameplay code, the debug overlay, and the test harness all call this instead of reimplementing the layered rule from specs/coyote-time-v2.md. When the rule changed from v1's flat 120 ms, having the one function meant the overlay and the harness updated themselves. Take speed in u/s, return whole milliseconds, never a float — the harness compares exactly.

### Input attribution

`input_attribution_t` carries (timestamp, device, magnitude vector) from the poll into the tick. Gameplay never reads device state directly — specs/input-latency.md's latency numbers are only true as long as that stays enforced. The struct is small on purpose; if someone needs a field added, the latency rig re-run is part of the review, by rule.

## Render-facing calls

### `rpush_sprite_batch(layer, sort_key, quads)`

The only legal way to submit quads. Two sort-key tiers since the May war room dropped the third (see plans/perf-push.md). Rules the signature cannot express:

- **Never hold a batch across an atlas eviction.** Eviction can invalidate the page your quads point into; the batch must be submitted in the same service window it was built.
- Layer indices are banded (0–7 world, 8–9 effects, 10 UI); the bands are load-bearing for the post stack order in specs/rendering-pipeline.md.
- 8,192 quads per batch buffer is the cap — overflow raises ERR_RIDGE_112 (see reference/error-codes.md).

## Diagnostics

### `ridge_frame_stats_t`

Per-frame timing struct the debug overlay prints: sim, pose solve, batch build, atlas service, particle sim/draw, lights, post, UI, present, slack. If you add a pipeline stage, you add a field here in the same change or the overlay lies by omission, which is worse than crashing.

### `ridge_timeline_push(marker)`

Profiler marker, zero-cost when the overlay is off, writes into the frame graph when on (F8, see reference/debug-overlay-keys.md). Convention: markers are `system:detail` lowercase with a colon — `atlas:pagein`, `sim:vents`, `capture:save`. The frame graph groups on the prefix.

## Gotchas learned the hard way

1. `resolve_coyote_window` must be called with the *leave* speed, not current speed — during the window they differ, and the harness catches it but the overlay won't.
2. The atlas service admits at most 2 pages per delivered frame *at the service*, not the caller (war-room decision, 2026-05-18). Callers that batch their own admission are lying about the cap.
3. `ridge_frame_stats_t` is written at present time; reading it mid-frame gives last frame's truth, which is usually what you want, but document that in the tool you write, not in a chat message.
