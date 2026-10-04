# Cold-start performance audit — DRAFT

- Owner: Dmitri Vale, with Maya Okafor
- Date: 2026-04-14
- Status: draft — instrumentation pass; conclusions pending the corrected harness (see final)

## Why

Cold start (process birth to first interactive frame on the boards list) had crept up across the 2.x trains. Product set a budget in the Q4-2025 roadmap: p95 cold start at or under 900 ms. The March fleet telemetry put us at 1,310 ms p95 on Android and 1,020 ms on iOS. This audit decomposes the Android number first because it is the worse one and the harness is easier to control.

## Method

Trace instrumentation on 40 physical devices (2026-03-30 to 2026-04-11), cold starts only (device idle 10+ minutes, process not resident), 30 samples per device, medians per stage. Stages: process init, store open, asset decode (fonts and theme), first frame compose, first sync touch.

## Breakdown (draft numbers)

| Stage | Median | Notes |
| --- | --- | --- |
| Process init | 210 ms | Platform-fixed; not addressable |
| Store open | 380 ms | Dominant stage — see finding 1 |
| Asset decode | 130 ms | Theme + three font weights |
| First frame compose | 90 ms | Boards list skeleton |
| First sync touch | 60 ms | Deferred off the critical path since 2.4 |
| Total | 870 ms | Instrumented median (telemetry says 1,310 p95 — gap discussed below) |

## Finding 1 (draft): the store open is the culprit

Store open at 380 ms is the single largest addressable stage. The draft conclusion: the synchronous open on the main thread — opening the database, replaying the change-feed high-water mark, and validating the queue index — is the dominant cost, and the fix is to pre-warm the connection during process init on a worker thread, overlapping it with process init's 210 ms.

## Finding 2: the telemetry gap

Instrumented median (870 ms) versus fleet p95 (1,310 ms) differs mostly because p95 includes cold-class storage and low-RAM devices excluded from the physical test set. The draft treats the gap as sampling artifact; the corrected harness in the final audit revisits this.

## Planned fixes (draft)

1. Pre-warm the store connection during process init (owner: Dmitri, est. 3 days).
2. Defer theme decode off the critical path (owner: Maya, est. 2 days).
3. Target after fixes: p95 at or under 900 ms by the 2.8 train.
