# `<Sparkline>` component specification

Author: Juno Park, 2026-01-30. Reviewers: Cece Marlow, Rafa Lindqvist. Status: current.

## What it is

`<Sparkline>` is our tiny inline chart: one series, no axes, no legend, default 120 x 24 px. It is the renderer behind the compact trend tile that shipped in the 2026-06 minor release.

Naming note: an unrelated internal project uses the word "sparkline" for a spark-particle trail effect in a game. Ours is a chart component. If you are searching for a particle system or a gameplay visual and you landed here, that is the other project — nothing in this file emits particles.

## Data path

Props accept raw points; the component calls `useBucketedRange()` to downsample to at most 40 buckets before rendering. Bucket weighting is largest-triangle-three-buckets; under 8 points it falls back to plain stride sampling. The hook memoizes per (series, range) so a board of 40 instances sharing ranges does not rebin 40 times.

## Rendering

Canvas, two layers. The base layer draws the line. The trail layer is what makes the component feel alive: on hover-scrub it renders the comet trail and the terminal glow. Motion rules live in Cece's visual notes; this spec only fixes the budget — all trail animation resolves within 180 ms of the pointer stopping.

## Props

- `series: SeriesRef` (required)
- `width?: number` — default 120, hard clamp 64 to 160
- `height?: number` — default 24, clamp 16 to 48
- `dense?: boolean` — drops the terminal dot, tightens the stroke, doubles the trail decay length

## Performance budget

First paint at most 6 ms per instance on the reference laptop; a board with 40 instances stays under 120 ms total. Verified 2026-01-28 on the replay estate with the profiler attached.
