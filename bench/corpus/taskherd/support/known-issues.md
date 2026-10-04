# Known issues

- Maintainer: Tomas Lindgren
- Last updated: 2026-07-27
- Rule of thumb: if a ticket matches an entry here, the first reply links this page and nothing else. If it does not match, it gets a macro plus a personalized line.

## Open

### Badge drift after restore-from-backup

The icon count can be wrong after a restore until the first backfill pass completes. Workaround: open the app twice. Status: mitigated by the backfill pass (`specs/badge-counts.md`); permanent fix tracks with the 3.0 delivery report. Volume: about 40 user-visible cases per week as of 2025-12, 80% restore-related.

### Stale member avatars after role changes

Avatars on a board member list can show the old image for up to an hour after an owner promotes or demotes someone. Cause: the avatar cache keys on user ID only. Workaround: none needed; it self-heals. Fix scheduled in the 3.0 train. Volume: 12 tickets in June.

### Link preview cards render as plain text

URLs pasted into task descriptions lose their preview card when the description was edited while the device had no connection; the preview fetch never retries. Workaround: re-save the task while online. Fix candidate for 3.1, unowned as of this writing. Volume: 6 tickets in June.

### Late reminders on idle devices (mostly Android)

Reminders arriving tens of minutes late after the device has been idle overnight. The interim fix shipped in 2.9.0 (2026-07-06); median lateness is down from 34 minutes to 6, and the architectural fix is the 3.0 reminders rework. Ticket volume down 88% since ship. First-reply: link this entry, mention the 2.9.0 fix, and ask for the device model if the user is still on 2.8.

## Closed

### Composer hop on first keystroke (Android)

Fixed in the June Android patch (2.8 line). See `plans/kangaroo-keyboard-bug-plan.md` for the full history; support replies now link that plan instead of the old channel thread. Residual reports: 4 per day, all on the two wide-gesture launcher builds, tracked separately.

### First launch slower after the May update

Expected one-time store conversion; closed as works-as-intended with the first-launch macro as the standing reply. Volume at peak: 28 tickets in the patch week.
