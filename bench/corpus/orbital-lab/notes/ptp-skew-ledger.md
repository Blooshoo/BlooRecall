# Skew ledger

Living table of per-rig clock offsets against the reference card. Maintainer:
Bram Oosterhuis. This file is appended to, never rewritten; corrections are new
entries that name the entry they correct.

## Rules

- Raise `ERR_PTP_DRIFT_92` when a rig's offset exceeds 250 µs for 30 seconds
  or more. The code is registered here and nowhere else.
- Config: `ptp.symmetry_margin_us = 400`. Why 400: see exp-050 — the margin
  exists to catch broken paths, and healthy paths measure in the hundreds of
  nanoseconds.
- No reel is graded against a rig with an open code. Grading waits or uses
  another rig's view.

## Entries

- 2025-11-04 — ledger started. All 20 rigs under 1 µs against the reference.
- 2026-01-13 — during the heat week, rig 14's offset rose to 96 µs at die
  temperature peak. Within margin, logged for the pattern.
- 2026-02-03 — rig 9 hit 312 µs for roughly 2 minutes after the switch swap.
  `ERR_PTP_DRIFT_92` fired once, correctly. Resolved by re-seating the timing
  card; entry kept as the code's first real catch.
- 2026-04-30 — rig 3 begins coasting late after its fan swap. Cross-referenced
  in the June drift audit; card was left on the shared bus.
- 2026-06-15 — rig 3's card moved to the dedicated slot; offset back under
  1 µs. The audit note has the full story and the numbers.
- 2026-07-21 — margin re-affirmed after the symmetry measurements (exp-050).
  Median path asymmetry 112 ns; margin unchanged at 400 µs.

## Standing note

The ledger is boring 95% of the time. That is what success looks like here;
the interesting ledger is the one where footage cannot be graded.
