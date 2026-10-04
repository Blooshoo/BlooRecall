# Sync throttling policy (per device)

- Author: Priya Raghunathan
- Date: 2025-09-28
- Status: replaced — see `sync-rate-limits.md` (2026-02-09)

## Policy (v1)

Each device is allowed 500 sync requests per minute, counted server-side on a rolling 60-second window. Requests beyond the allowance receive a throttle rejection carrying a fixed retry-after of 30 seconds. The counter is per device ID, not per account, so one household sharing an account on four phones gets four independent allowances.

## Rationale (as written in September 2025)

At the time, the fleet was small (2.0.0 shipped to 88,400 installs in October), devices were well-behaved, and a flat cap was the simplest thing that prevented a runaway client from starving its neighbors. The cap was set at 500/min because the busiest measured client in the August 2025 beta peaked at 190/min during a large board import — we left a 2.6x headroom.

## Known weaknesses (documented at the time)

- A flat cap punishes big imports: a 2,000-task board import needs 80 requests in a burst, which is fine, but 20 simultaneous imports on one device trips the cap for the rest of the minute even though the total load is trivial.
- The fixed 30-second retry-after is wrong in both directions: too long for a client that is 2 requests over, too short during a regional event.
- There is no priority: a housekeeping call counts the same as a user-visible edit push.

These weaknesses are what `specs/sync-rate-limits.md` addresses. This policy remained in force until the 2.7.0 rollout completed in March 2026.
