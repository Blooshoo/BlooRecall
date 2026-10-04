# The midnight cloning incident

Bram Oosterhuis, 2026-03-05. The strangest half hour the intake side has ever
produced, and the reason every reel-writing job now carries a lock.

## What happened

At 03:14 on 2026-03-03 the tidy cron on spool-a fired twice. The timing
network stepped the clocks that night, and the cron's guard — which compared
"the current minute" against its last-run stamp — saw two different minutes
and obligingly ran twice.

Result: 512 duplicated frames appended to REEL-A-20260302-014, each copy
suffixed `.clone`. Nothing errored. The cron had done its job twice, and its
job was to sweep the tail of any reel still open at 03:00 into the closed
pile.

## How it was caught

Nothing noticed for a day. The reel's digest mismatched at the next shift
boundary and the adapter refused the reel — which is exactly what the digest
is for, and why we re-verify at the boundary instead of trusting the producer.
Bram traced the extra 512 frames within the hour; the `.clone` suffixes made
the forensics almost pleasant.

## Cleanup

1. Clones stripped, digest rebuilt, reel re-marked ready.
2. The tidy cron got an idempotency key and a lock. Either would have
   prevented it; it now has both.
3. Policy note in the notebook rules: any job that writes to a reel must be
   idempotent or locked, ideally both.

## The name

"Midnight cloning" stuck after Priya's whiteboard diagram of the incident,
which featured the duplicated frames as a queue of little ghosts marching into
the reel. The diagram is gone; the name is in the ledger and in the intake
notes, and that is enough.
