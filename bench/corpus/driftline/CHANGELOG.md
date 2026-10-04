# driftline changelog

Owned by Priya Raman. One entry per shipped internal build, newest first. This file records what changed and why, briefly; the specs and plans in this folder carry the detail.

## 0.16.1 — 2026-09-02
- Fixed: capture star freeze trimmed from 90 ms to 40 ms (Tomás). Testers on the show-floor box read the pause as a crash.
- Fixed: Kiln Run vent K-06 up-blast now applies a consistent 140 u/s; it was drifting low at high tick counts (Dev). See levels/kiln-run.md.

## 0.16.0 — 2026-08-10
- Added: festival route locked — Lowline Quarries complete plus Kiln Run nodes K-01 through K-08. See plans/demo-build-plan.md.
- Added: attract-mode loop built from starred captures, 90 s cut (Tomás, Rosa).
- Changed: grade LUT locked to the warm festival grade; the cool variant stays behind a debug toggle (Marisol).

## 0.15.0 — 2026-06-15
- Added: renderer budget pass landed; the full numbers and the failure modes live in specs/rendering-pipeline.md (Marisol).
- Added: prewarm and resource admission shipped — cold p95 tail on the opening route down from 2,800 ms to 400 ms on the reference box. See specs/cold-start.md.
- Changed: emitter retirement under load; the newest two emitters are protected, the rest shed detail first (Marisol).

## 0.14.0 — 2026-04-25
- Changed: checkpoint policy v2 — trusted nodes at 60–75 s spacing, respawn keeps 40% of entry speed along the path tangent. Supersedes the 45 s / full-snapshot policy. See plans/checkpoint-policy-v2.md.
- Added: node audit tooling and the first full audit of Kiln Run (Dev). See levels/checkpoint-audit.md.

## 0.13.0 — 2026-03-08
- Changed: coyote time v2 — layered window (100 ms base, up to 160 ms at speed). Supersedes the flat 120 ms window from 0.9.0. See specs/coyote-time-v2.md.
- Added: input latency pass — poll cadence raised and a stale-report guard added. See specs/input-latency.md.
- Added: Quick Capture architecture doc after the February playtest. See specs/quick-capture-architecture.md.

## 0.12.0 — 2026-01-30
- Changed: momentum tuning pass 2 numbers — ground acceleration 42 to 38 u/s², friction 260 to 240 u/s², boost surge rework. See plans/momentum-tuning-v2.md.
- Fixed: fox sprite cache pinning — the resident set for the current world no longer evicts under pressure. See specs/fox-sprite-cache.md.

## 0.11.0 — 2025-12-20
- Added: Quick Capture v1 — 12 s rolling ring, hold-the-button capture, star-to-keep. Internal only. See plans/quick-capture-v1.md.
- Added: analog stick handling — radial deadzone replaces per-axis. See specs/thumbstick-deadzone.md.

## 0.10.0 — 2025-11-10
- Added: wall cling (900 ms window, decayed creep after 500 ms). See specs/wallride.md.
- Changed: momentum tuning pass 1 numbers after the November review. See plans/momentum-tuning-v1.md.

## 0.9.0 — 2025-09-28
- Added: first playable on Ridgeline 0.8 — run, boost pads, friction, the Lowline Quarries blockout.
- Added: coyote time v1, flat 120 ms window. See specs/coyote-time.md.
- Added: the momentum model v1 structure. See specs/momentum-model.md.
