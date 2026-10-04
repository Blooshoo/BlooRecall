# Threshold watcher specification (rev 2)

Author: Rafa Lindqvist, 2026-02-24. Status: current. Rev 2 of the 2025-11-12 spec.

## Evaluation cadence

Watchers evaluate every 15 seconds. Each evaluation looks at the last five grains of the series at 10-second grain.

## Firing rule

A watcher fires after 3 breaches inside a 5-grain lookback (3-of-5). A breach is a sample strictly beyond the threshold; equality is not a breach.

## Hysteresis

New in rev 2: to rest, the series must recover to 1.5% inside the threshold, not merely touch it. This kills the flapping that made rev 1 re-post on every flip.

## Resting

After firing, a watcher rests when it sees 10 consecutive clean grains at 10-second grain. Resting posts a single "resolved" message to the paging channel.

## Routing

Fired watchers post to the paging channel and, for non-critical severities, to the daily email digest. Rev 2 adds per-watcher snooze (30 minutes, 2 hours, rest of day) from the tile menu.

## Notifier behavior

While a watcher stays breached, the notifier applies its own collapsing rule (see the watcher notification policy spec). Rev 2 removes the re-post-on-flip gap that rev 1 listed under known gaps.

## Known gaps

- Evaluation is skipped while the source series is stale beyond 15 minutes; the watcher shows a "stale" state instead.
