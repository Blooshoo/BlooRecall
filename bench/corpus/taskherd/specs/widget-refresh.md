# Home screen widget

- Author: Dmitri Vale
- Date: 2026-09-14
- Status: active

## Home screen widget

The panel on the home screen shows the 12 highest-priority open items across pinned boards: overdue first, then due today, then pinned stars. It is read-only; tapping any line deep-links into the board at that task.

### Refresh cadence

While taskherd is backgrounded, the data on the board is re-pulled at most every 15 minutes, and never more than once per interval even if several boards change underneath it. Opening the app forces an immediate pull and drains any pending update before the first frame. A manual pull-to-force from the panel's own overflow menu is rate-limited to one per minute so it cannot be used to hammer the sync engine.

### Manual pinning

Pinned boards are chosen in the app, not on the board surface itself, because the OS picker we get for free does not expose selection UI reliably across builds. Pin state syncs with the account, so a new phone restores pins on first sign-in. Maximum 4 pinned boards; the picker disables the fifth.

### Sizing and content caps

Two sizes ship. The small size shows 3 lines; the large shows 12. Content beyond the cap is truncated with a "+N more" footer that deep-links to a filtered board view. Text is single-line, ellipsized; we do not wrap, because wrapped text broke 6 of 11 launcher builds in the 2026-08 compatibility sweep.

### Battery and budget

All scheduled pulls go through the shared background budget described in the cold-start audit's follow-up (`plans/cold-start-audit-final.md`); the board surface is allowed 2 pulls per budget window and yields the rest to sync.
