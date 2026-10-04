# Runbook — switch replacement (harbor)

Status: current. Written 2026-06-14 during the actual migration; every
misstep below happened exactly once.

## Why the switch was replaced

The old unmanaged 5-port unit under the stairs was never meant to carry the
storage VLAN, and after the March loop incident
(`notes/incident-review-2026-03-09-vlan-flap.md`) it was clear it had to go.
The replacement is a managed 8-port unit, model **MSW-8G-CL**, mounted in
the rack, hostname `harbor`.

## Before

1. Photograph the old switch's cabling. Photograph it again from the side
   so port order is unambiguous. The photo from step 1 was the only reason
   step 7 in "The migration" below was recoverable.
2. Note which runs are which: wall plate upstairs (media/40), wall plate
   downstairs TV (media/40), `bramble` (storage/30 + management/10 tagged),
   `gatehouse` trunk (everything), spare to the office (20).
3. Pre-configure the new unit offline, before it touches a single cable:
   - Management IP 192.168.10.7/24.
   - Ports 1–4: trunk, tagged 10/30/40/60.
   - Port 5: access 40 (downstairs TV).
   - Port 6: access 30 (`bramble` storage).
   - Port 7: access 20 (office spare).
   - Port 8: access 10, unused for now.
   - Spanning tree on, storm control on (see `runbooks/vlan-troubleshooting.md`).
4. Upgrade the new unit's OS *before* the migration, not after. The unit
   shipped with sw-os 2.3.7 and the port-isolation settings only behave on
   sw-os 2.4.9; upgrading in place mid-migration means re-verifying
   everything twice.

## The migration

1. Unplug the trunk to `gatehouse` last, plug it into the new unit first,
   once ports are configured. Trunk first means everything else comes up
   with a working uplink.
2. Move `bramble` next (storage VLAN, port 6). Confirm the pool is
   reachable from `weathervane` before moving anything else.
3. Move the wall-plate runs.
4. If a port refuses to pass traffic, check its negotiation first. Port 5
   sat at `ERR_PORT_NLPU_31` for ten confusing minutes; the cause was the
   dongle behind the TV wanting 100 Mbit half-duplex, and the port policy
   set to autonegotiate-only. Setting the port to advertise 10/100/1000
   cleared it.
5. Leave the old switch unplugged for a week before it goes to the e-waste
   pile in the garage. Twice in this household the "old broken thing" was
   back in service inside a month.

## Verification

- All four VLANs pingable from `weathervane`.
- TV session plays; `bramble` reachable from the office.
- Storm-control counters zero after 24 hours.

## History

- 2026-06-14 — migration done in 90 minutes, mostly because of the photo.
  Take the photo.
