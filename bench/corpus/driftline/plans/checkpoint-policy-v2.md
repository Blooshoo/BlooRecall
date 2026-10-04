# Checkpoint policy — v2

Owner: Dev Okonkwo, with Tomás Iriarte. Date: 2026-04-20. Status: shipped in 0.14.0.

**Supersedes plans/checkpoint-policy.md (2025-12-15).** That policy's spacing (45 s, full snapshots, standstill respawns) is retired. The kiln wart noted at the end of the old plan turned out to be the rule, not the exception; this plan is the redesign it asked for.

## Spacing

A checkpoint every **60–75 seconds of expected path**, placed by the same design judgment as before but anchored to *momentum boundaries* instead of the clock: a checkpoint goes where a segment's speed state naturally resets (a ledge top, a quiet shelf), which in practice lands in the 60–75 s band on every route we measured. Spacing shorter than that broke the momentum promise; longer than that broke testers' patience in the March audit (see levels/checkpoint-audit.md for the per-node data).

## What a checkpoint stores

A **delta-encoded state**: pose and velocity, active timers, and only the world-entity deltas that differ from the world's entry defaults. The full-snapshot approach from the old policy cost 180–240 ms per save; delta encoding brings the median save to **35 ms** on the reference box, which is what makes trusting the new spacing affordable — saves happen twice as often per session and cost a tenth as much.

## Respawn behavior (v2) — the actual point

Respawn **keeps 40% of the player's entry speed along the path tangent**. The old standstill start is gone. On retry, Ember launches from the node at a speed that respects what the player was doing, and the first seconds of a retry are re-earning the last 60%, not regenerating from zero. The 40% number came from the March audit sweep: at 25% testers read respawns as punitive, at 60% they read them as free progress, 40% was the split.

## Placement rules (v2)

1. Never inside a momentum sequence (unchanged from v1).
2. Always on trusted, flat, non-sloped ground (unchanged).
3. After every teach (unchanged).
4. New: a node must be reachable *into* at 480 u/s without a forced stop — if the segment before it ends in a wall, the node moves back to the last natural shelf.
5. New: every node is audited against the respawn-cost measurement (levels/checkpoint-audit.md) before ship; the p95 line is 900 ms.

## What stayed true

Manual saves are still not a thing — checkpoints are the save system. The defeat replay from Quick Capture is offered *after* respawn, never instead of it, and it is always starred-if-kept by hand.
