# Static copy pipeline

Author: Juno Park, 2026-05-12. Status: GA since the 2026-03-05 minor release.

## What it produces

Any tile can be rendered to a fixed-layout PNG. Any whole board can be rendered to a paginated A4 document: one tile per section, cover page carrying the board title and range. Both land in object storage with a 14-day TTL and a private-by-default link.

## How to trigger it

Share menu, then "Static copy". Two options: "this tile" and "whole board". A toast shows queue position. A 24-tile board completes in about 20 seconds; a single tile in under 3.

## Renderer cluster

Two nodes, 8 vCPU each, headless canvas rendering. Peak occupancy since GA measured at 0.4 nodes. A third node is planned for Q4 per the 2026-08-19 planning note — that is a budget decision, not an incident response.

## Limits

- 400 tiles per board document, hard cap; the menu disables the whole-board option past it.
- Live tiles render their latest settled frame, and the document footer says so explicitly.
- Watcher states print as of render time, with the render timestamp on the cover page.

## What it is for

Design-partner reviews, board packs for quarterly business reviews, and archiving a board's appearance at a moment in time. It is deliberately not a general-purpose rendering API; the queue has no programmatic entry point.
