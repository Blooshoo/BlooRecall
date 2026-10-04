# Intake checklist — capture cage B

Issued 2025-10-27 by Bram Oosterhuis. Cage B: 8 rigs at 120 fps, reels of
roughly 75,000 frames. Follow in order; do not skip the pre-shift.

## Pre-shift

1. Verify all 8 rigs clock-locked; skew ledger shows green for every rig.
2. Confirm spool-b free space at or above 1.1 TB.
3. Flash board charged; spare battery in the cage B cabinet.
4. LED panels warmed 10 minutes before the first clap.

## Reel open

5. Name the reel REEL-B-YYYYMMDD-nNN, zero-padded, never reused.
6. Sidecar filled: fps 120, rig roster, cage id, operator initials.
7. First clap recorded on all 8 rigs before the first take of substance.

## Mid-shift

8. Intake and emitted counters reconciled at every shift boundary.
9. Spool watermark checked hourly; above 0.90, pause capture rather than let
   the hose shed GOPs.
10. Any rig flagged in the skew ledger is pulled from the roster, not worked
    around.

## Reel close

11. Digest written and verified against the sidecar.
12. Cohort closed on the hose; tracker queue depth checked and noted.
13. Ledger entry: reel id, frame count, anomalies, initials.

## Notes

Cage B exists for long-duration work: at 120 fps its spool holds twice the
wall-clock time of cage A's. The lower frame rate means crossing judgments
are coarser here; anything that needs half-frame precision moves to cage A.
Changes to rig count or frame rate are a new protocol revision, not an edit
to this one.
