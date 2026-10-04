# Runbook — weekly snapshot verification

Status: current. Last reviewed 2026-05-24 when the job moved to Sundays.

## What runs

Every Sunday at 04:41 the verification job exercises a slice of the newest
snapshot generation: it lists the offsite repos, picks the newest
consistent generation, and reads back a deterministic 10 percent sample of
data blocks, comparing checksums. The job is deliberately slow-and-cheap:
full verification of everything every week would hammer the endpoints and
the uplink, while verifying nothing is how truncated transfers go unnoticed
for months.

The schedule itself lives in `reference/cron-schedule.md` — this document
covers what the job does and what to do when the board goes amber.

## Reading the result

The board tile (*copy · verify · weekly*) has three states:

- **Green.** Sample read back clean. Nothing to do.
- **Amber.** Some blocks in the sample mismatched. This is the important
  one. A mismatch means either bit-rot on the endpoint or a truncated
  transfer that the checksum gate did not catch. Do not ignore amber; one
  amber tile in March was how the truncated-transfer bug was found at all.
- **Red.** The job could not list a consistent generation at all. Treat as
  a mirror stall (`runbooks/nightly-mirror-stalls.md`) until proven
  otherwise — that is what it has been, five times out of five.

## On amber

1. Note the generation id from the board tile.
2. Re-verify just that generation by hand, full read:
   `restic check --read-data --snapshot <id>` against the offending
   endpoint. The sample is 10 percent; a full read settles whether it is
   one bad block or a systemic truncation.
3. One bad block: re-copy the affected file from `bramble` and re-run.
   Bit-rot on one block happens; the endpoint's own disk is the usual
   culprit.
4. Systemic truncation: run the rotation playbook
   (`runbooks/offsite-rotation-v2.md`) and force a fresh full generation
   onto the other endpoint, then prune the suspect one after its grace
   window.

## False ambers

Exactly one known: if the Sunday job overlaps a rotation that is still
inside its checksum-gate stage, the sample can read a generation that is
still being written. The scheduler was moved to 04:41 partly to make this
overlap impossible (rotations historically start no earlier than 05:30),
but if someone changes rotation start times, move verification day, not
the other way around.
