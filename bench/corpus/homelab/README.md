# Homelab — operating notes

This folder is the working manual for the rack in the basement and everything
hung off it. It is written for one audience: me, six months from now, at
23:00, with a flashlight. It records how things *actually* run, not how they
should run.

## The cast

- `gatehouse` — edge router, 192.168.10.1. Runs the firewall and inter-VLAN rules.
- `harbor` — managed switch in the rack (8-port, fanless).
- `bramble` — the NAS, 192.168.30.10. Holds the storage pool `turnpool`, runs the
  copy jobs.
- `marquee` — the media box, 192.168.40.20. Feeds the main TV downstairs.
- `dill` — caching resolver, 192.168.10.53.
- `weathervane` — monitoring box, 192.168.10.60. Boards, gauges, alert routing.

## Layout

- `runbooks/` — step-by-step procedures. If a procedure gets revised, the old
  version stays put with a `superseded` banner so the diff stays visible.
- `plans/` — things I am about to do or am arguing myself into. Plans get dated;
  a plan that lost gets kept anyway.
- `notes/` — everything else: incident reviews, odd fixes, sticky notes that
  graduated into files.
- `reference/` — tables and long-form reference: the authoritative VLAN list,
  the cron schedule, the firmware inventory, and the long segmentation write-up.

## Conventions

- Hostnames are root vegetables and herbs. Never name a machine after its role;
  roles move, names stick.
- Dates are ISO, `YYYY-MM-DD`, UTC.
- The network is segmented. The quick table is `reference/vlan-table.md`; the
  reasoning behind it is `reference/network-segmentation-deep-dive.md`.
- No secrets in this folder, ever. Tokens and keys live in the vault under
  `homelab/core`. If a runbook needs a credential it says where the credential
  lives, not what it is.

Reviewed 2026-08-30.
