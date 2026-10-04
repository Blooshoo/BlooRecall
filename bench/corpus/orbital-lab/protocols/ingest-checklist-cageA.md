# Intake checklist — capture cage A

Issued 2025-10-20 by Bram Oosterhuis. Cage A: 12 rigs at 240 fps, reels of
roughly 150,000 frames. Follow in order; do not skip the pre-shift.

## Pre-shift

1. Verify all 12 rigs clock-locked; skew ledger shows green for every rig.
2. Confirm spool-a free space at or above 2.2 TB.
3. Flash board charged; spare battery in the cage A cabinet.
4. LED panels warmed 10 minutes before the first clap.

## Reel open

5. Name the reel REEL-A-YYYYMMDD-nNN, zero-padded, never reused.
6. Sidecar filled: fps 240, rig roster, cage id, operator initials.
7. First clap recorded on all 12 rigs before the first take of substance.

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

The 240 fps rig count is what makes cage A the reference cage: half-frame
judgments are possible here and nowhere else. Anything that changes the rig
count or the frame rate is a new protocol revision, not an edit to this one.
