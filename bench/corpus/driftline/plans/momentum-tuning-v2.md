# Momentum tuning — pass 2

Owner: Tomás Iriarte. Date: 2026-01-15. Second pass; see plans/momentum-tuning-v1.md for the first round and its method. Same goal, same instrument, new data (kiln build playtests, December).

## Goal

Take the pass-1 state of specs/momentum-model.md and adjust the six live numbers until the quarry route and the kiln shaft are fun without any level-side crutches. This pass changes numbers only; structure changes are out of scope by agreement at the review.

## The numbers

| Knob | Pass 1 | Pass 2 |
|---|---|---|
| Ground acceleration | 42 u/s² | **38 u/s²** |
| Ground maximum | 480 u/s | **480 u/s (unchanged)** |
| Friction | 260 u/s² | **240 u/s²** |
| Air steer | 35% of grounded | **30%** |
| Boost pad impulse | +180 u/s | **+160 u/s, plus a 0.4 s surge** |
| Landing velocity keep | 60% | **55%** |

## Why these moved

Pass 1 fixed the landing interaction and the teaching; the December kiln playtests then showed the residual problem was *drift at the top end*: at 480 u/s the fox carried more speed through corners than testers could read, and 7 of 8 testers overshot the kiln's first tile turn at least once. Acceleration down (42→38) makes mid-range corrections effective sooner; friction down (260→240) keeps the low end from feeling punished by the same change. Air steer down (35→30) is the commitment knob — with ground correction cheaper, air authority can drop without the game feeling unfair. Boost impulse down to +160 but followed by a 0.4 s surge (drag-free, +40 u/s ramp) keeps peak pad speeds identical while making pads feel like a wave instead of a slap.

## What this pass changes instead (carried rules)

1. **Landing friction spike**: unchanged from pass 1 — 1.5× friction for 120 ms unless the stick is fully committed (magnitude ≥ 0.9).
2. **Damper crates per early route**: unchanged from pass 1 — 7 across quarry nodes 1–9.
3. **Boost pad placement pass**: unchanged from pass 1, plus one new rule — pads within 300 u of a kiln tile turn are illegal; two qualify today.

## What this pass adds

**Ramp launch compensation**: launches off concave ramps keep 80% of tangent speed instead of falling through the normal slope rules. Without it, the new friction number made ramp exits feel hollow in the kiln shaft.

## Method

Sweep each change independently against the December recordings (8 testers, 33 completions) before combining: a change ships only if it moves the overshoot count without moving completion times by more than ±4%. Same instrument, same population as pass 1 where the testers overlapped (5 of the 12 returned).

## Checkpoint

Re-review at the next milestone with the same complaint instrument. Pass 1's trigger ("at least halve the complaint count") was met; pass 2's trigger is the kiln overshoot count, same halving bar. If pass 2 misses, the six core knobs come back on the table with fresh eyes.
