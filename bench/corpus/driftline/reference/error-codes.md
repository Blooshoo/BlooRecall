# Engine error codes (ERR_RIDGE family)

Author: Marisol Vega. Date: 2026-02-16. Scope: the Ridgeline engine core family only. Feature-module codes live with their features (the capture module's truncation code is in specs/replay-format.md, the particle guard is in specs/sparkline-trails.md, the momentum guard is in specs/momentum-model.md) — this file is the engine's own, and it does not duplicate them.

## Policy

- Codes are four digits after the family prefix, assigned once, never reused. Retired codes stay in the table marked retired, because a stale log line should still resolve.
- Engine errors are *conditions*, not failures: most are recoverable and the engine state after handling is documented per code. A code that means "crash" should be an assert, not a code.
- Every code below has an owner. If a code fires and you don't know why, the owner is who you ask first.

## The table

| Code | Meaning | Recovery | Owner |
|---|---|---|---|
| `ERR_RIDGE_037` | Atlas page miss at draw time — a batch referenced a page the service had evicted despite the pin/resident rules | The draw is skipped for that page this frame; the overlay logs the page key. Means the admission rules were lied to somewhere upstream | Marisol |
| `ERR_RIDGE_112` | Batch vertex overflow — more than 8,192 quads pushed through `rpush_sprite_batch` in one batch | Batch is split automatically; the split point is logged. Frequent fires mean a layer needs re-banding, not a higher cap | Marisol |
| `ERR_RIDGE_209` | Shader permutation watchdog — a permutation took over 400 ms to compile on the render thread | Compile is deferred to the admission queue; the affected draw uses the fallback permutation this frame. A fire during the opening route means the prewarm list missed it (see specs/cold-start.md) | Marisol |
| `ERR_RIDGE_231` | Timeline underrun — the simulation ran long enough that presentation slipped a frame | Nothing to recover; the frame is late. Investigate if it repeats within a route run | Tomás |

## Retired

| Code | Was | Retired because |
|---|---|---|
| `ERR_RIDGE_055` | Legacy sound-bank stream stall (pre-0.9 audio path) | Audio path rebuilt in 0.11; stalls are handled in-stream now |

## Notes

- `ERR_RIDGE_037` has fired exactly once in shipped builds (2026-03-14 nightly, during a world transition with a hand-edited pin list). The pin list format got a validator out of that fire; the code stays.
- Do not add a code "in case". A code without an owner and a recovery story is noise. Priya rejects them at review and she is right to.
