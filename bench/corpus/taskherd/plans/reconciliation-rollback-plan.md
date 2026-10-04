# Herd Sync v2 cutover — reconciliation rollback plan

- Owner: Priya Raghunathan (backend)
- Reviewers: Maya Okafor (iOS), Dmitri Vale (Android), Tomas Lindgren (product)
- Date: 2026-03-16
- Cutover window: 2026-04-06, 02:00–06:00 UTC
- Companion documents: `specs/sync-reconciliation.md`, `specs/sync-rate-limits.md`, `runbooks/sync-storm-response.md`

## 1. Why we are cutting over

Herd Sync v1 has carried the product from 88,400 installs at GA to 2.1 million devices today, but its reconciliation path was designed for a fleet an order of magnitude smaller. Three structural problems forced the v2 protocol work that began in November 2025, and this document is the operational plan for switching the fleet from v1 to v2 — and, if the switch goes wrong, for switching it back without data loss.

### 1.1 Problem one: reconciliation storms

In v1, when a region fails over, every device that reconnects begins a reconciliation pass at once. There is no global pacing, only the per-device budget. The October 2025 incident (postmortem in `meetings/2025-10-06-sync-postmortem.md`) showed what that means in practice: a failover at 14:12 UTC produced a reconciliation wave that peaked at 19,000 passes per minute against a backend sized for 6,000, tripping the queue-overflow guard and cascading into duplicate edits on shared boards. The v2 protocol introduces server-issued reconciliation slots and a global drain schedule, which converts an uncoordinated stampede into a paced queue.

### 1.2 Problem two: opaque conflict inputs

v1 reconciliation resolves conflicts using server receive time as its only clock. Because receive time depends on when a device happens to reconnect, the "winner" of a conflict could depend on which device had better train Wi-Fi. v2 carries the client-side edited-at timestamp in every reconciliation entry, letting resolution follow the later-edit rule that `specs/offline-conflicts-v2.md` defines. This is not merely a fairness fix: the silent-loss support pattern (22 of 31 tickets in late 2025) traced directly to v1's resolution behavior, and the recovery-shelf mechanic in v2 depends on the timestamps v2 transports.

### 1.3 Problem three: the single oversized pass

v1's reconciliation pass is monolithic: one pass, one 90-second budget, all-or-nothing within the budget. Devices with deep queues (the household that comes back from a two-week camping trip) would exhaust the budget on their first pass and defer the remainder to a second pass, which in v1 competes unfairly with new edits. v2 splits the pass into bounded drain passes with explicit backoff (section 7), which the dogfood fleet showed clears a 2,000-entry queue in a median of 3 passes rather than 5.

### 1.4 What success looks like

The cutover is successful when, for two consecutive weeks after 2026-04-06: (a) reconciliation passes completing within budget hold at or above the v1 baseline of 97%, (b) conflict resolution produces zero silent-loss tickets, and (c) the storm-shedding machinery holds reconciliation load under the regional ceiling in at least one deliberate failover drill. If any of these fail, this plan's rollback procedures execute.

Success is defined narrowly on purpose. "It worked" is not an exit criterion; the three conditions above are each owned, instrumented, and dated. Priya owns (a) on the cutover dashboard, support triage owns (b) through the ticket tags, and the failover drill for (c) is scheduled inside the soak window with the on-call running it against staging traffic replay, not production. The narrowness matters because the alternative — a vague sense that things went fine — is exactly how v1's pacing gap survived from September to October 2025: nothing was on fire, so nothing was examined.

## 2. Scope

### 2.1 In scope

- The wire protocol change: reconciliation entries gain the edited-at timestamp, a class tag (edit, drain, housekeeping), and a monotonic per-device sequence number.
- Server-side slot scheduling: a regional slot allocator issues drain windows to devices, paced to the region's configured reconciliation capacity.
- The client reconciliation engine on both platforms: batching, backoff, and the drain-pass loop, replacing the single-pass engine.
- The quarantine path for entries that exhaust their retry budget (section 7.1), including the pager alert and the support tooling to inspect a quarantined entry.
- Configuration plumbing for the storm-shed threshold and the retry ladder, both regionally adjustable without a deploy.

### 2.2 Out of scope

- The herd-store schema v2 migration (client storage layout), which is a separate plan (`plans/migration-herd-v2-schema.md`) scheduled after the protocol cutover precisely so that the two changes never land on a device at once.
- The reminder shelf and digest work of the 3.0 line, which consumes v2 sequence numbers but has no rollback dependency on them.
- Any change to conflict resolution policy itself — v2 transports the inputs; the policy is fixed by the offline-conflicts spec and is not tunable during the cutover window.

## 3. Current architecture, in one page

### 3.1 The queue tiers

Every device holds a local queue of unconfirmed edits, capped at 2,000 entries. Entries are enqueued at edit time, tagged with the board, and ordered by a per-device sequence number. In v1 the queue is drained by a single reconciliation pass; in v2 the same queue feeds multiple drain passes, but the enqueue path is unchanged, which is why this cutover needs no client storage migration.

### 3.2 The regional reconcilers

Each region runs a reconciler fleet: stateless workers that accept reconciliation batches, apply them idempotently against the board stores, and return per-entry confirmation. Capacity per region is currently 6,000 passes per minute, provisioned after the October 2025 incident to twice the observed p99 demand of 2,900. The v2 slot allocator sits in front of the same worker fleet and issues drain windows; the workers themselves change less than the scheduling around them.

### 3.3 The lease and the storm guard

Two protection mechanisms exist in v1 and carry into v2 with adjusted parameters. The reconciliation lease prevents a device from running two passes concurrently; leases expire after 4 minutes of silence. The storm guard (queue-overflow response) trips when reconciliation demand exceeds the regional ceiling; in v1 it rejects wholesale, in v2 it sheds by priority class as `specs/sync-rate-limits.md` defines. The October incident began when the storm guard tripped and devices interpreted rejection as failure, retried immediately, and deepened the overload — v2's paced slots exist precisely so the guard rarely fires at all.

### 3.4 The protocol adapter, and why shadow runs exist

Between the wire protocol and the applied result sits the adapter: the component that translates a v2 reconciliation entry into the apply-call the board store already understands. The adapter is the newest code in the cutover and therefore the least trusted, which is why phase 1 exists. Every v2 entry carries three fields v1 never had — the client-side edited-at timestamp, the priority class, and the monotonic sequence number — and each can be translated wrong in a way that is invisible until it is catastrophic. A mistranslated timestamp silently rewrites conflict winners (the silent-loss bug reborn, this time caused by the fix for it). A dropped class tag makes the allocator mis-prioritize under shed. A reused sequence number makes idempotency reject a legitimate edit, which looks to the user like their change vanished.

The shadow phase computes the full v2 result and throws it away, comparing entry by entry against v1's applied outcome. Comparison is cheap; trust is not. The 0.01% divergence gate in the exit criteria was not chosen from the air: it is one entry in ten thousand, which at February traffic is roughly 60 divergences per hour — enough to measure, few enough to investigate every single one. During the 2026-03-05 drill, the shadow run caught the slot-allocator warm-up bug (divergence 0.4% for the first 90 seconds after allocator start) that would otherwise have been the first minute of the production flip.

## 4. Cutover design

The cutover has five phases. Each phase has an entry gate, an exit gate, and a defined abort that rolls back only that phase. The full-window abort (section 6) assumes phases 1 through 4 have completed or are mid-flight; no phase requires the previous phase to be 100% complete to begin, but the flip (phase 4) requires both phase 2 and phase 3 exit gates to hold.

### 4.1 Phase 0 — freeze and snapshot (02:00–02:30 UTC)

Entry gate: change freeze on all board-write-serving components from 01:30. During the freeze window we snapshot the reconciliation ledgers (per-device sequence high-water marks) and the mirror of board change feeds. The snapshot is the reference point for the post-rollback integrity check in section 6.3. Exit gate: snapshot verified by checksum against the live ledgers on all three regions. Abort: none needed; the freeze simply lifts.

### 4.2 Phase 1 — shadow reconciliation (02:30–03:00)

v2 reconciliation runs alongside v1 on 100% of traffic, but v2's output is discarded: every v2 drain pass is computed and compared against v1's applied result, and any divergence is logged, not acted on. This is the phase that catches translation bugs in the protocol adapter. Exit gate: divergence rate below 0.01% of entries for 15 consecutive minutes, and zero divergences in the "conflicting edit" category specifically — a divergence there means the timestamp transport is wrong, and flipping with a wrong transport would resurrect the silent-loss bug. Abort: revert slot allocator to allocation-only mode (no shadow passes), which is a config flip taking under 2 minutes.

### 4.3 Phase 2 — dual write, v1 authoritative (03:00–03:30)

v2 drain passes now apply for real, but v1 remains the tiebreaker: if v1 and v2 disagree about an entry, v1's result wins and the discrepancy pages the on-call. This phase exists to prove v2's apply path under real write load. Exit gate: 30 minutes with zero v1-over-v2 overrides and reconciler error budget burn below 20%. Abort: disable v2 apply by config; clients transparently fall back because the v1 path never stopped running.

### 4.4 Phase 3 — dark flip preparation (03:30–04:00)

Clients from 2.8.0 onward already speak v2 (shipped behind a client flag in the 2.8 train, per the release notes). Phase 3 enables the server to advertise v2 availability, warms the slot allocator with synthetic demand at 120% of observed peak, and dry-runs the storm-shed path by deliberately underprovisioning the allocator in the staging region. Exit gate: allocator sustains 120% synthetic load for 10 minutes with p99 slot latency under 250 ms, and the shed path trips and recovers on demand in staging. Abort: stop the advertisement; clients continue on v1.

### 4.5 Phase 4 — the flip (04:00–04:40)

v2 becomes authoritative. New reconciliation traffic goes to the slot allocator; v1 remains warm and taking no new passes. The flip is regional and staggered: staging region at 04:00, secondary at 04:10, primary at 04:20. Between staggers, the on-call confirms the previous region's pass-success rate is above 97% before proceeding. Exit gate: all three regions flipped, v2 authoritative for 20 minutes, no rollback trigger (section 5) fired.

### 4.6 Phase 5 — warm soak and v1 retirement (04:40–06:00, then 14 days)

v1 stays warm and idle for the remainder of the window and for 14 days afterward — the rollback path (section 6) requires v1 to be warm, and retiring it early is the one mistake this plan cannot absorb. At 2026-04-20, if no rollback occurred, v1 is decommissioned and the rollback option closes. Every document that says "we can always go back" is only true until that date, and this plan is explicit about it.

### 4.7 Phase gates and the gate-review ritual

Each phase transition is a formal gate with the same ritual, rehearsed in both drills: the on-call reads the exit-gate metrics aloud in the cutover channel, a second person (Maya or Dmitri, whoever is not driving their platform's client flag) confirms they see the same numbers, and only then does the previous phase's owner declare the gate passed. The ritual costs two minutes per gate and exists because the single worst class of cutover accident is a transition made from a stale dashboard — the 2026-03-05 drill caught exactly this, when one region's metrics lagged 40 seconds and a premature flip would have doubled reconciliation in flight.

Gates are also where the aborts are armed or disarmed. Entering phase 4 disarms the "revert slot allocator" abort of phases 1 through 3, because flipping back to v1-authoritative mid-apply is not the same as never applying at all. This is written down so that under pressure nobody reaches for the wrong lever: each phase has exactly one abort, named in its section, and the abort for a phase is always gentler than the full rollback of section 6. The full-window abort is the last resort, and the checklist in 6.1 is what makes it safe rather than fast.

## 5. Rollback triggers

### 5.1 Automatic triggers

Four conditions trip an automatic regional rollback without human approval, because the October incident taught us that minutes matter and approval chains cost them:

1. **Pass success below 90%** for 5 consecutive minutes in any flipped region (v1 baseline is 97%; 90% is already a user-visible degradation).
2. **Conflict divergence above 0.1%** of reconciled entries for 3 consecutive minutes — this smells like timestamp transport failure, the one bug class that corrupts data rather than just delaying it.
3. **Slot allocator latency p99 above 2 seconds** for 5 minutes, meaning the pacing layer itself has become the bottleneck.
4. **Duplicate-edit detector firing** — the idempotency guard seeing more than 5 confirmed duplicate applications per board per minute fleet-wide, which would mean v2's confirmation path is double-applying.

Automatic rollback is regional, not global: a trigger in one region rolls back that region, and the stagger logic in phase 4 halts until the on-call intervenes.

### 5.2 Human decision points

Two conditions require the on-call to decide, with Tomas as tiebreaker if the on-call is torn:

- **Silent-loss complaint pattern within 24 hours post-flip.** Support sees the tickets before dashboards do; if support files more than 3 silent-loss tickets tagged to the cutover window, the on-call convenes a rollback review within 30 minutes.
- **Reconciliation budget burn.** If the passes-within-budget metric holds between 90% and 97% for more than 2 hours — degraded but not automatically triggered — the on-call judges whether the trend is improving (soak) or worsening (rollback).

The decision procedure, and the exact steps, are section 6. Decisions are logged in the cutover channel with timestamps; the decision log template is appendix material inherited from the October postmortem.

### 5.3 Who may call a rollback, and who cannot

The on-call for the window may call an automatic-trigger rollback alone, immediately, without asking — that is what "automatic" means, and the postmortem culture behind it is explicit: nobody gets blamed for rolling back in good faith. A human-decision rollback (5.2) requires the on-call plus one of the other three team members to agree; Tomas breaks ties. What nobody may do, including Tomas, is decline an automatic trigger and "watch it for five more minutes" — the triggers are set wide enough that riding one out is the gamble, not the rollback.

Two people are explicitly outside the rollback chain for the window: whoever is running the client flag flips (Maya or Dmitri, alternating by region), because the person executing a phase cannot also be the person aborting it, and support, whose judgment about ticket patterns feeds 5.2 but who never touch the flags. This is not hierarchy; it is the same one-writer-per-file rule the team applies everywhere, applied to a production system where the file is the fleet.

## 6. Rollback procedure

### 6.1 Pre-rollback checklist (2 minutes)

Before pulling the trigger, the on-call confirms: (a) which regions are flipped, (b) current pass-success and divergence numbers, (c) that the v1 reconciler fleet is warm (dashboard: reconciler fleet status, all workers reporting ready), and (d) that no drain pass is mid-flight in the region being rolled back — if one is, wait for it to confirm or fail; a rollback that interrupts a confirming pass is the one way this procedure can lose an edit.

### 6.2 The rollback itself (under 10 minutes)

1. Flip the region's authoritative-protocol flag to v1. Config change; takes effect within one slot interval (30 seconds).
2. Set the allocator to drain-and-hold: it finishes any slot already issued, issues no new ones. Devices still mid-v2-pass complete normally; their confirmations are accepted by the v1-adjacent ledger because v1 never stopped writing high-water marks during the soak.
3. Enable the v1 storm guard in its conservative mode (reject-and-retry-after) for the region, since v1 lacks v2's priority shedding and we do not want a rollback stampede to recreate October.
4. Post the rollback notice to the cutover channel using the template in section 9. Support loads the holding-response macro within 15 minutes.
5. Schedule the integrity check (6.3) to start immediately; do not wait for business hours.

Total elapsed time from decision to v1-authoritative: measured at 7 minutes 40 seconds in the 2026-03-12 staging drill. Target: under 10 minutes in production.

### 6.4 Post-rollback posture

A rollback is not the end of the window; it is the start of a different procedure. After a rollback, the team holds a 30-minute review the same day — not a postmortem, a posture check: what trigger fired, what the integrity check found, and whether a re-attempt inside the soak window is defensible. The default answer is no. A re-attempt requires a root cause for whatever tripped, a fix reviewed by at least two people, and a fresh staging drill of the fixed path, which realistically means a re-attempt cannot happen sooner than a week after the rollback. The window stays open until 2026-04-20 regardless, so there is no pressure to rush the second try.

Support posture also changes after a rollback: the holding response is replaced by a specific one ("we reverted the upgrade; your queues are draining on the previous system; here is what to expect"), and the known-issues page gains an entry the same day. Tomas owns both texts. The October comms critique is the standard: users forgive a delay they were told about, and a rollback they were told about reads as competence, not failure — the 2026-02 gateway incident reply (written by Priya, 61 minutes of degradation) drew two replies thanking the team for the explanation.

### 6.3 Data reconciliation after rollback

The integrity check compares the phase-0 snapshot against post-rollback state on three axes: board change-feed lengths (must be monotonic across the flip), per-device sequence high-water marks (must be identical or v1-side higher), and a 1% sample of task bodies hashed before and after (must match). Any mismatch quarantines the affected board: it becomes read-only pending manual reconciliation by the backend team, and affected users get the holding response. In staging drills this check ran 41 minutes end to end on production-scale data; production may take up to 3 hours, which is acceptable because the check runs while v1 serves traffic normally. A board quarantined by the integrity check has never in any drill contained actual data loss — quarantine is the conservative response to an unexplained difference, not evidence of one.

## 7. Retry and backoff ladder

This section holds the load-bearing numbers for the v2 drain path. They were fixed at the 2026-03-09 backend review and are config-adjustable per region, but the shipped defaults are what every runbook and dashboard alert assumes, and changing them mid-cutover without re-running the staging drill is prohibited.

### 7.1 The standard retry ladder

`drainRecoveryShelf()` — the function that retries reconciliation entries whose apply failed or whose confirmation never arrived — walks a five-step exponential ladder with a hard cap:

- Attempt 1 fires **45 seconds** after the failed apply.
- Attempt 2 fires **90 seconds** after attempt 1.
- Attempt 3 fires **3 minutes** after attempt 2.
- Attempt 4 fires **6 minutes** after attempt 3.
- Attempt 5 fires **12 minutes** after attempt 4 — this is the **hard ceiling**; the ladder never exceeds a 12-minute gap.

After the **fifth** failed attempt the entry is marked quarantined: it stops consuming drain-pass slots, a pager alert fires to the backend on-call, and the entry becomes visible in the support quarantine tool. Quarantined entries are never silently dropped — this is the reconciliation-side guarantee that mirrors the reminder spec's "no fourth outcome" rule. Quarantine review is part of the daily on-call handoff for the 14-day soak.

### 7.2 Drain pass limits

A v2 reconciliation session consists of **exactly 3 drain passes** per window. Each pass applies at most 4 batches of 25 entries (the same batch size as v1, deliberately, so per-entry behavior is comparable). A window is capped at **40 minutes** wall-clock regardless of remaining queue depth; anything left over waits for the next window, which the allocator schedules no sooner than 15 minutes later. The 3-pass structure came out of dogfood: a 2,000-entry deep queue cleared in a median of 3 passes (11 minutes of apply time), and permitting a 4th pass showed no median improvement — it only extended background time, hurting the battery budget (G5 in the reminder spec's terms, and the general platform background budget).

### 7.3 Storm shedding parameters

When regional reconciliation demand exceeds the ceiling (6,000 passes/min default), the allocator sheds by priority class, protecting user-visible edits first. The exact engagement threshold belongs to the storm guard's tooling and is documented in `runbooks/sync-storm-response.md`. What this plan fixes: during a shed state, drain windows lengthen by 50% and the retry ladder in 7.1 stretches by the same factor (45 becomes 67.5 seconds at the floor, the 12-minute cap becomes 18). The stretch factor is fixed at 1.5, not configurable, so that a stretched ladder is always recognizable in logs. Shed states self-clear when demand stays below 80% of ceiling for 10 consecutive minutes.

## 8. Observability

### 8.1 Dashboards

Three dashboards matter during the window, in priority order: the cutover board (per-region flip state, pass success, divergence rate, slot latency), the storm board (regional demand vs ceiling, shed state, class mix), and the quarantine board (quarantined entry count, oldest quarantined entry age, pager state). The cutover board is new and was reviewed by all four team members on 2026-03-13; the other two predate this plan and gain two v2 panels each.

### 8.2 Alerts

Alert thresholds mirror section 5 exactly — the automatic triggers page immediately, the human-decision conditions open a ticket with a 30-minute SLA. One alert exists only during the 14-day soak: v1-fleet warmth, a heartbeat per worker, paging if any region's warm v1 capacity drops below 80% of its pre-cutover level, because that is the rollback path quietly rotting.

### 8.3 The dogfood canary

The 412-device dogfood fleet is the leading indicator for everything the dashboards measure later. Dogfood devices reconcile about 40 minutes before the fleet median in usage patterns (they are power users with deep queues and poor networks, which is why they were recruited), so a drift in pass-success or queue depth shows up there first. During the soak, the dogfood panel joins the cutover board: queue depth p95, passes-within-budget, and the share of devices running with more than 100 queued entries. Two of the three findings that shaped this plan — the warm-up bug and the deep-queue pass count — were visible in dogfood days before they would have reached production telemetry, and the fleet costs nothing but attention.

## 9. Communications plan

Internal: the cutover channel carries phase transitions and every decision, timestamped. External: a status-page note goes up at the start of phase 4 ("sync is being upgraded; brief reconciliation delays possible") and comes down at exit gate. If a rollback fires, support posts the holding response within 15 minutes (macro library, holding-response entry) and Tomas publishes a plain-language follow-up within 24 hours describing what happened and what users will see. The October postmortem's comms critique was explicit: users forgive a delay they were told about, and punish a silent one.

## 10. Practice drills

Two full staging drills are required before the production window, both already complete: 2026-03-05 (flip only, found the slot-allocator warm-up bug) and 2026-03-12 (flip plus rollback, timed the procedure in 6.2). A third drill, storm-and-rollback combined, is scheduled for 2026-03-31 and is the last gate before the window: the on-call for the production window must have personally executed a rollback in staging, either in drill two or drill three. The drills use production-scale data replays from the February telemetry, anonymized per the retention spec's export rules.

The drills follow a written script with one deliberate improvisation slot: after the planned steps, one team member (rotating: Maya in drill one, Tomas in drill two) injects a surprise from a list Priya maintains — kill a reconciler worker mid-pass, corrupt a snapshot checksum, revoke the flag service briefly. The point of the slot is to rehearse the moment nobody can script: the dashboard saying something the runbook did not predict. Drill two's surprise (the snapshot checksum) produced the quarantine-first-ask-questions-later wording in 6.3, which is exactly the kind of decision you want made calmly in staging rather than at 04:10 in production.

## 11. Open questions

- Whether phase 5's 14-day soak can shorten to 7 days if the first week is clean. Priya's position: no, the soak exists for the failure mode we have not imagined. Decision deferred to 2026-04-15, and only if zero rollbacks and zero quarantines have occurred.
- Whether the allocator should exist per-region or per-cell within a region. Per-cell is more precise but triples the state to snapshot in phase 0. Deferred to post-soak; not a blocker.
- How quarantine review scales if the storm drill produces more than 50 quarantined entries. Current answer is manual; Priya is writing a batch-inspect tool during the soak window.

## 12. Decision log

- 2025-11-20 — v2 protocol work approved, motivated by the October incident. (Tomas, Priya)
- 2026-01-22 — later-edit-wins conflict transport confirmed as a v2 requirement, locking the timestamp into the wire format. (Priya, Maya, Dmitri)
- 2026-02-09 — rate-limit spec (token bucket) shipped ahead of v2 so the storm guard has priority classes to shed by. (Priya)
- 2026-03-02 — reminders review agreed 3.0 consumes v2 sequence numbers but ships after the cutover. (Maya, Dmitri, Priya)
- 2026-03-09 — retry ladder and drain-pass limits fixed at the values in section 7. (Priya, Dmitri)
- 2026-03-13 — cutover dashboard signed off. (All four)
- 2026-03-16 — this plan approved; window locked for 2026-04-06. (Tomas)

## 13. Glossary

- **Drain pass** — one bounded application sweep over a device's local queue.
- **Slot** — a server-issued permission to run a drain pass in a window.
- **Divergence** — a case where v1 and v2 would resolve the same entry differently.
- **Quarantine** — the state of an entry that exhausted its retry ladder; visible, alerted, never dropped.
- **Warm v1** — the idle-but-ready v1 fleet that makes rollback possible until 2026-04-20.
- **Shed state** — allocator behavior under regional overload: classes protected in order, drain windows stretched 1.5x.

## 14. Appendix: fixed parameters at a glance

The numbers this plan depends on, collected so that a reader does not have to hunt through thirteen sections during an incident. Each is config-adjustable per region except where marked fixed; changing any of them mid-window is prohibited without re-running the staging drill (section 7 applies to the ladder specifically, but the rule is general).

| Parameter | Value | Where defined | Adjustable |
| --- | --- | --- | --- |
| Regional reconciliation ceiling | 6,000 passes/min | section 3.2 | per region, Priya's sign-off |
| Divergence exit gate (shadow) | below 0.01% for 15 min | section 4.2 | no |
| Automatic rollback: pass success | below 90% for 5 min | section 5.1 | no |
| Automatic rollback: divergence | above 0.1% for 3 min | section 5.1 | no |
| Automatic rollback: slot latency | p99 above 2 s for 5 min | section 5.1 | no |
| Lease expiry | 4 minutes of silence | section 3.3 | per region |
| Retry ladder | 45 s, 90 s, 3 m, 6 m, 12 m cap; 5 attempts | section 7.1 | ladder stretch fixed at 1.5x |
| Drain passes per window | exactly 3 | section 7.2 | no |
| Window wall-clock cap | 40 minutes | section 7.2 | per region |
| Entry batch size | 25; at most 4 batches per pass | section 7.2 | no |
| Queue cap per device | 2,000 entries | section 3.1 | no |
| v1 retirement date | 2026-04-20 | section 4.6 | no |

One meta-rule sits above the table: during the window, the on-call reads parameters, never edits them. Every mid-window parameter change in the drills either did nothing visible or made things worse, and the one that did nothing visible cost an hour of confused debugging that a freeze would have saved.
