# Notes — quirks of the cyan SSID

Written 2026-02-20 after the spring crop of house callers. Everything
below concerns the cyan SSID (VLAN 60, 192.168.60.0/24) — the one
visitors get told about, the one with the fridge magnet.

## Guest network

## Guest network — Isolation rules

Visitors land in a segment that can reach the internet and exactly two
internal things: the household board (deliberate — the house-sitter card
points there) and the network printer, because "can I print my boarding
pass" is a real and recurring request. Everything else — `bramble`, the
media box, the management segment — simply does not answer. The rules are
a dedicated firewall alias as of the 2026 segmentation plan; before that
they were a copy-pasted block, which is how the printer briefly became
world-readable in April (fixed, and the alias exists so it stays fixed).

### Bandwidth cap

The segment is capped at 20 Mbit downstream, 5 up. This sounds mean and
has never once been noticed: the cap exists so that one visitor's
operating-system update cannot eat the evening uplink while someone else
in the building is on a video call. The cap applies per client, not per
segment.

### Lease quirks

The cyan segment hands out leases from a pool of 30, and a stale lease
can block a new arrival when the pool is tight (long-staying visitors'
devices parking on leases after they leave). The evening renewal usually
clears it; the manual fix is in the router's lease table, expiring the
dead lease by hand. Worth knowing before re-cabling anything: "new device
cannot get an address on cyan" is a lease problem nine times out of ten
and a radio problem never.

### The one rule visitors must be told

Cyan is for the length of a stay, and the passphrase rotates with the
seasons (it lives in the vault under `homelab/cyan`, not in this note).
The rotation means the fridge magnet with the old phrase on it is wrong
twice a year, and someone always tries it first.
