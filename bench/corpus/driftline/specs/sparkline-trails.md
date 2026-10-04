# Sparkline trails

Author: Marisol Vega. Date: 2026-02-25. Status: shipped in 0.13.0. Tuned again in the June budget pass (see specs/rendering-pipeline.md).

## What a sparkline is

A **sparkline** is the ribbon of spark particles that trails behind Ember while charge is at or above 70%. It is a *gameplay-readable* effect first: at full speed the ribbon is long and bright, and its length is one of the ways players read their own momentum without looking at any meter. (Naming note for future archaeology: in this codebase "sparkline" means the particle trail and nothing else. Do not confuse it with tiny chart graphics; we have no charts.)

## Emission and shape

- Emission rate: **90 Hz**, config key `trail_emit_hz`.
- The ribbon is built from **180 segments** at full detail; each segment is a quad stretched between consecutive emission points, width falling from **14 px to 2 px** along the age of the segment.
- Segment count is the LOD dial: when more than **2 concurrent sparklines** are active (co-op ghost runs, attract mode), each drops to 60 segments before anything else sheds detail.
- Blend is additive. The color ramp is the ember palette (three stops: pale gold at the head, orange mid, deep red at the tail) sampled from a 64×1 LUT — see reference/particle-shader-notes.md for the shader-side details and the seam fix.

## Charge gate

The gate at 70% charge is a gameplay decision owned by Tomás: below the gate the ribbon would visually promise speed the player doesn't have. The gate uses the *smoothed* charge (200 ms EMA), not raw charge, so the ribbon doesn't flicker on landing.

## Guards

When the emitter pool is exhausted, the allocator raises `ERR_SPK_OVERFLOW_118` and refuses *new* emitters rather than shrinking active ones mid-trail — a sparkline that collapses halfway through a jump reads as a bug even to testers who don't know what a sparkline is. In practice the pool is sized so the guard only fires in the attract-mode stress scene, which deliberately spawns 12 concurrent trails.

## Budget interaction

A single full-detail sparkline costs roughly 0.9 ms per delivered frame on the reference box (simulation + draw, measured June 2026). Two concurrent full-detail ribbons plus the kiln's vent emitters is the load case the budget doc is written around. If a future feature wants more than the LOD rules allow, it needs to take budget from somewhere explicit — the guard is there to force that conversation, not to silently degrade the look.
