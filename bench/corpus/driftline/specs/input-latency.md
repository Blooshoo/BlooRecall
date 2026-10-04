# Input latency budget

Author: Tomás Iriarte. Date: 2026-03-30. Status: shipped in 0.13.0. Re-measure after any change to the presentation path.

## Targets and measured state

End-to-end latency (physical press to first visible response) target: **45 ms p95** on the reference box. Measured on the 2026-03-06 build: **47 ms p95, 38 ms median**, over 5,000 recorded presses across 3 routes with the hardware counter rig. The two worst contributors were poll cadence (see below) and one avoidable presentation stall.

## Poll cadence

The engine polls controllers at **240 Hz** via the `input_poll_hz` config key, regardless of the device's report rate, and timestamps each report on arrival. Polling faster than the report rate is nearly free and removes up to one poll interval of quantization from the timestamp; the timestamp is what the rest of the pipeline uses to attribute the press to the correct simulation tick.

A guard surrounds the poll: if a poll returns no new report for more than **25 ms** — a device stall, a wireless hiccup — the engine raises `ERR_INP_STALE_203`, holds the last state, and marks the frame. Held state is *not* predicted forward; the fox just holds. Testers consistently preferred a held pose over a guessed one during the forced-disconnect trials.

## Attribution to ticks

The simulation is a fixed 60 Hz step. A press is attributed to the tick whose window contains its timestamp; a press landing after a tick's window is consumed by the *next* tick, with one tick of prediction allowed at the presentation layer so the response does not visibly wait. This costs one tick of perceived latency in the worst case (~16.7 ms) and is why the median is 38 rather than 55.

## Where the remaining milliseconds are

| Segment | p95 (ms) |
|---|---|
| Device to poll timestamp | 6 |
| Poll to tick consumption (avg half-window) | 8 |
| Simulation | 3 |
| Pose + render submission | 11 |
| Presentation queue | 15 |
| Display | 4 |

The presentation queue number was 22 before the March pass; the fix was not letting the capture ring flush on the same submission (see specs/quick-capture-architecture.md, the star freeze).

## Rules

- No gameplay system may read device state directly; everything goes through the attributed-tick path or the latency numbers above stop being true.
- Any change to the presentation path (post stack order, atlas service scheduling) requires a re-run of the 5,000-press rig before the change ships. Marisol and Tomás co-own the rig.
