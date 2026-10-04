# Naming conventions

Status: stable since 2025-09-14, imported from the old notes and unchanged
since. This file exists so naming arguments happen once.

## Hostnames

- All machines are named after **root vegetables and herbs**, in no
  particular order, chosen by whoever racks the box: `bramble`, `dill`,
  `harbor` (the one exception, named by the previous owner of the case
  and grandfathered), `marquee` (grandfathered, it predates the scheme),
  `weathervane`, `gatehouse`.
- The rule underneath the whimsy: never name a machine after its role.
  Roles move. `bramble` has been a file server, then a hypervisor, then a
  NAS. A box named `nas1` would have needed renaming twice. Names stick;
  DNS entries follow the machine, not the function.
- New machines take any name that is not already used and not
  embarrassing to say out loud to an electrician. `parsnip` and `sorrel`
  are reserved for the next two additions because deciding later is how
  you end up with `new-nas-2`.

## Networks and VLANs

- Segments number by decade, function per decade, as recorded in
  `reference/vlan-table.md`. New segment = next free decade. Never a
  "clever" number; clever numbers are how you get two VLAN 5s.
- Subnets follow the VLAN: VLAN 20 is 192.168.20.0/24 without exception.
  The lab segment breaks the 192.168 pattern on purpose (10.20.70.0/24)
  so that a lab route leaking into a client is instantly recognizable.

## Files and documents

- Dates are ISO `YYYY-MM-DD`, UTC, everywhere, no exceptions. Two-date
  formats in one tree is how "which backup ran" arguments start.
- Runbooks: `runbooks/<thing>.md`. A revised runbook becomes
  `<thing>-v2.md` and the old file stays with a superseded banner — old
  versions are diff material, not garbage.
- Plans get the year in the name when they are time-boxed
  (`plans/media-server-relocation-2026.md`); undated names are for
  living documents.
- Notes are named for what you would grep for at midnight
  (`notes/pool-capacity-headroom.md`), not for when they were written.
  Dates go inside, in the first three lines.

## The one meta-rule

When a convention costs more than it saves, change the convention and
write down why here. The scheme serves the household; it is not a hobby
of its own.
