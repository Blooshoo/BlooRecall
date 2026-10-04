# Review — does the copy pipeline still meet 3-2-1?

Status: current. Written 2026-04-29 as the annual sanity check of the
whole pipeline against the 3-2-1 rule (three copies, two kinds of media,
one offsite). Verdict: **yes, with two filed gaps.**

## The three copies

1. **Live data** on `bramble`'s pool. Not a backup, but it is where the
   three hours of nightly generation deltas come from.
2. **Local generations** on the USB dock's cold drive, synced weekly.
   Updated Sundays after verification; verified quarterly by the drill in
   `runbooks/backup-restore-drill.md`. This copy exists for "the pool ate
   something" scenarios, which are rare but not hypothetical.
3. **Offsite generations** on the two endpoints, rotated per
   `runbooks/offsite-rotation-v2.md`. Newest generation is never more than
   one cycle old.

## The two kinds of media

Pool drives plus a USB cold copy: different devices, different failure
modes, same building. The rule is satisfied on paper. Honest caveat: the
"two kinds" protection is weakest against the house-level events (theft,
fire, the furnace room flooding) — that is exactly what the offsite
endpoints exist for, and they are a different building and a different
operator.

## One offsite

Satisfied, twice over. The rotation scheme makes it effectively two
independent offsites, which is more than the rule asks.

## Gap 1 — no immutable generation anywhere

Every copy can currently be altered by the same credentials. An immutable
bucket on one endpoint (object-lock, even a 7-day window) would close the
"bad actor or bad script deletes everything" class. Deferred twice now
because the endpoint that supports it meters egress, and the immutable
window interacts weirdly with the prune grace window
(`runbooks/prune-and-retention.md`). Filed, not forgotten. Target: decide
by the next annual review.

## Gap 2 — the cold drive sync is manual-adjacent

"Synced weekly" depends on someone (me) plugging the dock in on Sundays.
It has missed four weeks this year, each caught by the green-streak alert
on the board. Options: automate via the rack shelf and a cron entry (adds
a always-spinning device), or accept the manual step and keep the alert.
Current lean: accept it, document the catch-up procedure
(plug in, run the sync, confirm the tile) so anyone in the household can
do it, not just me.

## What was checked and passed

- Restore drill numbers current (May).
- Both endpoints listed a consistent generation within the last 7 days.
- Encryption keys recoverable: the vault entry `homelab/core` has the
  recovery phrases and the offsite account recovery codes, and the vault
  itself has a tested paper fallback in the fire safe.
- The grab-bag drawer has one verified restore stick
  (`runbooks/restore-from-bare-metal.md`).
