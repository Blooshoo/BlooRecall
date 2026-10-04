# Particle and ribbon shader notes

Author: Marisol Vega. Date: 2026-02-27. Status: current as of 0.13.0.

Working notes on the particle pass shaders, written down after the sparkline seam incident so the next person does not re-derive them. The feature-side rules (emission rates, LOD, the charge gate) live in specs/sparkline-trails.md; this file is the GPU side.

## Ribbon vertex layout

Each ribbon segment is a quad with a per-vertex **age attribute** (0 at the head, 1 at the tail) and a per-vertex **lateral coordinate** (-1/+1 across the width). Width, alpha, and color all derive from age in the shader:

- width = mix(14, 2, age) px, evaluated in screen space then divided by the scale factor so world zoom keeps the ribbon readable;
- alpha = (1 - age)^1.4 — the 1.4 exponent keeps the tail visible longer than a linear fade without brightening the head;
- color = 64×1 LUT sampled at age (the ember ramp, three stops baked at build time).

## The seam incident

The first ribbon shader drew segments as independent quads and the joints showed: at speed, the ribbon looked beaded, like a string of pearls, because consecutive quads didn't overlap and the additive blend exposed a one-pixel gap at every joint. The fix is boring and stays: each segment is extended by **1 px of overlap** at both ends, and the overlap region writes alpha at 50% so the double-draw doesn't brighten the joint. The pearls are gone; the overlap costs nothing measurable.

## Additive banding

Additive blending on dark scenes banded hard on the laptop tier's lower-precision backbuffer. Fix: a **1/255 ordered dither** applied to the ribbon output only, pattern rotated per frame. On the reference box the dither is invisible; on the laptop tier it converts the banding into noise the eye tolerates. Do not remove this "because it looks dirty in screenshots" — screenshots are taken on the reference box where the dither does nothing.

## The charge gate uniform

The charge gate (70%, smoothed) is passed as a scalar uniform and the shader draws nothing when it is below threshold — the CPU also skips the draw, so the uniform is belt-and-suspenders for replay playback, where the smoothed charge is reconstructed from the input echo and can momentarily disagree with the CPU-side decision during a seek. During a seek the uniform is authoritative; this is deliberate and not up for "simplification".

## Rebuild vs. record

Sparkline ribbons are **never stored** in captures. The replay re-simulates and re-emits them from the input echo; only gameplay state is snapshotted (see specs/quick-capture-architecture.md for why). Consequence: the shader must be deterministic given (snapshot state, inputs, time) — no per-particle randomness outside the seeded hash. The hash seed is folded into the capture's build tag field, which is one reason that field is not optional.
