# Board interactions

Author: Juno Park, 2026-01-18. Status: current.

## Cross-filtering

Clicking a bar, slice or segment on any tile narrows every other tile on the same board to that value. A second click on the same value clears it. The chip row under the board title lists what is currently applied; chips are individually removable. Narrowing propagates within about 150 ms and never refetches the tile you clicked.

### Linked time range

Dragging a window on the master strip moves the picker on every other tile in lockstep. Tiles pinned to a fixed stretch do not follow; the pin wins and shows a small anchor glyph. Clearing the strip restores each tile's own previous picker.

### Drilldown targets

Double-clicking a segment opens the next breakdown level in a slide-over. The breadcrumb at the top of the slide-over tracks the path; each crumb is clickable. Slide-overs never mutate the board underneath.

## What does not propagate

Typing in one tile's search box stays local. Only rendered marks (bars, slices, segments) and the master strip propagate. Esc closes the slide-over; Esc twice clears all chips on the board.
