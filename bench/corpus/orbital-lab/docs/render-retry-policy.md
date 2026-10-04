# Decision: the farm retry ceiling

Date: 2026-05-14. Owner: Marco Deluca. Ratified at the May farm review (see
meetings/2026-05-14-render-review.md).

## Decision

For the render re-encode pipeline, `retry_policy.max_attempts` is 2.

On a stall-class or spool-class failure the fragment goes straight back onto
the queue — immediate requeue, zero delay, no backoff. A fragment that fails a
second time is parked in the quarantine bin for morning triage instead of
cycling forever.

## Scope, stated plainly

This key belongs to the render pipeline and only to the render pipeline. The
intake hose has its own, different retry behavior — three attempts with a
30-second pause, Bram's domain — and we explicitly chose not to unify them.
The key name collides across pipelines; the scope line in the configuration
reference is what disambiguates. Anyone grepping the config for this key must
check which subsystem's block they are reading.

## Why two, why immediate

The May quarantine bin held 9 fragments the previous week, all stall-class,
all of which rendered clean on their second pass. So: one retry recovers
nearly everything that will ever recover. A third attempt never once helped
in the April sample, and backoff between attempts costs the farm its tail
latency guarantee for no measured benefit — stall-class failures are not
load-shaped, they are compaction collisions and hungry caches, and both clear
in seconds or not at all.

## What does not count as an attempt

QC gate failures are not retries; a QC fail routes through the QC protocol's
adjudication lane. Ladder deviations (one rung up on texture loss) are not
retries either. The counter counts scheduler-level attempts, nothing else.

## Review

Re-examine if the stall profile changes — the February census numbers are the
baseline. Until then the ceiling stands.
