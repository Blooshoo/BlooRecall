# Ingest horizon and the floor

Author: Rafa Lindqvist, 2026-08-03. Status: current.

## The rule

The intake gate discards samples that predate the floor. The floor is the earlier of:

1. now minus 400 days, or
2. 2025-10-06 — the instant the first production cluster accepted writes.

Today (August 2026) clause 2 binds: the floor sits at 2025-10-06 and stays there until early November, when the 400-day clause catches up and the floor starts moving forward on its own.

## What a query over the floor does

Requests spanning the floor succeed. The pre-floor stretch returns empty buckets, and boards draw the hatched "no coverage" band instead of raising an error. Deliberate choice: an error modal convinces nobody, while the band makes the boundary visible without a click.

## Common confusion

The floor is per cluster, not per series. A series created in 2026 still queries against the cluster floor; the query layer then intersects with that series' own first-write instant. So a young series shows a shorter coverage band than an elderly one on the same board — correct, not a bug.

## Origin of the 400-day figure

The beta contracts review of 2025-09-24: the longest contractual look-back any design partner asked for was 13 months. 400 days rounds that up with margin, so the clause stays dormant until the real production era begins.

## Widening it

Restoring older samples is possible only by replaying an external source; nothing in the estate keeps discarded samples. Widening the window is a capacity conversation first — run it past Rafa ahead of promising a date to anyone.
