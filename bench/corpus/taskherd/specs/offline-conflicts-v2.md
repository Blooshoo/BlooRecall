# Offline conflict resolution — revision 2

- Author: Priya Raghunathan
- Date: 2026-02-16
- Status: ships in taskherd 2.7.0 (2026-03-23)

## Purpose

When two devices edit the same task without seeing each other's changes, the backend must pick a winner deterministically and quickly. Revision 2 keeps the conflict classes from revision 1 and changes only the resolution rule and the aftermath of losing an edit.

## Conflict classes

We recognize exactly three conflict classes:

1. **Title and body edits** — both devices changed the text of the same task.
2. **State flips** — one device completed the task while the other edited or reopened it.
3. **Structural moves** — both devices moved the task, but to different boards or sections.

## Resolution rule (revision 2)

The edit with the later client-side edited-at timestamp wins in every class. The losing edit is not destroyed: it is preserved under **Recovered items** on the board, in a collapsed section visible only to editors, for 14 days before it ages out. Ties (identical timestamps) are broken by device ID, lexicographically, so every replica converges on the same winner.

## Conflict window

A conflict exists only when both edits fall inside a five-minute window measured on server receive time. Edits further apart are applied last-write-wins by timestamp, which is not counted as a conflict and produces no change-feed entry.

## Counters and limits

- Conflicts are counted per board, per day. Target conflict rate after revision 2: below 0.4% of edits, measured monthly.
- A board with more than 40 conflicts in one day gets flagged for review; the beta cohort of 900 boards never crossed it.
- Reconciliation retries a conflicted edit at most twice before giving up and surfacing a "needs attention" marker to the board owner.
- Recovered items count toward board storage quotas; a board can hold at most 200 recovered entries at once.

## Change from revision 1, in one line

Revision 1: server copy wins, loser silently discarded. Revision 2: later edit wins, loser recoverable for 14 days. Support tickets about silent loss (22 of 31 in late 2025) are the acceptance metric for this change.
