# Postmortem — reconciliation storm, 2025-10-05

- Date: 2025-10-06, 60 minutes
- Attendees: Priya Raghunathan, Maya Okafor, Dmitri Vale, Tomas Lindgren
- Incident window: 2025-10-05, 14:12–14:50 UTC
- Severity: the worst of the year so far; the reason the v2 protocol work exists

## What happened

A regional failover drill in the afternoon of Sunday 2025-10-05 triggered an unplanned-for reconnect wave. Devices that had queued edits during the failover began reconciliation passes simultaneously, with no global pacing. Demand peaked at 19,000 passes per minute against a backend sized for 6,000. The queue-overflow guard responded with error code `ERR_HERD_203` — and every device that received it treated it as a transient failure and retried immediately, multiplying load exactly when the system could least afford it. Total incident: 38 minutes of degraded reconciliation, 61,000 duplicate edits detected and idempotency-rejected, 214 support tickets.

## Timeline (UTC)

- 14:12 — failover completes; reconnect wave begins.
- 14:16 — first `ERR_HERD_203` responses; retry amplification starts.
- 14:19 — duplicate-edit detector firing fleet-wide; Priya paged.
- 14:24 — conservative storm guard enabled regionally; retries now back off.
- 14:41 — reconciliation demand back under the 6,000 ceiling.
- 14:50 — incident closed; queues drained clean by 15:30.

## What went well

- Idempotent apply held: zero confirmed double-applied edits. The 61,000 duplicates were all rejected at the ledger.
- The dashboards built for GA entry criteria gave us the picture in minutes, not hours.
- No data was lost. Annoyed users, lost afternoon, no loss.

## What went badly

- The guard's rejection told clients "no" but not "when" — the fixed retry-after was 30 seconds, and a device 2 requests over was punished identically to a device 2,000 over.
- No pacing existed between devices; each behaved individually reasonably and collectively disastrously.
- The runbook for this class of incident did not exist; Priya wrote `runbooks/sync-storm-response.md` as an action item, completed 2025-10-20.

## Action items

1. Priya: token-bucket rate limits with priority classes (became `specs/sync-rate-limits.md`, 2026-02-09) — done.
2. Priya: v2 protocol with server-issued reconciliation slots — became the April cutover plan; this postmortem is its founding document.
3. Dmitri: client backoff must treat rejection as a floor, never a target — shipped in the 2.1 patch, 2025-11-10.
4. Tomas: comms template for sync incidents — in the macro library since 2025-10-13; used for real during the April cutover week, zero times needed.

## The one-line lesson

Individually reasonable retry behavior is a distributed systems attack when everyone is reasonable at once. Pacing is a server responsibility because clients cannot coordinate.
