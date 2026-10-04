# Runbook — NAS firmware upgrade

Status: current. Written 2026-05-17 before the May patch window; both steps
of this exact procedure were followed and the upgrade went clean.

## Scope

This covers firmware on `bramble` only — the storage appliance itself, not
the drives and not anything running on top of it. Drive firmware is checked
at purchase and otherwise left alone; the appliance firmware is what this
runbook exists for.

## Before

1. Check the pool scrub status: it must show **clean** and have completed
   within the last 14 days. Do not upgrade on a pool that has never been
   scrubbed or has pending errors. If the scrub is dirty, stop and read
   `notes/nas-scrub-findings-2026-01.md` for what a dirty scrub turned into
   last January.
2. Export the appliance configuration (web panel → *System → Config →
   Export*). Save it somewhere that is not `bramble`. The offsite endpoints
   are fine; it is 400 KB.
3. Confirm no job from `reference/cron-schedule.md` fires in the next two
   hours. The upgrade reboots the box twice; a job landing mid-reboot is
   how the April mirror got wedged.
4. Write down the current version. In May it was nas-firmware 3.18.2, and
   the target was the 3.19 line. Knowing the exact source version matters
   because the 3.18→3.19 upgrade migrates the pool metadata and the
   migration is one-way.

## The upgrade

1. Upload the image through the web panel. Do not use the "auto-update"
   toggle; it applies whatever is newest whenever it wants, which is the
   opposite of "during a window I chose".
2. Start the upgrade. First reboot: 6–8 minutes. The panel goes
   unresponsive around minute 3 — this is normal, do not power-cycle it.
   The single worst thing you can do to this box is interrupt its first
   boot after a metadata migration.
3. Second boot happens automatically after the migration step. Total
   elapsed in May: 19 minutes door to door.
4. Log in, confirm the version string, and let the pool import settle. The
   web panel shows a yellow "pool importing" banner for a few minutes;
   services start after it clears.

## After

1. Re-run a scrub within 48 hours of the upgrade. This is not paranoia;
   the metadata migration is exactly the kind of event a scrub is designed
   to catch collateral damage from.
2. Re-enable and confirm the nightly mirror went green the following
   morning before declaring victory.
3. Update `reference/firmware-inventory.md`.

## Rollback

There isn't one across the metadata migration, which is why the pre-checks
exist. Within a minor revision (say 3.19.x → 3.19.y) the panel keeps the
previous image and can boot it from the boot menu.

## History

- 2026-05-17 — clean upgrade, 3.18.2 → 3.19.1. Post-upgrade scrub clean in
  4 h 12 m, mirror green next morning.
