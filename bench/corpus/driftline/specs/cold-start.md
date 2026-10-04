# Prewarm and resource admission

Author: Marisol Vega, with Rosa Lindqvist. Date: 2026-04-14. Status: experiment results from April; shipped in 0.15.0 (2026-06-15).

## The problem we measured

Before the prewarm pass, a cold run of the opening route (quarry nodes 1–6, festival intro pose set) showed a p95 tail of **2,800 ms** on the reference box, concentrated in the first 90 delivered frames. The cause was lazy admission: shader permutations, atlas pages, and audio banks were all admitted on first use, so the opening minutes of a fresh session paid every admission cost at once, in delivery order, with no staging.

## Admission order

The prewarm pass admits in a fixed order, because the costs are asymmetric:

1. **Shader permutations** first — the watchdog (see reference/error-codes.md, ERR_RIDGE_209) fires above 400 ms per permutation, and a fired watchdog during the opening frames is the single worst first impression we can make.
2. **Atlas pages for the first route** — the prewarm list per world from specs/fox-sprite-cache.md, admitted at a maximum of 2 pages per delivered frame.
3. **Audio banks** last — they decompress fast but they are the largest raw payload.

## Staggering

Admission is staggered at **40 MB/s** with a service budget of **1.1 ms per delivered frame**. The stagger exists because admission competes with the simulation for the same upload path; running it flat-out produced visible competition artifacts in the pose solve during the first 90 frames, which is exactly where the camera does its establishing move.

## Results

- Cold p95 tail on the opening route: 2,800 ms → **400 ms** on the reference box.
- Warm-session numbers unchanged (the pass no-ops when the residency set is already present).
- Laptop tier: the tail went from "long enough that Priya thought the build had hung" to roughly double the reference box number, which we accept for this tier.

## Rules going forward

- Any new route must ship with a prewarm list; the admission log prints a warning when a first-use admission happens on the route, and the goal is zero warnings.
- The 40 MB/s stagger is a floor, not a target — faster hardware may admit sooner, but nothing may admit ahead of the shader permutations.
- Rosa owns the admission log format; the overlay surfaces a per-category counter (see reference/debug-overlay-keys.md).
