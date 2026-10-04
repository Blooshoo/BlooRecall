# exp-032 — stall storms on renderlet-09

Date opened: 2026-02-05. Owner: Marco Deluca. Status: concluded 2026-02-09.

## Symptom

The hardware encoder on a farm node occasionally stops returning pictures
mid-fragment. From the scheduler's side this is silence: no completion
interrupt, no error, just a fragment that should have finished and did not.
Threshold for calling it a stall: silence greater than 1200 ms where normal
fragment completion is 380–610 ms.

We registered the farm's first dedicated stall code, `ERR_ENCODER_STALL_118`,
in the week's ledger note before writing any of this down.

## Census

17 events in the week of 2026-02-02, every one of them on renderlet-09. Mean
silence 2.3 s, longest 11.4 s. No correlation with fragment size, ladder rung,
or time of night. Strong correlation with spool-a crossing the 0.95 watermark:
12 of 17 events began within 90 s of compaction starting on a nearly full
spool. The encoder's read stream starves while the spool compacts.

## Fixes

1. Compaction moved off the shift window — it now runs immediately after the
   ledger roll, when the queue is shallowest.
2. Watermark alarm added at 0.95 so the operator sees the condition before the
   encoder does.
3. renderlet-09's read cache bumped from 64 MB to 256 MB.

Events after the fix: 0 across 14 consecutive shifts.

## Interface note

The stall code is what the node emits; what the scheduler does about it is
policy, not code. The retry ceiling for stall-class failures (two attempts,
immediate requeue) is recorded separately in `docs/render-retry-policy.md`.
Code and policy are deliberately kept apart so either can change without the
other.
