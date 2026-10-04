# Plan: herd-store schema v2 migration

- Owner: Priya Raghunathan
- Date: 2026-05-04
- Status: shipped in taskherd 2.7.1 (patch, 2026-05-11)

## What changes

The on-device store (the "herd store") moves from schema v1 to v2. Two additions drive it:

- The **recovery_shelf** table, which backs the Recovered items section that conflict resolution v2 introduced (`specs/offline-conflicts-v2.md`).
- The **conflict_log** table, which records every resolution with both edit hashes so support can answer "where did my text go" with evidence instead of sympathy.

Schema v1 remains readable forever in the sense that matters operationally: a device that never upgrades keeps working against v2-protocol servers, because the wire protocol and the local schema are independent (the protocol cutover in April deliberately landed first).

## The migration function

`migrateHerdSchema()` runs on first launch of the patch build, in three steps:

1. **Begin lease.** A 20-second local lease guards against a second migration attempt from a re-entrant launch (fast app switch during the run).
2. **Convert in batches.** Tables convert in batches of 5,000 rows per transaction, ordered smallest-first so the interactive tables (boards, tasks) finish early and the UI unblocks while change feeds convert in the background.
3. **Commit and flip.** A single marker row records the schema version; on crash, the marker is absent and the whole run repeats from scratch. Batch conversion is idempotent by design, so a repeat run over partially converted tables converges.

## Performance on the test fleet

Measured on the 412-device dogfood fleet (2026-04-27 to 2026-05-02):

- p50 migration time: 2.4 seconds (median store size, 6,400 rows).
- p95: 11 seconds (large store, 120,000+ rows, older devices).
- Worst observed: 38 seconds on a 400,000-row store from a power user who has been with us since 1.x; the UI stayed interactive throughout because of the smallest-first ordering.

## Failure path

If `migrateHerdSchema()` cannot complete (disk pressure, corrupted page), the client falls back to a wipe-and-resync: the local store is discarded and rebuilt from the server, since the server is authoritative for everything except quarantined reconciliation entries (which, per the cutover plan, are backed by the server-side quarantine tool). Wipe-and-resync triggered 3 times in 412 dogfood devices, all on one device with a failing flash chip.

## Rollout

Staged with the patch train: 5% on 2026-05-11, 50% on 2026-05-13, 100% by 2026-05-18. The scale review that week (`meetings/2026-05-18-scale-review.md`) confirmed p95 migration time in production matched the test fleet within 8%. Support saw 31 tickets total, 28 of them "why is my first launch slower" — answered with the first-launch macro.

## Sequencing note

This migration deliberately follows the April protocol cutover by a month. Running both on one device in one release would have made rollback analysis impossible: a fault after a double upgrade could not be attributed to protocol or schema. One change per train, per the team's standing rule since the October 2025 incident.
