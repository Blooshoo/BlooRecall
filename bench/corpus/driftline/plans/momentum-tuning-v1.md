# Momentum tuning — pass 1

Owner: Tomás Iriarte. Date: 2025-11-05. Follows the 2025-11-03 momentum review; folds in the review's data and complaints.

## Goal

Take the 0.9.0 baseline from specs/momentum-model.md and adjust the six live numbers until the quarry route is fun without any level-side crutches. This pass changes numbers only; structure changes are out of scope by agreement at the review.

## The numbers

| Knob | 0.9.0 baseline | Pass 1 |
|---|---|---|
| Ground acceleration | 42 u/s² | **42 u/s² (unchanged)** |
| Ground maximum | 480 u/s | **480 u/s (unchanged)** |
| Friction | 260 u/s² | **260 u/s² (unchanged)** |
| Air steer | 35% of grounded | **35% (unchanged)** |
| Boost pad impulse | +180 u/s | **+180 u/s (unchanged)** |
| Landing velocity keep | 60% | **60% (unchanged)** |

## Why nothing changed

The review's data did not support touching the six core knobs: 12 testers produced 41 route completions, and the complaints ("too slippery on small landings", 9 of 12) all traced to two things this plan *does* change (below) rather than to the core numbers. The lesson we agreed on: fix the landing interaction and the teaching before touching the engine of the whole game.

## What this pass changes instead

1. **Landing friction spike**: on landing, apply 1.5× friction for 120 ms unless the stick is fully committed (magnitude ≥ 0.9). This is the fix for "too slippery on small landings" — small hops were keeping 60% of a velocity the player had already abandoned.
2. **Damper crates per early route**: Dev raises the count from 4 to 7 across quarry nodes 1–9, so the "landing costs speed" lesson is taught before it is tested.
3. **Boost pad placement pass**: pads that fight friction (within 300 u of a damper crate) get moved; three qualify today.

## Method

Sweep each change independently against the recorded 41 completions before combining: a change ships only if it moves the "slippery landing" complaint count without moving completion times by more than ±4%. The review's baseline recordings are the control; no re-recruiting, no new testers for this pass.

## Checkpoint

Re-review at the next milestone with the same complaint instrument. If the complaint count has not at least halved, the six core knobs come back on the table with fresh eyes — that is the trigger, written down now so January-us can't dodge it.
