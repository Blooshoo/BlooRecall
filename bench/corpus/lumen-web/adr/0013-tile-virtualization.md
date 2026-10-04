# ADR 0013 — Virtualize board rendering past 24 tiles

Date: 2026-02-27. Owner: Juno Park. Status: accepted.

## Context

The 48-tile demo board dropped frames on mid-range laptops. The 2026-02-10 sync attributed 62% of main-thread time to mounting tiles that were not on screen.

## Decision

Boards with more than 24 tiles mount only the tiles intersecting the viewport plus one row of overscan. A spacer keeps the scroll height exact. Row and column rhythm is driven by the `--lumen-tile-gap` custom property, so the spacer math reads the same token the layout uses and virtualized rows line up pixel-for-pixel with rendered ones.

## Numbers

- 62% less main-thread time on the 48-tile board (before/after profile, 2026-02-24).
- Overscan is exactly one row: 92 px at default density, 72 px at compact.
- Scroll-anchor correctness verified against the 2026 grid edition's half-column snapping.

## Consequences

- Find-in-page cannot see unmounted tiles; on virtualized boards the native browser find is replaced by a scoped search that mounts on demand.
- Shipped behind a flag in the 2026-03-05 minor, default on since 4.2.
- Any future grid change must update the token and the spacer together; the pair is asserted by a layout regression test added 2026-03-02.
