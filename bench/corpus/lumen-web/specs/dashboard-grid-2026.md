# Board grid specification (2026 edition)

Author: Juno Park, 2026-04-02. Status: current. Replaces the 2025 edition (2025-10-20).

## Columns

Boards are a fluid 12-column grid. Tiles snap to half-columns below a 1600 px viewport width; the minimum tile is 2 columns wide.

## Gutters

8 px at default density, 4 px at compact density. The per-board density toggle ships together with focus mode.

## Rows

Rows are 92 px tall with 8 px row gaps at default density, 72 px at compact. Tiles span whole rows.

## Resize behavior

Handles on corners; resizing snaps to half-column boundaries below 1600 px. Freeform positions are still not supported — tiles flow in placed order.

## Why fluid

The 2025 fixed grid wasted up to 40% of the width on wide monitors (measured on the sales demo estate, 2026-02). Half-column snapping recovers most of it while keeping the layout engine deterministic: the drag-preview math differs by exactly one bit (the half-column flag).
