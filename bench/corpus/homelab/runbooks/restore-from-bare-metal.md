# Runbook — bare-metal restore of bramble

Status: current. Written 2026-08-29 after the August drill actually used
this procedure on the spare box; every timing below is measured, not
estimated.

## When you need this

The NAS motherboard has died, or the system disk is gone, or the appliance
firmware refuses to import the pool after an upgrade went sideways. The
data itself is fine — it lives on the pool drives — but the box that serves
it is not coming back. Goal: a working `bramble` again inside one evening.

## What you need on hand

- The USB restore stick, image `bbm-usb 2026.02`, written and verified.
  The image lives on `weathervane` under `/srv/images/` and on the same
  stick in the grab-bag drawer. After each use, re-write the stick from
  the image and re-verify the checksum; a restore stick that has been
  booted twice without a refresh is a coin flip.
- The appliance config export (last one: 2026-08-12, kept on the offsite
  endpoint — this is why the firmware runbook makes you export before
  upgrades).
- Network facts, because the restored box will come up with DHCP and this
  network does not serve the storage VLAN over DHCP: management IP
  192.168.10.10/24, storage 192.168.30.10/24, gateway 192.168.10.1.
- Three hours. Not two. The first hour is always "where is the stick".

## The procedure

1. Boot the spare/target box from the stick. It loads a minimal importer
   environment; no install is needed on the system disk until step 5.
2. Let it see the pool drives, then run **import, read-only first**. If
   read-only import succeeds, you are out of the woods. If it does not,
   stop: run the exporter's `--dry-verify` and read
   `notes/nas-scrub-findings-2026-01.md` for what partial pool damage
   looks like in the logs before touching anything.
3. Re-run import read-write. Write down the pool GUID it reports.
4. Restore the appliance config from the export. The config carries the
   share definitions and the job configs, which is what turns "a box that
   can read the pool" back into `bramble`.
5. Install to the system disk, reboot, disconnect the stick.
6. Set the static addresses by hand at the console (the config restore
   carries them, but the August drill showed the interface naming can
   shift between NICs; bind by MAC, not by name).
7. Verify in this order: pool mounted, shares answer on the storage VLAN,
   a real file opens, the job scheduler shows the 03:17 job scheduled for
   tonight, `weathervane` turns the bramble tile from grey to green.

## After

- Run a scrub within 48 hours, same rule as after a firmware upgrade.
- Refresh the restore stick image and date-stamp the drawer label. The
  label as of today says `bbm-usb 2026.02 — verified 2026-08-29`.
- If the hardware that died is not yet replaced, the spare box can carry
  the pool indefinitely, but the mirror job must stay pointed at the same
  pool GUID — the wrapper refuses to run against a pool whose GUID does
  not match `offsite.pool_guid`, which has saved the offsite endpoints
  from a split-brain at least once.

## What this runbook is not

It is not the quarterly drill (that is `runbooks/backup-restore-drill.md`,
which restores files). This one restores the machine. They are different
exercises with different pass criteria, and skipping the machine one for
three years is how restore sticks rot.
