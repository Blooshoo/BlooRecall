# Runbook: push pipeline

- Author: Dmitri Vale, with Priya Raghunathan
- Created: 2026-02-23 (with the 2.6.0 hardening)
- Scope: the notification relay between the backend and the platform push gateways

## Pipeline shape

Board events become relay jobs in three stages: the board store emits a change event, the relay coalescer holds it for a short window to batch bursts, and the dispatcher hands the batch to the platform gateway. The coalescing window is `push.relay_window_seconds` = 90: any events for the same device inside the window ride one push. The window is the single most misunderstood knob in the system — it trades delivery latency for battery, deliberately. At 90 seconds, a device receives about 3.2 pushes per day at average activity; at 15 seconds it received 11 and the battery complaints of December 2025 happened.

## Recognize trouble

- **Backlog depth** (relay jobs waiting) above 5,000 sustained 10 minutes: dispatcher trouble, not coalescer trouble.
- **Gateway acceptance rate** below 98%: credential or quota-class problem at the gateway, page Priya — this is not a self-heal.
- **Relay timeouts**: batches that miss the gateway deadline carry error `ERR_HERD_512`. A handful per hour is normal (gateway hiccups). More than 50 per minute means the gateway is degraded and the replay path (below) is about to earn its keep.

## Steps

1. **Check the coalescer window flag first.** If someone shortened `push.relay_window_seconds` for an experiment and forgot to restore it, backlog and battery complaints arrive together. Restore 90; the flag takes effect within one window.
2. **If `ERR_HERD_512` is elevated:** the dispatcher already queues undelivered batches for replay — up to 3 replays per batch, oldest first, before the batch is marked expired and its content is left to the client's next sync to pick up. Verify the replay gauge is advancing; if replay is stuck at 0 attempts while timeouts climb, bounce the dispatcher (single instance at a time; the coalescer covers during the bounce).
3. **If backlog keeps growing through healthy acceptance rates:** find the hot device or hot board. One board with 10,000 members generates a batch storm on every change; the per-board write ceiling should be shedding it — if the ceiling flag is off, that is your answer (turn it on; it defaults on).
4. **Reminder-class pushes are never coalesced.** If due reminders are arriving in batches, that is a bug: check that the reminder emitter tags its jobs `no-coalesce` (regression guard added 2026-02-20 after the beta finding). A batched reminder is a sev-3 minimum.
5. **Close-out:** peak backlog depth, timeout count, replay outcomes, and whether the window flag was the culprit (it was, both times so far).

## History worth knowing

- 2026-01-28: window flag left at 15 after an experiment; 2,300 battery-adjacent tickets in four days. The flag now logs every change with the actor's name.
- 2026-02-14: gateway degradation, 61 minutes of elevated `ERR_HERD_512`; replay carried every batch, zero permanent losses, 9 support tickets. The hardening shipped because of this incident, not before it — note the ordering, it was tight.

## Related

- Reminder delivery surfaces and suppression behavior: `specs/reminder-delivery-surfaces.md`.
- The 3.0 shelf changes how undelivered reminders behave after replay exhausts — see `specs/reminders-rework-spec.md` section 3; until 3.0 GA, an expired reminder batch simply waits for next sync.
