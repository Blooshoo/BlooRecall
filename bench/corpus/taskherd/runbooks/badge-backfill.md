# Runbook: forced badge backfill

- Author: Maya Okafor
- Created: 2026-01-26
- Audience: support rotation with the account tools open

## When to use

A user reports the app icon count is wrong and it stayed wrong after opening the app twice on a stable connection. Twice matters: the first open starts the normal backfill, the second confirms it settled. If the count is still wrong, the local figure is pinned by something the normal pass cannot move, and the forced backfill is the tool.

## What the forced backfill does

It runs the same server-authoritative count fetch as the cold-start backfill (`specs/badge-counts.md`), but immediately and one board at a time, bypassing the cold-start window entirely. The result overwrites the device's local figure on the next open. It does not touch notifications, does not re-send anything, and is invisible to the user except that the number is finally right.

## Steps

1. Confirm the account and device: get the device ID from the user (Settings > About > long-press the version row). A forced backfill is per-device, not per-account, by design — pushing counts to a device the user no longer holds helps nobody.
2. Check the grace state. The tools show whether the device is inside `badge.overflow_grace_minutes` (default 10) of a recent count write. If it is, wait out the grace window first — a forced run inside the grace period is discarded by the device, which is the number one "I ran it and nothing happened" cause.
3. Run the backfill from the account tools: board order is the user's pinned boards first, then alphabetical. Four boards take about 20 seconds server-side.
4. Tell the user to open the app once more. The corrected count lands on that open.
5. Log it. Every forced run lands in the weekly support summary; 12 runs total since January, and the pattern in them is the restore-from-backup cluster from the known-issues page.

## If it did not fix it

- The user's own device may be counting a different definition (for example, a demoted board they forgot they are still a member of — demoted boards still count; the badge tracks obligations, not attention). Walk through the member list with them.
- A stuck local queue can pin the figure: check the sync dashboard for the device's queue depth. If the depth is nonzero and growing, this is a sync ticket, not a badge ticket — the badge will fix itself when the queue drains.
- Escalate to Maya only after both of the above; there has never been a case that survived them (0 escalations in 12 runs).

## Do-not list

- Do not force-run per-board counts one at a time by hand. The tool exists because the manual path raced itself and made counts worse (the 2026-01-19 incident, two tickets deep).
- Do not run it during the user's reported sync storm without checking the storm board first; during a shed state the count fetches shed with housekeeping traffic and the run silently no-ops.
