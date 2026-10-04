# Offline conflict resolution — revision 1

- Author: Priya Raghunathan
- Date: 2025-10-13
- Status: shipped in taskherd 2.0.0 (2025-10-27)

## Purpose

When two devices edit the same task without seeing each other's changes, the backend must pick a winner deterministically and quickly. Revision 1 of this spec defines the rules that shipped with shared boards GA.

## Conflict classes

We recognize exactly three conflict classes:

1. **Title and body edits** — both devices changed the text of the same task.
2. **State flips** — one device completed the task while the other edited or reopened it.
3. **Structural moves** — both devices moved the task, but to different boards or sections.

## Resolution rule (revision 1)

The server copy wins in every class. The device whose edit lost is told the edit was discarded and re-pulls the authoritative task. There is no preservation of the losing text in revision 1; the change feed records that a conflict occurred, with both edit hashes, but the losing content is not retained anywhere user-visible.

## Conflict window

A conflict exists only when both edits fall inside a five-minute window measured on server receive time. Edits further apart are applied last-write-wins by timestamp, which is not counted as a conflict and produces no change-feed entry.

## Counters and limits

- Conflicts are counted per board, per day. In the GA fleet we observed a median of 0.3 conflicts per board per week.
- A board with more than 40 conflicts in one day gets flagged for review; that threshold was never crossed in the beta cohort of 900 boards.
- Reconciliation retries a conflicted edit at most twice before giving up and surfacing a "needs attention" marker to the board owner.

## Known gaps (feeding revision 2)

Support data from November 2025 shows the biggest complaint is silent loss: 22 of 31 conflict-related tickets in the 2025-11-10 to 2025-12-08 window were users asking where their text went. Revision 2 of this spec revisits the resolution rule; see `offline-conflicts-v2.md` once it lands.
