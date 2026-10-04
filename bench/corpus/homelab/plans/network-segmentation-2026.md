# Plan — network segmentation changes for 2026

Status: accepted 2026-06-28 (household veto period passed without
incident). Written 2026-06-10. This is the plan; the reasoning lives in
`reference/network-segmentation-deep-dive.md` and the resulting quick
table in `reference/vlan-table.md`.

## What changes

1. **New VLAN 70 — the lab.** Experiments (the test resolver, the
   disposable VM host, anything with "works on my machine" energy) get
   their own segment: 10.20.70.0/24. Rule: lab can reach the internet and
   nothing else by default; anything it needs from the house gets an
   explicit allow and a note here.
2. **IoT gadgets move off the trusted wireless.** The gadget SSID now
   tags VLAN 50 (192.168.50.0/24) instead of sharing VLAN 20 with laptops.
   Motivation: the smart plugs' firmware check-ins were flooding the
   trusted segment's multicast; also the plugs do not need to see the
   printers, and after March nobody trusts what they do not have to trust.
3. **Storage VLAN stops hairpinning through the router.** Sessions
   between VLAN 20 and `bramble` used to route through `gatehouse`; with
   the switch now managed (`runbooks/switch-stack-replacement.md`), the
   storage and media VLANs interchange at the switch. Result measured
   2026-06-22: session start latency halved.
4. **The cyan visitors segment gets its own firewall alias** so its rules
   stop being copy-pasted from the trusted block. Cosmetic, but the
   copy-paste was how visitors briefly got printer access in April.

## What deliberately does not change

- The numbering scheme by decades (10s = management, 20s = trusted,
  30s = storage, 40s = media, 50s = gadgets, 60s = visitors). Renumbering
  existing segments costs more than it buys; the scheme is documented in
  the deep dive and the table, and that is the enforcement.
- `dill` stays on the management segment and answers everyone. Moving the
  resolver per-segment was considered and rejected: one resolver with
  good logging beats three resolvers with three config drifts.

## Rollout order (and what happened)

1. VLAN 70 defined on `gatehouse` and `harbor`, no rules attached
   (2026-06-29).
2. Gadget SSID re-tagged (2026-07-04). One smart plug sulked until its
   app's "rediscover" was run — the expected cost, budgeted.
3. Switch-level interchange for 30/40 (2026-07-06).
4. Cyan alias cleanup (2026-07-12).

## Verification

- From a gadget: printers unreachable, internet reachable. Confirmed with
  the hallway smart plug.
- From cyan: nothing internal reachable except the board, which is
  deliberate (house sitter card).
- Lab segment: default-deny confirmed by trying to reach `bramble` from
  the test resolver and watching the counter go up instead of the
  connection go through.

## Out of scope, deliberately

A segment for guests' gaming consoles (VLAN 45 idea) — the cyan segment
covers it and forty-five is a numbering scheme violation waiting to
happen. The answer is 60 gets a console-shaped rule if it is ever needed.
