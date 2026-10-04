# Quick Capture

- Author: Maya Okafor
- Date: 2025-11-03
- Status: shipped in taskherd 2.4.0 (2025-11-24)

## What it is

Quick Capture is the one-gesture path from anywhere in the app to a new task. Swipe down from the middle third of any screen and the capture composer slides up over the current view; the keyboard is already focused and the cursor is in the title field. There is also a Capture action on every taskherd notification, so a reminder about one task can seed another without opening the app.

## The capture combo

A capture is a combo of three parts: title (required), board target (defaults to the last-used board), and an optional due chip (today, tomorrow, weekend, or a date picker). The whole combo is one continuous motion — type, tap the suggested board chip, tap Save. Median capture-to-save in the beta cohort was 3.8 seconds, and the 90th percentile was 9.1 seconds.

## Quick-saved drafts

The composer quick-saves continuously. If the app is backgrounded, interrupted by a call, or killed mid-typing, the partial title survives: the draft is restored the next time the composer opens, with a "recover draft?" bar on top. Quick-saved drafts expire after 24 hours; nothing is promoted to a real task until Save is tapped, so a stray draft never pollutes a board.

## Instant replay of board targets

The suggestion row under the title field replays the three most recent board targets as tappable chips, newest first. This is the feature beta testers called out most: 68% of captures in the final beta week went to a replayed chip rather than the default board, which told us the default-last-board rule alone was wrong.

## Gesture conflicts

On devices where the system owns edge swipes, the capture gesture is intentionally placed mid-screen and requires 120 dp of travel. The back gesture and the capture gesture coexist; we saw a 0.2% accidental-trigger rate in beta, all traced to third-party launcher builds that widen the system gesture zone.

## Success metrics

Targets set at the 2025-10-20 product review: 30% of new tasks created via Quick Capture within 60 days of ship; capture-to-save median under 4.5 seconds. Actuals at 2026-01-15: 41% share, median 3.6 seconds.
