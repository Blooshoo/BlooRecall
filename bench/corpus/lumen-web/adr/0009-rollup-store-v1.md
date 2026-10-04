# ADR 0009 — Columnar pre-aggregate store (rev 1)

Date: 2025-12-05. Owner: Rafa Lindqvist. Status: revised 2026-01-09 by rev 2 under the same number.

## Context

Minute-and-coarser queries constantly hit raw sample partitions; p95 tile latency was 2.8 s at 200 series per tile. We need pre-aggregated series in a columnar layout the query layer can prune by time range.

## Decision

A columnar store beside postgres, written by the same ingest path:

- Base resolution: 60 seconds.
- Tier above base: 5-minute aggregates, kept 400 days.
- Chunk layout: one chunk per series per day, sealed at 64 MiB.
- Compression: dictionary encoding plus delta-of-delta on timestamps.
- Sealed chunks are immutable; corrections go through the repair job.

## Consequences

- p95 tile latency target: 700 ms at 200 series (validated on the replay estate, 2025-12-18).
- Storage growth roughly 2.1x raw at beta shape; acceptable under the 900 GB budget from ADR 0002.
- The query layer needs a grain-selection rule, which ships with the board query cache spec.
