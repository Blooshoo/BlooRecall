# Reminders rework — specification (the 3.0 line)

- Authors: Maya Okafor (iOS), Dmitri Vale (Android)
- Date: 2026-03-30
- Status: approved for the 3.0 beta; beta staged at 5% of accounts from 2026-09-08
- Review trail: `meetings/2026-03-02-reminders-review.md`

## 1. Problem statement

Reminders are the second-most-used feature in taskherd and the source of our longest-running reliability complaints. Between 2025-10 and 2026-02, reminders accounted for 31% of all support tickets, more than sync (24%) and onboarding (11%) combined. When we categorize those tickets, three failure patterns dominate, and they share one root cause: taskherd 2.x schedules reminders inside the app process, on the assumption that the process is alive, or will be woken, at the moment a reminder is due.

### 1.1 Pattern one: the killed process

On both platforms, the operating system reclaims background processes under memory pressure. When that happens to taskherd, in-process timers die with it. The 2.x mitigation — rescheduling all pending reminders on every app open and on every sync — means a reminder for a task the user never reopened simply never fires. We measured this directly with instrumentation added in 2.6.1: of reminders due while the app had been closed for more than 48 hours, 9.7% fired late and 3.1% never fired at all. That 3.1% is the single worst number anywhere in the product, and it is concentrated on exactly the users who trust us most: the ones who set a reminder and walk away.

### 1.2 Pattern two: deferred windows

The 2.x Android client scheduled reminders through deferred background job windows. Deferred windows are cheap on battery and catastrophic for punctuality: the scheduler batches jobs and can hold a window for tens of minutes on an idle device. The incident the team nicknamed after the tumbleweed made this visible enough to prioritize (see `plans/tumbleweed-timer-plan.md`): reminders arrived 20 to 90 minutes late on devices that had been idle overnight. The interim fix in 2.9.0 (exact window requests) reduced the median lateness from 34 minutes to 6, but it is a patch over the architectural problem, not a fix of it.

### 1.3 Pattern three: silent collision with suppression

When a reminder fires while an attention profile is active, 2.x does the right thing on paper (silent tray delivery) but the wrong thing in practice: the tray is where notifications go to be forgotten. Our delivery instrumentation shows that only 12% of tray-delivered reminders are acknowledged within 4 hours, versus 71% of banner-delivered ones. The user experience is "taskherd lost my reminder" even though the log says it delivered. The rework introduces the digest as a deliberate, designed surface for exactly this case, instead of the tray being a silent dead end.

### 1.4 Why this is a rework, not a patch

All three patterns trace to one design decision: the schedule lives in the client process. The rework moves the authoritative schedule to a system-level alarm mechanism backed by a server-side mirror, and introduces an explicit, user-visible shelf for reminders that could not be delivered. That is a change to the data model, the delivery pipeline, and both platform clients simultaneously — hence a 3.0 line, hence this document.

### 1.5 The cost of standing still

Doing nothing was priced, because it always should be. At the current install growth curve (2.1 million devices in May 2026, growing 6% month over month), the never-fires cohort alone produces about 900 tickets per month by the end of 2026, and the churn data attached to those tickets is ugly: users whose reminder never fired cancel paid plans at 2.7 times the baseline rate within 30 days. Reminders are also the feature most tightly coupled to trust — a task manager that silently loses a medication reminder has failed at the one job, no matter how good the boards are. Priya's estimate (2026-02-26, backend planning) was that the shelf plus mirror costs roughly one engineer-month of build and a rounding error of server capacity; the ticket and churn cost of inaction is several times that per quarter, forever. The rework is the rare plan where the do-nothing column loses on every line.

## 2. Goals and non-goals

### 2.1 Goals

- **G1 — Never silently drop.** Every scheduled reminder is either delivered on a surface the user can see, held on the shelf with visible status, or folded into the digest. There is no fourth outcome.
- **G2 — Punctuality.** At least 98% of reminders fire within 60 seconds of their due time on devices that are powered on, regardless of how long the app has been closed.
- **G3 — Respect suppression without forgetting.** A reminder that lands during suppression is delivered silently AND appears in the next morning digest, so the user encounters it through a designed surface within hours, not days.
- **G4 — Observable.** Every reminder has a delivery status the user can inspect (Settings > Reminders > Delivery report), and every state transition is instrumented server-side.
- **G5 — Battery-neutral.** The rework must not increase background wakeups per device per day by more than 10% versus 2.9.

### 2.2 Non-goals

- Location-based reminders. Explicitly out of scope; they need a different permission posture and a different scheduling mechanism. Revisit no earlier than 3.2.
- Smart rescheduling (moving reminders the system thinks are ill-timed). The system delivers what the user scheduled, full stop.
- Per-reminder custom sounds. The channel model from `specs/notification-channels.md` stays as is.
- Backfilling reminders for tasks created before 2.0. The 1.x import already dropped them; we will not resurrect four-year-old state.

### 2.3 Constraints

- No new permission prompts. The rework must work with the permissions the funnel already requests (see `specs/onboarding-funnel-v2.md`).
- Server-side schedule mirror must be derivable entirely from existing edit logs, so that account export and the purge job in `specs/data-retention.md` keep working unchanged.
- Both platform clients ship in the same release train; there is no interim protocol version.

### 2.4 Prior art inside the product

Two existing mechanisms shaped this design, and it is worth recording what was borrowed and what was rejected. From the sync side we borrowed the "no silent loss" idiom: reconciliation quarantines entries rather than dropping them (the cutover plan's section 7 guarantees it), and the shelf applies the same contract to reminders — a bounded, visible holding state with an alerting path, never a fourth outcome. From the badge work we borrowed the honesty rule: a provisional value is acceptable briefly, a wrong value is worse than a zero, so the delivery report always shows what actually happened rather than what we intended. Rejected prior art: the 2.x approach of rescheduling on every app open (this is pattern one, kept only as a migration path), and a proposal from the January spike to deliver reminders through the push relay as a backstop. The relay backstop was rejected because a push cannot wake a dead process on either platform at reminder-grade reliability, and building a second delivery path whose failure modes we would have to explain was worse than building one path that tells the truth.

## 3. The alarm shelf

The central new concept is the shelf: a durable, per-device store of every reminder whose delivery has not yet been confirmed, plus every reminder that tried and failed. The shelf is what makes "never silently drop" (G1) enforceable, because every reminder is somewhere — scheduled, delivered, or shelved — and a user can always ask where.

### 3.1 Lifecycle of a reminder

A reminder moves through exactly five states:

1. **Scheduled.** The due time is in the future. Both the device alarm and the server mirror hold the schedule.
2. **Armed.** The due time is within the delivery horizon and the device has registered a system-level alarm.
3. **Delivered.** A surface confirmed receipt (banner shown, tray posted, digest included, or shelf marker observed).
4. **Shelved.** Delivery was attempted and not confirmed within the confirmation window. The reminder sits on the shelf with a visible reason.
5. **Completed/cancelled.** The task was completed or the reminder deleted before firing. The alarm is unscheduled and the mirror entry marked.

State transitions are one-way except Shelved, which can transition to Delivered (user opens the app and handles it) or back to Scheduled (user edits the time).

### 3.2 What shelves a reminder

A reminder is shelved when any of these hold at due time:

- The device is powered off or unreachable for the entire confirmation window.
- An attention profile suppressed the banner AND the tray entry was not acknowledged within the window.
- The system refused the alarm (quota exhaustion, platform-specific failure — see section 5 and section 6).

Every shelved reminder carries a reason code from a fixed enumeration of five values, so the delivery report and support macros can speak the same language. The reason codes are: `device-off`, `suppressed`, `quota`, `clock-skew`, and `unknown`.

### 3.3 Shelf as a user-visible surface

The shelf is not a hidden log. It appears in two places: the in-app "Undelivered" section at the top of the boards list (with a count badge), and the Monday morning digest under "missed while away". A shelved reminder can be promoted back to Scheduled with one tap (re-arm at the next round hour or tomorrow 09:00), completed directly from the shelf, or dismissed to the board's Recovered-style history. The 3.0 beta cohort's shelf median occupancy is 1.4 items; the 95th percentile is 9. If occupancy exceeds 20, the shelf shows a "trim" action that bulk-dismisses everything older than 7 days.

### 3.4 The server mirror

The server holds a mirror row per scheduled reminder: task ID, due time (absolute), recurrence expansion (up to 10 occurrences), device binding, and state. The mirror is authoritative for recurrence and for cross-device visibility (a task's reminder state is visible to board members in the task detail view), but the device alarm is authoritative for firing — the mirror never pushes a reminder on its own except into the digest path. This split keeps us honest about G2 (a server push cannot wake a phone) while the mirror gives us the audit trail and the digest feed. Mirror rows age out with the same horizons as the task they belong to.

### 3.5 Recurrence expansion

Recurring reminders are expanded exactly 10 occurrences ahead, on both device and mirror. When an occurrence fires (or shelves), the window slides forward. This bounds alarm quota usage (section 5.1) and bounds mirror growth. A recurrence with no valid future occurrence within the expansion window (for example "every leap day") is stored as scheduled-but-unexpanded and expanded lazily when a window opens. The 2.x bug where recurrence edit desynced across devices is fixed by construction: edits rewrite the whole expansion, atomically, on both sides.

### 3.6 Two shelf scenarios

Concrete cases, written down because abstract state machines hide the edges. **Scenario one: the flight.** Dana sets a 06:15 reminder to leave for the airport, then powers the phone off overnight at 22:40. At 06:15 the device is off; nothing can fire. On power-on at 08:20, the pipeline finds the reminder past due and unconfirmed: it shelves with reason `device-off`, the Undelivered section shows "missed while your phone was off," and the digest offers re-arm at the next round hour. Dana taps it; the reminder re-enters Scheduled. Total user actions: one tap, full visibility. Under 2.x, this reminder either fired into a dead process or was rescheduled into the past on next open and dropped — the "3.1% never fired" number is mostly this scenario.

**Scenario two: the night shift.** Marcus works nights, suppresses alerts from 22:00 to 14:00, and sets a 13:30 reminder for his kid's pickup handoff. At 13:30 the attention profile is active: banner skipped, tray entry posted silently, digest inclusion scheduled. Marcus sleeps through all of it. The confirmation window passes with no acknowledgment, so the reminder shelves with reason `suppressed` — but the tray entry is still live, and when Marcus opens the phone at 14:05 the Undelivered section and the tray entry agree with each other. The design point: suppression changes the surface, never the bookkeeping. A suppressed reminder is a delivered-or-shelved reminder like any other, and the reason code tells the delivery report (and support) exactly which.

## 4. Delivery pipeline revision

### 4.1 The armed window

The device arms a system-level alarm when a reminder enters the delivery horizon: due time minus 15 minutes. Why 15 and not at-creation: arming at creation burns alarm slots on the platform quota for reminders that may be edited or completed long before they are due. Why 15 and not at-due-time: the arming step itself needs a wakeup, and arming slightly early lets the pipeline pre-resolve the delivery surface (suppression state, do-not-ring windows) without delaying the fire.

### 4.2 Surface resolution at fire time

At fire, the pipeline resolves surfaces in the same priority order as `specs/reminder-delivery-surfaces.md`: banner, tray, digest, shelf marker — but with the rework's changes: a suppressed banner goes to tray AND schedules a digest inclusion; a confirmed banner short-circuits everything else. Confirmation is receipt-based, not intent-based: the OS callback for "notification shown" counts, a tap does not (a tap is engagement, which is tracked separately for the digest report).

### 4.3 The confirmation window

After a surface fires, the pipeline waits for confirmation for a bounded period; if nothing confirms, the reminder shelves with the appropriate reason code. The window length and retry policy are quota parameters, deliberately grouped in section 5 so they can be tuned in one place.

### 4.4 Digest integration

The morning digest (07:15 local, from `specs/notification-channels.md`) gains a reminders section during the rework: shelved-since-yesterday items first (with reason codes rendered in plain language), then suppressed-overnight items, then a count of upcoming items today. The digest is assembled server-side from mirror state, which is why the mirror must exist before the digest can include reminders — this ordering drove the rollout plan in section 7.

### 4.5 What we deliberately did not build

Three tempting mechanisms were cut, and the cuts are recorded so they are not re-proposed in six months. No in-app snooze-from-notification action beyond the existing deferral ladder — the ladder in `specs/reminders-snooze.md` already owns deferral semantics and the escalation counting, and a second deferral path would split the counters. No per-reminder delivery retries configurable by the user — the retry policy is a quota parameter (section 5.3) for the same reason the sync backoff is: user-tunable retries are how batteries die. And no server-initiated wake-up attempt for `device-off` shelves beyond the digest — when a device is off, nothing we send is received, and pretending otherwise (sending pushes at power-on in burst) would recreate the reconnect-wave problem the sync team spent the spring fixing. The shelf tells the truth instead.

## 5. Quotas and limits

All tunable numbers live in this section. They were agreed at the 2026-03-02 review and validated on the internal dogfood fleet (412 devices) during April and May 2026.

### 5.1 Pending alarm quota

Each device holds at most **64 armed reminders** at once. The quota counts armed plus scheduled-within-horizon items; recurrence expansions count each occurrence separately. When a 65th reminder is created, the farthest-future armed reminder is disarmed and left in Scheduled state on the mirror only (it will re-arm when a slot frees). In dogfood, the 95th percentile of concurrent armed reminders was 11; the quota exists to bound worst-case platform behavior, not to constrain real users — no dogfood device ever exceeded 40.

### 5.2 Shelf retention

A shelved reminder stays on the shelf for **72 hours**, then auto-dismisses into the board history with a digest line noting the dismissal. Users can always dismiss earlier; auto-dismissal exists so the shelf cannot grow unboundedly on a device that is never reopened. The 72-hour figure came from the dogfood histogram: 94% of shelved reminders were handled within 48 hours, and extending to 7 days increased shelf anxiety complaints in the UX sessions without measurably improving handling.

### 5.3 Delivery retry

An unconfirmed delivery is retried **3 times** at **90-second** intervals before shelving. Retries re-resolve surfaces (the device may have been unlocked between attempts, changing suppression state). After the third failed attempt the reminder shelves with its reason code; there are no background retries after shelving, because the shelf itself is the retry surface.

### 5.4 Digest batching cap

The reminders section of a digest carries at most **30 items**; beyond that it shows the 30 oldest and a "view all N" deep link. The cap is a rendering constraint discovered in beta: digests longer than 30 lines had a 2.1% open rate versus 14% for shorter ones — an over-long digest trains users to ignore the surface, which would defeat G3.

## 6. Platform notes

### 6.1 iOS

System-level alarms use the event-based notification mechanism with a time trigger, which survives process death. iOS imposes no user-visible quota at our 64 ceiling. The one platform quirk: critical-alert-style overrides are entitlement-gated and out of scope; suppressed-reminder handling therefore always routes through the digest path. Provisional notification permission (quiet delivery until the user promotes) is treated as permanent suppression for the first 14 days after install, after which we request promotion once, contextually.

### 6.2 Android

Exact window requests replaced deferred jobs entirely (this is the 2.9.0 interim fix made permanent). On builds where the platform requires the user to grant exact-alarm permission explicitly, the funnel gains one contextual ask at first reminder creation; denial falls back to windowed scheduling with a persistent Settings card explaining the punctuality cost. The 64-armed quota maps to the platform alarm manager with room to spare. Battery validation (G5): dogfood showed +4% background wakeups per day, within budget.

## 7. Migration from 2.x

On first launch after upgrade, the client enumerates all in-process scheduled reminders and writes mirror rows for them in a single transaction, then re-arms through the new pipeline. There is no server-side migration: mirrors are created lazily from client state, which means a user who upgrades but never reopens the app keeps 2.x behavior (dead alarms) until they do — accepted, because that population is the 3.1% drop cohort and any contact with the app fixes them. Migration adds one diagnostic event and no user-visible surface; the delivery report simply appears populated.

## 8. Telemetry

Nine new events cover the lifecycle (schedule, arm, fire, confirm per surface, shelf with reason, unshelf, digest-include, auto-dismiss, quota-evict). Dashboards: punctuality (G2, target 98%), shelf occupancy distribution, digest open rate, quota pressure (p99 of armed count), and suppression-night surface mix. Weekly review in the 3.0 standup until GA; after GA, monthly.

## 9. Open questions

- Whether the "kept asking" digest section (deferral escalation, `specs/reminders-snooze.md`) should merge into the same digest section as shelved items. Tomas wants one section; Maya wants two, arguing they mean different things. Deferred to beta feedback, decision by 2026-10-15.
- Whether the 72-hour shelf horizon should shorten to 48 for boards the user has not opened in 30 days. Needs data from beta.
- Watch-face delivery for the paired wearable: platform partner docs are unclear about confirmation callbacks; spike scheduled for the 3.1 window.
