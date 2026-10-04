# Firmware inventory

Status: checked 2026-08-12. This is the "what is running where" card.
Rule: exact version strings for an upgrade live in that device's runbook;
this file only tracks that the check happened and what to re-check next.

| Device | What runs | Last checked | Notes |
|---|---|---|---|
| `gatehouse` (edge router) | router firmware **9.9.4-p2** (2026-06-02) | 2026-08-12 | p2 was a stability release; the auto-update toggle stays off |
| `bramble` (NAS) | appliance firmware — current stable, upgraded 2026-05-17 | 2026-08-12 | exact string and procedure in `runbooks/nas-firmware-upgrade.md`; post-upgrade scrub clean |
| `harbor` (switch) | switch OS — upgraded during the June migration | 2026-08-12 | version and migration notes in `runbooks/switch-stack-replacement.md` |
| `dill` (resolver) | resolver package from the distro repo, auto security updates | 2026-08-12 | config is version-controlled; package updates are not pinned |
| `marquee` (media box) | media server release, current stable | 2026-08-12 | upgraded 2026-08-04, session regression none |
| TV dongle | vendor firmware **6.2.1-build7**, auto-update ON (not fightable) | 2026-08-12 | auto-updates once broke passthrough; the preset survives it now |
| Tuner PC | tuner driver **1.1.7** (frozen) | 2026-08-12 | newer driver dropped the analog fallback; frozen on purpose |
| UPS brick | firmware not readable (no network card, label gone) | 2026-08-12 | status via USB only; see `plans/ups-replacement-eval.md` |
| PoE injector (upstairs run) | none (dumb) | 2026-08-12 | browns out above 30 °C — known, see `runbooks/vlan-troubleshooting.md` |
| Mesh node (upstairs) | AP firmware, auto-update ON | 2026-08-12 | the January auto-update re-picked the channel; channel is pinned now |

## Auto-update policy, such as it is

Fights are picked carefully: things that can break sessions invisibly
(router, switch, NAS, tuner) are manual. Things that sulk visibly
(dongle, AP) are auto, because their vendors force it anyway and the
failure mode is a bad evening, not data loss. The freezer list is the
"notes" column above; anything not listed as auto is manual, and the
manual ones only move during the window rules in the respective runbooks.
