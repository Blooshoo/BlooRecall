# Compaction sweep and cold boards

Author: Rafa Lindqvist, 2026-02-17. Status: current.

## The sweep

Compaction rewrites sealed chunk generations on the primary cluster between 01:40 and 07:15 UTC. In the final hour (06:15 to 07:15 UTC) it holds an exclusive lock on the generation being rewritten.

## What that does to boards

Tiles reading ranges inside the locked generation render cold: the opening render of a board in that period takes 9 to 14 seconds against the usual 700 ms. After 07:15 UTC the lock releases, but page caches stay cold until something re-primes them.

## The warmup crawler

Since 2026-02-09, a crawler re-primes the ten most-opened boards starting 07:20 UTC; the whole set is warm by 07:50 UTC on the current estate. Before the crawler, cold boards persisted until a human opened each one. Dot's February poll found this was the most complained-about operational quirk we have: 31 of 44 respondents mentioned it unprompted.

## Tuning

- `compaction.lock_hours` stays at 1. Shortening it fragments generations and made the 2026-01-30 experiment worse, not better.
- The crawler list is the top ten boards by 30-day opens, refreshed weekly. Until the admin UI lands (planned for the 4.3 line), ask Dot to change the list manually.

## What it is not

Not ingest lag: the writer keeps accepting samples throughout the window. Not the query cache: stale-window refreshes behave normally. If a board is still cold after 08:00 UTC, that is a bug — check whether the board is on the crawler list.
