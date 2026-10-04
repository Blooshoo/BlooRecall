# ADR 0002 — Store metrics in postgres with partitioned tables

Date: 2025-09-20. Owner: Rafa Lindqvist. Status: accepted.

## Context

At beta scale — roughly 40 boards and a peak of 90 writes per second — running a dedicated time-series database is operationally heavy for a four-person team. We still need range scans and downsampling that do not fall over.

## Options

1. Dedicated TSDB. Best compression and ingest, but one more system to run, back up, and upgrade.
2. postgres with monthly partitions on sample time, plus the columnar extension for the downsampled tiers. Known tooling, backups we already trust, good-enough compression.
3. Flat files on a single node. Cheapest, weakest query story, no concurrent readers.

## Decision

Option 2. Raw samples live in monthly partitions; anything older than 60 days is downsampled to minute grain and dropped from raw. The downsampled tiers move to the columnar store later (adr/0009).

## Consequences

- Revisit triggers, agreed 2025-09-18 from the beta capacity model: sustained ingest above 8,000 writes per second, or raw storage crossing 900 GB.
- The 60-day raw window satisfies every design partner contract reviewed on 2025-09-24.
