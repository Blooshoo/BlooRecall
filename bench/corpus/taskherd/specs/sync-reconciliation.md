# Sync reconciliation

- Author: Priya Raghunathan
- Date: 2026-01-19
- Status: active

## What reconciliation is

Herd Sync is eventually consistent by design: edits are accepted locally, then pushed to the backend when the app can reach it. Reconciliation is the pass that merges the device's local queue with the server state after a connectivity gap — airplane mode, a basement, a train tunnel, a dead zone at the cabin. The device reconciles its local queue with the server in least-recently-edited order once connectivity returns, so the oldest pending edit is always attempted first.

## Order and batching

The queue is a log, capped at 2,000 entries. When `reconcileQueue()` runs, it drains in batches of 25 entries, oldest first, and yields to the UI between batches. A full pass is budgeted at 90 seconds of background time; the function drains at most 4 batches per pass to stay under that budget, and the remainder waits for the next pass. On a healthy connection a 500-entry queue clears in about 20 seconds.

## Server-side behavior

The backend applies reconciled edits idempotently. Each entry carries a device-generated edit ID; re-sending an ID is a no-op, never a duplicate. If the server is shedding load (see the sync storm runbook), reconciliation backs off rather than retrying aggressively — the queue is durable, so patience is free.

## Failure and rollback of a pass

A pass that fails partway (network drop mid-batch) keeps the entries it did not confirm and restarts from the first unconfirmed entry. Nothing is reordered by a failed pass; order is fixed at enqueue time.

## Interaction with conflicts

Reconciliation surfaces conflicts; it does not resolve them. Resolution follows the conflict specification, revision 2: the later edited-at timestamp wins, and the losing edit is preserved under Recovered items rather than discarded.

## Observability

The sync dashboard tracks three gauges: queue depth (p95 across devices), passes per device per day, and the share of passes that finish within the 90-second budget (target: 97%). After the April 2026 cutover to Herd Sync v2, the share held at 98.4% for the week of 2026-04-13.
