# Runbook — quarterly restore drill

Status: current. Run quarterly; last executed 2026-05-19. Next due
2026-08-19 (overdue as of this edit — the August drill became the bare-metal
exercise instead, see `runbooks/restore-from-bare-metal.md`).

## Purpose

A copy that has never been restored is a rumor, not a copy. The drill
restores a real, recent slice of data to a scratch location and measures how
long it took, so that when a drive actually dies the answer to "how long"
is a number I have seen before, not a guess.

## Before you start

- Pick a restore target with enough free space. The drill restores the
  photo library's most recent generation (~210 GB as of May).
- Do the drill from `weathervane` or any machine that is **not** `bramble`.
  Restoring on the same box that holds the originals only tests half the
  pipeline.
- Confirm the mirror went green the night before. Drilling against a stale
  generation teaches the wrong lesson.

## Steps

1. List generations and note the newest one: `restic snapshots --latest 5`.
2. In May the listing aborted with `ERR_SNAP_SEQ_118` — the sequence had a
   gap because the 03:17 job had been interrupted mid-write two nights
   earlier (the stall documented in `runbooks/nightly-mirror-stalls.md`).
   The fix is in the wrapper docs: run the index rebuild on the *offsite*
   repo, then re-list. The gap itself is not fatal, but the drill must be
   run against a generation that lists cleanly or the timing numbers are
   garbage.
3. Restore to scratch: `restic restore <id> --target /drill/scratch`.
4. Time it end to end. May's numbers: 212 GB in 1 h 41 m from the local
   repo on `bramble`, 4 h 58 m from the offsite endpoint over the evening
   uplink. The offsite number is the honest one; the local number is the
   flattering one.
5. Spot-check three files: newest photo, the household ledger spreadsheet,
   and one random file chosen by closing eyes and pointing. Open each.
6. Record the numbers in the back of the rack notebook: date, generation
   id, GB, minutes, source (local/offsite).

## Pass criteria

- Restore completes without error from the offsite endpoint.
- Spot-checks open.
- Offsite timing within 25 percent of the previous drill. A sudden doubling
  means the endpoint throttling changed or the uplink is sick — chase it
  now, not during a real incident.

## Cleanup

Delete `/drill/scratch` afterwards. Twice now the scratch copy has survived
long enough to confuse a later disk-space investigation.
