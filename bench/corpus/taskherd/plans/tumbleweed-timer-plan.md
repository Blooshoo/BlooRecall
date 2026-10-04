# Plan: the tumbleweed timer

- Owner: Priya Raghunathan, with Dmitri Vale
- Date: 2026-06-29
- Status: interim fix shipped in 2.9.0 (2026-07-06); architectural fix lands with the 3.0 reminders rework (`specs/reminders-rework-spec.md`)

## The name

Priya named it at the 2026-06-15 sync review: reminders on idle devices were "rolling in late, like tumbleweeds." The name stuck in the channel and in one support macro, so this document fixes it: **the tumbleweed timer** is the pattern of due reminders arriving 20 to 90 minutes late on devices that had been idle (screen off, app backgrounded) for several hours.

## What was happening

The Android client scheduled reminders through deferred background job windows. Deferred windows are a battery-friendly scheduler promise: "somewhere inside this window, probably." On a device that had been idle overnight, the scheduler had wide latitude, and it used it — the measured median lateness was 34 minutes, with a p95 of 71 minutes. iOS was unaffected: its event-based notification mechanism fires on time regardless of process state, which is why the ticket volume skewed 9-to-1 toward Android.

## Impact numbers (May 2026)

- 2,100 tickets in 30 days mentioning late reminders, 84% from Android.
- The worst cohort: overnight/medication reminders set for 06:00–07:00 on idle devices, where "06:00" often meant 06:40.
- One particularly quoted review: "my morning pill reminder arrived with my lunch."

## Interim fix (2.9.0, shipped 2026-07-06)

Exact window requests replace deferred windows for reminder delivery only — sync and badge work still uses deferred scheduling, deliberately, to protect the battery budget. Exact requests have their own platform permission gate on newer builds; denial falls back to deferred windows with a persistent Settings card explaining the punctuality cost. Post-ship numbers (through 2026-08-15): median lateness 6 minutes, p95 19 minutes, ticket volume down 88%.

## Why the interim fix is not the fix

Exact requests still depend on the app process being able to register them, which means a killed process with an unregistered reminder is still a silent miss — the 3.1% never-fires cohort from the rework spec's problem statement. The architectural answer is the shelf and the system-alarm pipeline in the 3.0 reminders rework: the schedule moves out of the app process entirely, and anything that cannot be delivered becomes visible instead of vanishing. The interim fix buys punctuality; 3.0 buys both punctuality and the no-silent-drop guarantee.

## Cost paid

Background wakeups per device per day rose 4% with the interim fix (within the 10% budget the team set), and battery regression complaints did not move — 11 in June, 9 in July, within noise.

## Timeline

- 2026-05-04: pattern identified in ticket clustering.
- 2026-05-27: kangaroo keyboard bug work deprioritized this one week; Dmitri's note in the client channel: "tumbleweeds after the kangaroo lands."
- 2026-06-15: sync review agreed on the exact-window interim fix.
- 2026-07-06: shipped in 2.9.0.
- 2026-09-08: superseded in the 3.0.0-beta by the full rework.
