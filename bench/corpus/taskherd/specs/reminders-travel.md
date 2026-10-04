# Reminders across region changes

- Author: Maya Okafor
- Date: 2025-12-01
- Status: active

## Scope

What happens to scheduled reminders when the device reports a UTC offset that differs from the one the reminder was scheduled under — landing in a new region, a long stay abroad, or a daylight-saving jump at home. This spec covers scheduling only; delivery surfaces are covered in `reminder-delivery-surfaces.md`.

## The 8-hour rule

When the device reports a new offset, reminders due within the next 8 hours keep their original wall-clock target: a reminder set for 09:00 old-local still fires at what 09:00 old-local translates to in absolute time. This protects the common case of a red-eye landing at 07:20 with a 09:00 boarding reminder — the reminder must not silently slide to 09:00 new-local, which would be four hours late for the flight.

## Re-anchoring beyond 8 hours

Reminders further out than 8 hours re-anchor to the new locale by daypart:

- Morning reminders (05:00–11:59 old-local) move to 08:30 new-local.
- Afternoon reminders (12:00–16:59) move to 13:00 new-local.
- Evening reminders (17:00–21:59) move to 19:00 new-local.
- Anything scheduled 22:00–04:59 keeps its exact clock time in the new locale (rare; usually medication).

All-day items follow the calendar day of the new locale, whatever the offset does to the boundary.

## Daylight-saving jumps at home

A DST transition is treated as a region change with the same rules, except that the 8-hour rule becomes a 2-hour rule: reminders within 2 hours of the jump keep absolute time, the rest keep wall-clock time (a 07:00 alarm stays 07:00 across the jump). This matches what participants told us in the 2025-11 survey: 84% expected wall-clock stability for far-out reminders and absolute stability for imminent ones.

## Device clock tampering

If the offset changes by more than 13 hours in a single step, we treat it as a clock glitch, not a move: reminders are untouched and a one-time diagnostic event is logged. Support clears the glitch flag with the follow-up procedure attached to the sync-backlog macro in the support library.

## Telemetry

Re-anchor events run about 90,000 per week in summer. Complaint rate post-change (2025-12 to 2026-02): 6 tickets total, all from the medication daypart, which we now document prominently in Settings.
