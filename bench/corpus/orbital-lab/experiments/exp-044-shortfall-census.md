# exp-044 — the shortfall census

Dates: 2026-06-01 through 2026-06-07. Owner: Bram Oosterhuis. Status: concluded.

## Question

The hose intake counter says one number, the emitted ledger says another, and
the difference — we call it the shortfall — has never been reconciled tighter
than "small". Where do the frames go?

## Method

For one week we reconciled intake against emitted at every shift boundary
instead of at the daily roll. At each boundary Bram recorded intake total,
emitted total, and chased the difference before the next shift opened. The
point of chase-it-now is that the scratch ring still holds whatever never made
the ledger; after the daily roll it has been wiped.

## Numbers

Intake for the week: 14,203,552 frames. Emitted: 14,203,489. Shortfall: 63
frames, or 4.4 per million.

## Where they go

61 of the 63 turned up in the scratch ring, orphaned by the power dip at
02:11 on 2026-06-03: the intake and emitted counters split when the ring lost
power mid-flush, and the daily reconciliation had always absorbed this as
noise. The 61 were recovered, appended with `.orphan` suffixes, and verified
against the reel digests before being counted.

The remaining 2: traced to a hand-copy Priya made during the colormap test on
2026-06-05 — she pulled a debug window's worth of frames out to eyeball and
forgot a ledger entry. Filed as a notebook-policy reminder, not a hose defect.

## Verdict

1. Shift-boundary reconciliation becomes standard; the daily roll was hiding
   transients by design.
2. The hose now warns when the shortfall exceeds 5 per million in any single
   shift. It has stayed quiet since.
3. The census is cheap (about 15 boundary-chases all week) and repeats
   quarterly, next in 2026-09.
