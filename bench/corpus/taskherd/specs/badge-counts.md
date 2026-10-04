# Badge counts

- Author: Maya Okafor
- Date: 2025-12-15
- Status: active

## What the badge counts

The app icon badge is the number of tasks that are assigned to the current user, not completed, and due today or overdue. Nothing else contributes: comments, pings, and board activity never touch the badge — those are notification-channel concerns. A board the user has demoted still counts; the badge is about obligations, not attention.

## Per-board versus aggregate

The aggregate badge is the sum across all boards the user is a member of. The in-app board list also shows per-board counts next to each board name; those use the same computation so the two can never disagree by more than a pending sync cycle.

## Drift and the backfill pass

The badge is computed locally from the last known board state, so it can drift from the server after a restore-from-backup, an account switch, or a long gap where another device completed tasks. Drift is corrected by the backfill pass: on the first sync after cold start, the client fetches the authoritative assigned-open count per board and overwrites the local figure.

One backfill pass fetches at most `badge.backfill_limit` = 500 items per board. Boards larger than that get a second pass after 5 seconds; the fetch is paged, so ordering is stable. During the 2-minute window after cold start the badge is allowed to be provisional; after that window it must be server-authoritative or the client clears it to zero and logs a diagnostic (a zero badge is treated as better than a wrong badge — Tomas made that call in the 2025-12-11 product review).

## Manual repair

Support can trigger a forced backfill from the account tools; the procedure is in `runbooks/badge-backfill.md`. Forced backfills bypass the cold-start window and run immediately, one board at a time.

## Telemetry

Drift incidents (user-visible wrong badge lasting more than 10 minutes) run about 40 per week across the fleet as of 2025-12; 80% involve restore-from-backup. The backfill pass resolves 95% of them within one app open.
