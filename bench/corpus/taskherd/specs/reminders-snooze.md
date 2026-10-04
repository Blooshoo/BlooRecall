# Reminders — deferral behavior

- Author: Maya Okafor
- Date: 2026-09-21
- Status: active

## Reminders

A reminder fires on its due surface at its due time. When the user defers it, the deferral ladder in this spec applies. Deferral is always user-initiated; the system never defers on its own.

### Scheduling

The default deferral adds 10 minutes. The picker offers 10 minutes, 1 hour, this evening (18:00), and tomorrow (09:00). Each deferral re-enters the normal scheduling pipeline and counts as a fresh schedule, so a deferred reminder behaves exactly like a newly created one on its new time — same surfaces, same suppression rules.

### Snooze escalation

After the third deferral in a row, the bell stops: no further alerts fire for that item on any surface, and the item is surfaced in the weekly digest instead, under a "kept asking" heading. The count resets when the item is completed, edited, or moved to another board. The weekly digest goes out Mondays at 08:00 local and lists escalating items with the board name and how many deferrals accumulated (capped display at 9).

### Digest integration

Escalated items leave the digest once handled. If the board is deleted while items are escalated, the digest entry says "board removed" rather than vanishing silently, so the user knows why the line disappeared. Roughly 1,200 items per week reach the third-deferral cutoff across the fleet (2026-08 average); 60% of those are completed within two days of appearing in the digest.
