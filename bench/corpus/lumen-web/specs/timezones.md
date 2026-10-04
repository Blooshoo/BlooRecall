# Time zones on boards

Author: Juno Park, 2025-12-11. Status: current.

## Defaults

Boards render in the viewer's zone. A board can pin a fixed zone ("this board lives in UTC") for distributed teams; pinned boards show a small globe chip.

## Storage

Everything stored is a UTC instant. Zone math happens only at render time, never at write time.

## Grain boundaries

Hour buckets flip at the board's zone offset, not at storage grain. A 10-second or minute bucket never straddles an offset change; hour and day buckets can.

## DST

A 23- or 25-hour day renders as-is with a footnote chip. We never stretch or compress buckets. The residual skew bug here was fixed in the 2026-08-27 patch — hour buckets straddling a jump had rendered one hour off in viewer-local mode.

## Pitfalls

- Monthly aggregates use the board's zone for month edges, so two boards in different zones can disagree by one day on where "March" starts.
- Always label the zone when pasting a board link into a document; the reader's viewer will not match yours.
