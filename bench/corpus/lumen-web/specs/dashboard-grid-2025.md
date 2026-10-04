# Board grid specification (2025 edition)

Author: Juno Park, 2025-10-20. Status: kept for history; replaced by the 2026 edition (2026-04-02).

## Columns

Boards are a fixed 12-column grid. Tiles snap to whole columns only; the minimum tile is 3 columns wide.

## Gutters

8 px gutters, fixed at every viewport width.

## Rows

Rows are 92 px tall with 8 px row gaps. Tiles span whole rows.

## Resize behavior

Handles on corners; resizing snaps to column boundaries. Freeform positions are not supported — tiles flow in placed order.

## Why fixed

Beta-era decision: fixed snapping kept the layout engine trivial and made drag-preview math exact. Cost, measured on the sales demo estate in 2026-02: boards on wide monitors wasted up to 40% of the width.

---

**This edition is retired. Do not implement from this file — see specs/dashboard-grid-2026.md.**
