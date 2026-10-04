# Checkpoint policy — v1

Owner: Dev Okonkwo, with Tomás Iriarte. Date: 2025-12-15. Status: shipped in 0.11.0–0.13.0. See the v2 plan for the current policy; this file is the history of the first one.

## Spacing

A checkpoint every **~45 seconds of expected path**. "Expected path" means the route time recorded in the level notes, not a timer in the game — the game places checkpoints where the *design* says the player will be 45 seconds in, and Dev owns that judgment per node.

## What a checkpoint stores

A **full state snapshot**: pose, velocity, charge, every active timer, the full set of world-entity deltas since world entry, and the RNG stream position. Everything needed to reconstruct the exact moment, with no dependence on how the player got there.

This was chosen for simplicity: reconstruction is trivially correct, and at 45 s spacing nobody minded a 200 ms save hitch (measured 180–240 ms on the reference box).

## Placement rules (v1)

1. Never inside a momentum sequence — a checkpoint that interrupts a run teaches players to fear checkpoints.
2. Always on trusted, flat, non-sloped ground (the ground rules in specs/momentum-model.md, not cling walls).
3. After every teach: a node that introduces a mechanic gets a checkpoint before the first *test* of that mechanic.
4. Manual saves are not a thing in v1 — checkpoints are the save system, full stop.

## Respawn behavior (v1)

Respawn restores the full snapshot and **zeroes velocity**. The player restarts the segment from a standstill. This was deliberate: at 45 s spacing, segments are short, and a standstill start gives the player a breath and a chance to look around.

## Known wart, noted at the time

The standstill start is wrong for the kiln: restarting a vertical descent segment from zero speed means the first 8 seconds of every retry are the player rebuilding momentum they had already earned. Flagged for the next pass; the kiln blockout was young when this was written.
