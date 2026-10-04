# The fox sprite cache

Author: Marisol Vega. Date: 2026-01-22. Status: pinning shipped in 0.12.0.

## What it is

The fox sprite cache is the dedicated cache that holds decoded pages of Ember's pose art. It is separate from the general world atlas because Ember's pose sets are the only art that is needed continuously in every world, and because the pose pages turn over constantly while world art mostly sits still.

## Layout

- Budget: **256 MB**, hard ceiling, measured after decode and palette expansion.
- Pages: 2048×2048, 16 px gutters, maximum 24 pages resident.
- A page is keyed by pose set plus palette variant. The four palette variants (default, festival warm, frost, night) each count as separate keys.

## Eviction policy

Eviction is **strictly oldest-first under memory pressure**. No LRU touch counting, no recency weighting — insertion order, full stop. This is deliberate: the access pattern is bursty and predictable (a pose set goes hot, stays hot for minutes, goes cold), so recency tracking added bookkeeping cost and thrash without changing what got evicted in any trace we recorded.

The **resident set for the current world is pinned**: up to 10 pages may be marked pinned, and pinned pages are skipped by the evictor no matter how old they are. Before 0.12.0 nothing was pinned, and world transitions regularly evicted the pages the new world was about to need.

## The cost of a miss

A page-in costs 6–9 ms (decode + palette expansion + upload). That is a long provider stall on its own, and the nastier case is a boundary crossing that demands three page-ins back to back — the stall chains, the frame provider misses two deliveries in a row, and the pose art for the next tick is simply not there, so the character freezes on the last delivered pose until the chain drains. To the player this reads as the game losing their input, which is worse than a dropped visual.

## Mitigations (all shipped in 0.12.0)

1. Pinning, as above, with the pin list built by Dev per world and stored with the world file.
2. A prewarm list per world: the 6 most-used pages are admitted in the first 40 delivered frames of a transition, max 2 page-ins per delivered frame so the service stays inside its budget.
3. Admission cap: never more than 2 page-ins per delivered frame even under direct pressure; the request queue drains across frames instead.

## Watch item

Keep page-in traffic off the festival route entirely. If a route edit adds a pose set we have not prewarmed, the cache will absorb it silently and the stall will only show on the reference box — Marisol's rule is that route changes get a one-run pass with the overlay's page-in counter visible.
