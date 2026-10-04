# Runbook: sync storm response

- Author: Priya Raghunathan
- Created: 2025-10-20 (born from the 2025-10-05 postmortem)
- Last exercised: 2026-04-28, real shed state, 11 minutes, no manual action needed

## When to use this runbook

The regional reconciliation demand gauge crosses the ceiling (6,000 passes/min default) or the shed banner is live on the storm board. A storm is load, not breakage — your job is to keep the shed state clean and short, not to fight it.

## Recognize the shape

1. Demand gauge above ceiling, sustained. Check whether it is climb (failover, viral import) or plateau (already shedding).
2. Shed state engaged: the allocator protects user-visible edits first, slows drains, and stretches the retry ladder by the fixed 1.5 factor. Stretch is by design; do not "fix" it.
3. Error mix matters more than volume: throttle rejections with computed retry-after are healthy; stale-lease failures (`ERR_HERD_117`) in bulk mean a component restarted mid-pass — see step 4 below.

## Steps

1. **Confirm class mix** on the storm board. Healthy shed: class 1 (edits) at sustained rate, class 2 (drains) slowed, class 3 (housekeeping) near zero.
2. **Find the source.** Top of the demand-by-region panel. A failover shows one region spiking; a runaway client shows one device ID (14 reclassified so far, all import scripts).
3. **Do nothing if the shed is clean.** The shed state self-clears when demand stays below 80% of ceiling for 10 minutes. Watch; do not touch.
4. **If `ERR_HERD_117` (stale lease) is firing in bulk:** a reconciler worker restarted without releasing its leases. Re-arm: run the lease sweep tool (backend toolbox, "lease sweep"), which drops leases older than the 4-minute expiry. Sweep takes under a minute; devices whose passes were invalidated restart from their first unconfirmed entry, harmlessly.
5. **If shed persists past 30 minutes:** check the allocator's regional capacity flag — someone may have lowered it for maintenance and forgotten (this happened once, 2026-01-19, 40 minutes of avoidable shedding). Restore the flag, do not redeploy anything.
6. **If demand keeps climbing past 150% of ceiling for 10 minutes:** page Priya. That shape means the pacing layer is losing, which is cutover-plan territory, not runbook territory.
7. **Close-out:** when the shed clears, note duration, peak, source, and error mix in the incident channel. Ten lines is plenty.

## Do-not list

- Do not raise the ceiling live. The ceiling is sized at 2x the p99 for a reason; raising it mid-storm moves the overload somewhere worse.
- Do not restart reconciler workers to "clear" lease errors — that is what causes bulk `ERR_HERD_117` in the first place.
- Do not disable housekeeping shedding "to let counts catch up." Counts can wait; user edits cannot.

## Related

- The v2 retry ladder and drain-pass limits live in `plans/reconciliation-rollback-plan.md` section 7; the shed threshold parameter `sync.storm_shed_threshold` (default 2,400 passes/min of sheddable demand) is set per region in the guard tooling config and should only change with Priya's sign-off.
- The founding incident analysis is `meetings/2025-10-06-sync-postmortem.md`.
