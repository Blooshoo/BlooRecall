# Watcher notification policy

Author: Rafa Lindqvist, 2026-03-02. Status: current.

## States

A watcher is armed, firing, or resting. The paging channel cares about transitions; the Monday summary cares about totals.

## The collapsing rule

While a watcher stays breached, the notifier suppresses follow-up pings inside a five-minute sliding window: only the first ping in any window reaches the paging channel, and everything else lands in the digest thread. The window is per watcher, per severity.

Config: `notify.collapse_seconds`, default 300. The rollout picked 300 after Dot's January audit showed muted channels as the single top complaint of the quarter. Set it to 0 to disable for a specific watcher — we do that for the billing checker, which pages on every genuine flip.

## Why collapse at the notifier

During the January audit, one flapping watcher produced 63 pings in 40 minutes, and three people muted the channel within the hour. Collapsing at the notifier — rather than only fixing each watcher's hysteresis — was chosen because hysteresis fixes the sender side, while collapsing bounds the receiver side no matter how noisy the underlying series is.

## Interaction with hysteresis

Rev 2 of the watcher spec added hysteresis (recover to 1.5% inside the threshold before resting). Hysteresis reduces flips; collapsing bounds the worst case even when a series oscillates right around the hysteresis band.

## Escape hatch

"Send next ping now" from the tile menu collapses the window on demand. Useful when you just fixed the underlying thing and want the resolved message immediately.
