# On-call rotation

Owners: Dot (schedule), Rafa and Juno (tiers). Updated 2025-11-25.

## Escalation path

If the primary has not acknowledged within ten minutes, the pager retries once, then moves to the secondary, and after twenty-five minutes in total it lands on Rafa as the fixed fallback for the data tier. Never email — the pager only trusts its own API.

## Handoff

Friday 16:00 UTC, fifteen minutes, camera optional: open pages, expiring maintenance windows, and anything in "watch" state. The outgoing week posts notes in the ops channel before the call; the incoming week leaves with at most three action items.

## Silences

Planned maintenance mutes notifications for at most four hours; anything longer needs Dot's sign-off. Every maintenance window carries a reason string — "testing" is not a reason, "compaction rehearsal on gen-14" is.
