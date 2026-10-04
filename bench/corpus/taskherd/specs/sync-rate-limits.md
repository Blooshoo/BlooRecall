# Sync rate limits (token bucket)

- Author: Priya Raghunathan
- Date: 2026-02-09
- Status: supersedes `specs/sync-throttle-policy.md` (2025-09-28); ships server-side in 2.7.0, fully enforced for all clients since 3.0.0-beta

## Policy

The flat per-device cap is replaced by a token bucket per device:

- **Sustained rate:** 900 requests per minute (tokens refill continuously, 15 per second).
- **Burst:** 120 requests may be spent instantly on top of the sustained allowance.
- **Per-board write ceiling:** 240 write requests per minute per board, shared across all devices touching that board, so no single board can monopolize a region.

Rejections carry a computed retry-after derived from the current token deficit, in seconds, not a fixed value. Clients must honor it; the client-side sync engine already does (it treats retry-after as a floor on its backoff, never a target to beat).

## Priority classes

Requests are tagged by the client with one of three classes, and the bucket is consumed in class order under pressure:

1. **User-visible edits** — pushes and pulls of task content.
2. **Reconciliation drains** — the batched merge passes after a connectivity gap.
3. **Housekeeping** — counts, avatars, telemetry-adjacent reads.

Under load, class 3 is shed first (see `runbooks/sync-storm-response.md`), class 2 is slowed, class 1 is protected to the sustained rate. Class tagging is advisory; the server may reclassify misbehaving clients, and did so 14 times in the first enforced month.

## Why these numbers

The 900/min sustained figure is the 99.5th percentile of observed per-device demand in December 2025 (measured 740/min peak), with margin for the big-import case that the old policy punished. The 120 burst covers a full 2,000-task board import in one go. The 240/min board ceiling was set from the reconciliation storm data of October 2025: no legitimate board exceeded 180/min even during failover.

## Rollout and rollback

Server-side only; no client change is required, which is why this shipped ahead of the Herd Sync v2 cutover. If rejection rates exceed 0.5% of requests on any 7-day window, the throttle layer can be pinned back to the old 500/min flat cap by config, per region, without a deploy.
