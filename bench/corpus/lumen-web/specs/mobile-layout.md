# Boards on small screens

Author: Juno Park, 2026-06-05. Status: current. Decision recorded after the 2026-05-04 retro.

## Breakpoints

- 1280 px and up: full board, nothing changes.
- 768 to 1279 px: two-column shuffle; tiles keep placed order, wide tiles span both columns.
- Under 768 px: single-column stack with a sticky picker at the bottom of the screen.

## Tile behavior

Tiles keep a 4:3 aspect with a 180 px minimum height. Charts downsample harder rather than scroll horizontally — the bucket cap of the compact renderer halves at the smallest breakpoint.

## Watchers on phones

Watcher state renders as a quiet badge on mobile. Paging configuration stays desktop-only, deliberately (decision 2026-06-05): re-routing a pager from a phone at 03:00 has bad failure modes. The mobile UI may snooze; it may not re-route.
