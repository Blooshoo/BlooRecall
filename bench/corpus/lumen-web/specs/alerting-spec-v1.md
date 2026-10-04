# Threshold watcher specification (rev 1)

Author: Rafa Lindqvist, 2025-11-12. Status: revised — see the 2026 revision of this spec (same filename, -v2).

## Evaluation cadence

Watchers evaluate every 60 seconds. Each evaluation looks at the last three grains of the series at minute grain.

## Firing rule

A watcher fires after 2 consecutive breaches (2-of-3 lookback). A breach is a sample strictly beyond the threshold; equality is not a breach.

## Resting

After firing, a watcher rests when it sees 10 consecutive clean minutes. Resting posts a single "resolved" message to the paging channel.

## Routing

Fired watchers post to the paging channel and, for non-critical severities, to the daily email digest. Routing is per-watcher; there is no per-board routing in rev 1.

## Known gaps

- A watcher that keeps breaching re-posts on every flip between firing and resting; a noisy series can post the same condition over and over.
- No snooze; muting is manual, at the channel level.
- Evaluation is skipped while the source series is stale beyond 15 minutes; the watcher shows a "stale" state instead.
