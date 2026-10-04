# Job schedule — the cron card

Status: current as of 2026-08-22, when this card became the single source
of truth. Before that, job times were scattered across runbooks and two of
them disagreed; this file wins any argument. All times UTC, all on
`bramble` unless noted.

| Cron | Job | What it is | Runbook |
|---|---|---|---|
| `17 3 * * 1-6` | nightly-mirror | Pushes the newest generation to the offsite endpoint. Tue–Sat because Sunday is the verify day and the cold-dock sync owns Monday's early morning. | `runbooks/nightly-mirror-stalls.md` |
| `41 4 * * 0` | weekly-verify | Reads back a 10 percent sample of the newest generation against each endpoint. | `runbooks/snapshot-verify-weekly.md` |
| `11 4 * * *` | tuner-recordings | Writes the scheduled recordings to the pool. Moved here from 21:00 in January — see the hitches runbook for why 21:00 is cursed. | `runbooks/media-playback-hitches.md` |
| `33 6 * * 0` | cold-dock-sync | Syncs the weekly local copy to the USB dock. Manual-adjacent: fires only if the dock is mounted; the green-streak alert catches the weeks it is not. | `plans/backup-321-review.md` |
| `0 9 2 * *` | ups-selftest | Runs the brick's monthly self-test on the 2nd at 09:00. | `runbooks/ups-maintenance.md` |
| `30 22 25 * *` | monthly-scrub | Pool scrub, 25th at 22:30 so it finishes before the mirror window. Durations: ~4 h normal, up to 6 h on a fat month. | `notes/nas-scrub-findings-2026-01.md` |
| `0 5 1 * *` | thumbtrim | Trims the media thumbnail cache on the 1st. New since the August capacity note. | `notes/pool-capacity-headroom.md` |
| `0 14 * * 5` | swamp-check | A calendar nudge, not a job: "look at the evaporative rig" on Fridays during its season. Runs on the wall calendar and the board; the cron entry only fires the board nudge. | `notes/basement-swamp-cooler-hack.md` |

## Window rules (the part that actually matters)

- **Nothing new lands between 03:00 and 05:00.** The mirror owns that
  window; resolver restarts, switch work, and router reboots inside it
  are how the April stall happened.
- **Rotation starts after verify's window closes.** The 04:41 verify and
  a rotation inside its checksum gate reading the same generation is the
  one documented false-amber; the gap between them is the protection.
- **Scrub and firmware upgrades never share a weekend.** Both want the
  pool quiet; the upgrade runbook's 48-hour post-scrub rule and this line
  are the same rule stated twice.
- **Cron edits happen on `weathervane`'s config repo and deploy from
  there**, same discipline as the resolver config. Hand edits on the box
  die with the next rebuild.

## Historical oddities, kept so they are not re-litigated

- Why 03:17 and not 03:00? The original schedule was set in 2023 to land
  after a provider's midnight throttle lifted, and the seven minutes were
  fine-tuning against the evening session tail. Nobody remembers the
  exact measurement. It works; it stays.
- Why 41 past the hour for verify? No reason. It was 40 in a draft, a
  typo made it 41, and the typo is now load-bearing.
