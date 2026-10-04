# exp-038 — ladder sweep, first pass

Date opened: 2026-04-11. Owner: Marco Deluca. Status: superseded by revB below.

## Objective

Find the cheapest ladder that survives the farm QC gates, so we stop paying
for bitrate nobody can see.

## Setup

Encode the seed clips at every ladder point on two farm nodes (renderlet-04 and
renderlet-11), score each output against the cage master, and plot the metric
against bitrate. Same node, same encode settings, only the ladder point moves.

## Ladder points

4, 6, 8, 12 Mbps.

## Seed clips

Set A: 12 clips from the November cohort — 4 static-camera, 4 pan, 4 crowd.
Chosen once, checksummed, and never swapped mid-sweep.

## Passes

Two passes per point. Pass-to-pass spread above 1.5 fragment-score points
invalidates the point and it is re-run.

## Metrics

PSNR against cage master, and the fragment score we use for QC. A ladder point
qualifies only if every seed clip passes both QC gates at that rung.

## Acceptance

The adopted ladder is the lowest qualifying set of points, plus one rung of
headroom above the fastest motion clip. The result becomes the farm default
and is written into the ladder reference.

## Log

2026-04-11 — sweep opened. 2026-04-13 — the 4 Mbps rung fails on crowd clips
(mush in the upper third of the frame); 6 Mbps marginal on 2 of 4 crowd seeds.
2026-04-15 — renderlet-04 showed the VRR quirk mid-sweep (clock drift under
sustained load), invalidating its 8 and 12 Mbps rows. Rows re-run on
renderlet-11 only, flagged in the ledger.

## Outcome

6/8/12 qualifies; 6 is wobbly on crowd seeds. Decision deferred to a second
pass after the renderlet-04 clock fix — this record is kept for the invalid
rows and the reasoning, not for the numbers.
