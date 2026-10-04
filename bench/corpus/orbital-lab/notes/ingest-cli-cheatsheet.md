# Intake CLI cheat sheet

Bram Oosterhuis, 2025-11-19. The hose's command line — the three flags we
actually type, with the exact spelling, because the man page buries them.

## --deinterlace-safe

Pads fields before pull-down removal. Use for the loaner rig's interlaced
output; without it the pulldown detector eats alternating fields and the reel
arrives stuttering. Costs about 4% throughput. If a reel stutters and its
sidecar says the loaner rig touched it, this flag was forgotten.

## --frame-budget N

Soft cap on frames per cohort, default 250000. The hose closes the cohort
cleanly at the cap rather than tearing a GOP to hit an exact count, so actual
cohort sizes land a little above the cap — within one GOP, typically under 120
frames over. Set it explicitly for benchmark freezes; the February freeze used
`--frame-budget 250000` and landed cohorts between 250,003 and 250,096 frames.

## --motion-prior-only

Passes a hint downstream to skip appearance scoring at association. Irrelevant
unless the tracker's pinned values have been changed, since appearance is off
by default since the February rewrite — but on the histogram-era archive reels
it is the difference between a 4-minute and an 11-minute pass.

## Examples

    hose capture --cage A --deinterlace-safe --frame-budget 250000
    hose regrade --reel REEL-A-20260302-014 --motion-prior-only

Full flag list lives in the hose's man page. This sheet exists because those
three are the ones we type from memory at 03:00, and memory is where the
spelling mistakes live.
