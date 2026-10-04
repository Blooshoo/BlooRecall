# Pipeline configuration reference

2026-06-25, consolidated by Ingrid Halvorsen. Every config-file key the lab
runs with, on one page. Environment-pinned values live in the two handbooks,
not here; this page is the config file only.

## Keys

### retry_policy.max_attempts

Render re-encode attempts before a fragment is quarantined. Default 2.
Between attempts the fragment is requeued immediately (zero delay). Scope:
render farm. The full decision record is `docs/render-retry-policy.md`.
Caution: the same key name appears in other projects' configurations with
other meanings — always check the scope of the block you are editing before
changing it. Within this repo it means the farm ceiling and nothing else.

### max_inflight_frames

Tracker association inflight cap — the maximum number of boxes held live in
the association matrix at once. Default 512. The February cohort peaked at
347; raising the cap further only grows memory. Lower it only with the
architecture guide's memory numbers in hand.

### occlusion_bridge.window_frames

Coast cap for hidden stretches, in frames. Default 45. Matches occlusion
protocol v2 and the tracker's environment contract; if one of the three moves,
all three move together, and the bridging stress re-runs.

### encoder.ladder.preset

Which ladder the farm encodes against. Default: the April ladder (working
rung 7 Mbps, headroom 10). See `docs/bitrate-ladder.md` for the rungs and the
deviation rules.

### intake.cohort.frames_soft_cap

Bram's soft cap per cohort, default 250000. The hose closes cohorts cleanly
at the cap; actual sizes land within one GOP above it.

### ledger.roll.hour

Ledger roll time, 01:30 lab-utc. The roll is when compaction runs, the
kindled pool re-heats, and stale carriers retire. Moving it is a lab-wide
event, not a config tweak.

## Conventions

Keys are snake_case, scoped by subsystem prefix where one exists. No key may
be read by a subsystem outside its scope line; the one documented collision
above is the reason the scope line exists at all.
