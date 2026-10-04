# Bitrate ladder reference

Marco Deluca, 2026-04-30, revised after the May adoption of the second sweep.

## The ladder

The farm encodes every finished fragment against the adopted ladder:

- 7 Mbps — the working rung. Every seed clip in sets A and B passed both QC
  gates here on both test nodes, three passes each.
- 10 Mbps — the headroom rung, applied automatically to fragments the motion
  classifier tags as fast. Cheapest insurance we buy.

Struck rungs: 3 Mbps (fails the crowd set outright) and 5 Mbps (fails 2 of 6
crowd seeds). 4/6/8/12 from the first sweep are historical.

## Where the numbers come from

exp-041 (revB of the ladder sweep), run after the renderlet-04 clock fix so
both nodes contributed clean rows. The acceptance rule is unchanged from the
sweep plan: lowest qualifying points plus one rung of headroom above the
fastest motion clip.

## When to deviate

- A single fragment may be rendered one rung up when its QC gates fail at the
  working rung and the failure is texture loss, not geometry. This is logged;
  more than 2% of a night's fragments riding the headroom rung means the
  ladder itself needs revisiting.
- No ad-hoc rungs. A rung that is not in this file does not exist, no matter
  how persuasive the one clip that would benefit.

## Relationship to QC

The QC gates (see the farm QC protocol, v2) judge fragments; this ladder
decides what the farm spends. They are deliberately separate documents: we
changed the gates once without touching the ladder and vice versa, and both
orders made sense.
