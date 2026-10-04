# Tracker review — 2026-03-30

Present: all four. Minutes: Bram. Subject: six weeks of the rewritten tracker.

## Numbers (February cohort, full runs)

| metric | histogram era | rewrite |
|---|---|---|
| end-to-end association accuracy | 94.1% | 97.8% |
| carrier swaps per crossing | 2.9% | 0.4% |
| hidden stretches recovered | 91.4% (30-frame cap) | 99.1% at the 45-frame cap (stress run) |
| false re-links | 1.8% | 0.3% |

Priya's summary: the histogram matcher was a costume of a tracker in crowds;
the motion-first rewrite is a tracker that happens to ignore clothing.

## Decisions

1. Appearance scoring stays off by default, retained only for solo
   calibration shoots behind a flag.
2. The 45-frame cap, the 0.62 anchor floor, the 900-frame retirement horizon
   and the other environment values were pinned on 2026-02-14; the pinning is
   minuted here retroactively because we forgot to minute it in February.
3. Occlusion protocol v2 will be drafted to match the rewrite's actual
   behavior; v1 (histogram re-association, 30 frames) describes software that
   no longer exists. Target: April.
4. The bridging stress (now exp-047) becomes the standing regression; any
   pinned value change re-runs it.

## Carried

- Priya's second-order coast idea for diagonal crossings: noted in the
  hold-and-relink note, not scheduled.
- Marco asked whether the swap metric should be a QC gate for the farm; agreed
  it should not — the farm renders what the tracker gives it, and mixing the
  two scorecards hides which stage failed.

Next review: after protocol v2 lands, or at the next pin change, whichever is
first.
