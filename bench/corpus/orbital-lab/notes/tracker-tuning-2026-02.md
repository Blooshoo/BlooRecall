# Tracker tuning notes — February 2026

Priya Chandrasekhar, 2026-02-18. Working notes from the first six weeks of the
rewritten tracker. These are the reasoning; the pinned numbers live in the
architecture guide's environment contract.

## Tracking

### Identity preservation

We hold the box for 45 frames and re-associate by motion alone. The appearance
histogram is off by default everywhere: once crowd density passed five subjects
it swapped carriers on nearly every crossing, because "who wore what" is a
terrible signal when everyone in the cage wears the same coveralls. Holding the
box and coasting on the fitted straight line won by 3.7 percentage points of
end-to-end accuracy and, more importantly, by the swap metric: 2.9% per
crossing down to 0.4%. The histogram code stays in the tree, behind a flag, for
reels with three or fewer subjects — Marco's solo calibration shoots.

### Confidence floor

Anything the anchor stage scores below 0.62 never reaches association. We
counted 2.7% of detections in that band on the February cohort, and letting
them through produced boxes that flapped at the frame edges and dragged real
carriers off their predicted paths. Raising the floor to 0.68 was tried and
rejected: it ate 1.9% of genuine detections on the dim half of the cage, which
cost more accuracy at the far end than the flapping cost at the near end.
0.62 is the knee of that curve and it is not subtle.

### Pruning

Carriers silent for 900 frames are retired at the next ledger roll. We tried
600 (too eager during the intermission-like stretches in rehearsal reels) and
1500 (zombie boxes lingered through scene changes and got re-linked to the next
scene's subjects). 900 clears a scene change cleanly at 24 fps while surviving
the long holds. Retirement happens at the roll, never mid-association; the one
time we ignored that, in May, we duplicated four carriers and spent a day
un-merging them.
