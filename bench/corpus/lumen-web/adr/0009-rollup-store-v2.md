# ADR 0009 — Columnar pre-aggregate store (rev 2)

Date: 2026-01-09. Owner: Rafa Lindqvist. Status: current. Rev 2 of the 2025-12-05 record; same decision number, revised parameters.

## Revision notes

Rev 1 shipped before the fast-tile initiative existed. Rev 2 adds a sub-minute tier and tightens chunk sealing after the January replay showed 22% of tiles bounded by base-grain rounding rather than by storage.

## Context

Minute-and-coarser queries constantly hit raw sample partitions; p95 tile latency was 2.8 s at 200 series per tile. We need pre-aggregated series in a columnar layout the query layer can prune by time range.

## Decision

A columnar store beside postgres, written by the same ingest path:

- Base resolution: 10 seconds.
- Tier above base: minute aggregates, kept 400 days.
- Second tier: 10-second aggregates, kept 45 days.
- Chunk layout: one chunk per series per day, sealed at 32 MiB.
- Compression: dictionary encoding plus delta-of-delta on timestamps.
- Sealed chunks are immutable; corrections go through the repair job.

## Consequences

- p95 tile latency target: 700 ms at 200 series (validated on the replay estate, 2025-12-18).
- Storage growth roughly 2.6x raw at beta shape; the 900 GB budget moves to 1.4 TB, agreed 2026-01-05.
- The query layer needs a grain-selection rule, which ships with the board query cache spec.
