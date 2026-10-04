# ADR 0011 — Streaming export worker

Date: 2026-01-22. Owner: Rafa Lindqvist. Status: current. Replaces adr/0004 (2025-10-08).

## Context

The nightly batch worker (adr/0004) made archives one day stale, and one poisoned board could starve a 300-board estate for the whole six-hour window. The December audit showed 11 boards failing five or more nights in a row with no signal.

## Decision

Exports become per-request. Any board renders on demand to a zip archive (PNG tiles plus one CSV per tile) with a 90-second readiness target for boards under 200 tiles. A queue with per-board fairness replaces the single nightly job; failures retry with backoff within minutes, not days.

## Consequences

- The nightly 02:30 UTC job retires in v4.0.0.
- Two render nodes instead of one; measured peak load since GA is 0.4 nodes.
- The December failure mode — silent multi-night starvation — is structurally gone: anything older than 10 minutes in queue pages the data tier.
- The 90-second readiness target holds up to 200 tiles; beyond that the UI quotes an honest estimate instead.
