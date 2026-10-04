# VLAN quick table

Status: current as of 2026-06-28 (post-2026-segmentation-plan). The long
reasoning lives in `reference/network-segmentation-deep-dive.md`; this is
the card that goes in the rack door pocket. If this table and the deep
dive ever disagree, check the live config on `gatehouse` and fix whichever
document is wrong.

| VLAN | Name | Subnet | Purpose | Notes |
|---|---|---|---|---|
| 10 | mgmt | 192.168.10.0/24 | Management interfaces, `gatehouse` (.1), `dill` (.53), `weathervane` (.60), `harbor` (.7), `bramble` mgmt (.10) | Where the truth lives |
| 20 | trusted | 192.168.20.0/24 | Laptops, phones on the amber SSID, office runs | Full internal access |
| 30 | storage | 192.168.30.0/24 | `bramble` (.10), the cold-dock when plugged in | MTU 9000 switch-side; no internet needed |
| 40 | media | 192.168.40.0/24 | `marquee` (.20), TV, dongle, projector, tuner PC | Eastbound traffic: reads from 30 only |
| 50 | gadgets | 192.168.50.0/24 | Smart plugs, smart displays, anything with an app | Internet + broker only, no printers |
| 60 | cyan | 192.168.60.0/24 | Visitors on the cyan SSID | Internet + board + printer, capped 20/5 |
| 70 | lab | 10.20.70.0/24 | The lab: test resolver, disposable VM host | Default-deny to the house; internet yes |
| 99 | transfer | 192.168.99.0/24 | Uplink/transfer lane between `gatehouse` and the cabinet switch | No clients, no DHCP |

## Rules that surprise people

- The storage VLAN (30) has no default route on purpose. If something on
  it asks for the internet, that thing is misconfigured.
- The media VLAN can read storage but cannot write it; writes go through
  the services on `bramble` itself, which keeps the panels happy.
- Cyan reaches the board and the printer and nothing else. Both are
  deliberate (house-sitter card, boarding-pass printing).
- VLAN 70 has exactly one allow rule per resident service, each with a
  line in the segmentation plan. No allows "to test".

## Numbering scheme

Decades: 10s management, 20s trusted, 30s storage, 40s media, 50s
gadgets, 60s visitors, 70s lab, 90s spare. New segments take the next
free decade, never a "clever" number. See `reference/naming-conventions.md`
for the naming side of the same argument.
