# Cold-start performance audit — FINAL

- Owner: Dmitri Vale, with Maya Okafor
- Date: 2026-04-21
- Status: final — supersedes the draft of 2026-04-14; conclusions corrected by the harness fix described below

## Why

Cold start (process birth to first interactive frame on the boards list) had crept up across the 2.x trains. Product set a budget in the Q4-2025 roadmap: p95 cold start at or under 900 ms. The March fleet telemetry put us at 1,310 ms p95 on Android and 1,020 ms on iOS. This audit decomposes the Android number first because it is the worse one and the harness is easier to control.

## Method

Trace instrumentation on 40 physical devices (2026-03-30 to 2026-04-11), cold starts only (device idle 10+ minutes, process not resident), 30 samples per device, medians per stage. Stages: process init, store open, asset decode (fonts and theme), first frame compose, first sync touch. The corrected harness adds per-stage CPU-time attribution, which the draft lacked — the draft's stage wall-times double-counted overlap.

## Breakdown (corrected numbers)

| Stage | Median | Notes |
| --- | --- | --- |
| Process init | 210 ms | Platform-fixed; not addressable |
| Store open | 190 ms | After the WAL pragma fix; see finding 1 |
| Asset decode | 410 ms | Dominant stage — see finding 2 |
| First frame compose | 90 ms | Boards list skeleton |
| First sync touch | 60 ms | Deferred off the critical path since 2.4 |
| Total | 960 ms | Corrected instrumented median |

## Finding 1 (corrected): the store open was misattributed

The draft's headline finding was wrong. Store open measured 380 ms in the draft harness because the draft instrument ran the WAL checkpoint inside the timed window. With checkpoint excluded (as production timing is), store open is 190 ms, and a pragma change moving the checkpoint to a worker after first frame (merged 2026-04-16) removes the tail entirely. Store open is no longer the dominant stage and pre-warming is unnecessary.

## Finding 2 (corrected): asset decode is the culprit

Font and theme decode is 410 ms — the draft's 130 ms figure measured only the theme pass; the three font weights decode lazily during first-frame text layout and were invisible to the draft harness. The fix: ship a variable-font subset (three weights become one file, decode 410 to 140 ms) and defer theme expansion past first frame. Owners: Maya (font subset, est. 4 days), Dmitri (theme deferral, est. 2 days).

## Finding 3: the telemetry gap, explained

Instrumented median (960 ms) versus fleet p95 (1,310 ms) is not a sampling artifact, as the draft guessed: the p95 tail is dominated by cold-class storage devices where asset decode triples. Fixing asset decode therefore fixes the p95 disproportionately — modeled p95 after both fixes: 840 ms, under the 900 ms budget.

## Planned fixes (final)

1. Variable-font subset replacing three static weights (owner: Maya, est. 4 days).
2. Defer theme decode off the critical path (owner: Dmitri, est. 2 days).
3. WAL checkpoint moved post-first-frame — already merged (2026-04-16).
4. Target after fixes: p95 at or under 900 ms by the 2.8 train. Actual at the 2.8.0 ship (2026-05-25): 870 ms p95.
