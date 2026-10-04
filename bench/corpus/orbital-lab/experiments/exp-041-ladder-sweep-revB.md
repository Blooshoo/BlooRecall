# exp-041 — ladder sweep, second pass (revB)

Date opened: 2026-05-02. Owner: Marco Deluca. Status: adopted; the current farm
ladder comes from this record.

## Objective

Find the cheapest ladder that survives the farm QC gates, so we stop paying
for bitrate nobody can see.

## Setup

Encode the seed clips at every ladder point on two farm nodes (renderlet-04 and
renderlet-11), score each output against the cage master, and plot the metric
against bitrate. Same node, same encode settings, only the ladder point moves.
revB re-runs the exp-038 plan after the renderlet-04 VRR fix of 2026-04-29, so
both nodes contribute clean rows this time.

## Ladder points

3, 5, 7, 10 Mbps. Lowered one notch across the board versus the first pass,
because the first pass found headroom at every qualifying rung.

## Seed clips

Set A: 12 clips from the November cohort — 4 static-camera, 4 pan, 4 crowd.
Chosen once, checksummed, and never swapped mid-sweep. revB adds 6 crowd clips
from the February cohort (set B) because crowd seeds drove every failure last
time and 4 felt thin.

## Passes

Three passes per point. Pass-to-pass spread above 1.5 fragment-score points
invalidates the point and it is re-run.

## Metrics

PSNR against cage master, and the fragment score we use for QC. A ladder point
qualifies only if every seed clip in sets A and B passes both QC gates at that
rung.

## Acceptance

The adopted ladder is the lowest qualifying set of points, plus one rung of
headroom above the fastest motion clip. The result becomes the farm default
and is written into the ladder reference.

## Log

2026-05-02 — sweep opened, both nodes clean. 2026-05-04 — 3 Mbps fails set B
outright (6 of 6 crowd clips); 5 Mbps fails 2 of 6 crowd clips. 2026-05-06 —
7 Mbps passes all 18 seeds on both nodes; 10 Mbps passes with margin as
expected. 2026-05-07 — three-pass spread under 0.8 points everywhere.

## Outcome

Adopted ladder: 7 Mbps working rung with 10 Mbps as the headroom rung; 3 and 5
struck. Farm default switched 2026-05-07; QC gates unchanged.
