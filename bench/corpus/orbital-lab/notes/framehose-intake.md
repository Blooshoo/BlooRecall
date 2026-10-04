# The hose: intake notes

Bram Oosterhuis, opened 2025-10-14. Living notes on the intake side of the
pipeline. Amended as things change; the amend history is at the bottom.

## Ingestion

### Backpressure

When the scratch ring crosses 0.90 of capacity the hose pinches its own valve:
whole GOPs are shed rather than tearing one mid-stream. Shedding inside a GOP
corrupts the reel around the cut; shedding the entire GOP leaves a clean,
countable hole that the boundary reconciliation catches. December's tally: 41
shed GOPs across the month, every one during a spool compaction collision —
which is why compaction moved off the shift window in February.

### Handoff to tracking

When a cohort closes, the hose writes its sidecar and pushes the reel onto the
tracker's queue. Frames are never moved twice: the tracker reads from the ring
in place, and only the ledger entries travel. The queue is depth-monitored and
the depth appears on the wall board next to the spool watermarks.

### Integrity

Every cohort carries a digest in its sidecar, and the adapter re-verifies the
digest at the boundary before the reel is marked ready. We re-verify rather
than trust the producer because of the March duplication incident: the tidy
cron cloned a reel's tail at 03:14 and the digest mismatch was the only thing
that caught it. Trust, but timestamp.

## Amend history

- 2025-10-14 — opened with the valve and queue notes.
- 2026-02-06 — compaction moved off shift window; valve note updated.
- 2026-03-06 — digest section added after the cloning incident.
