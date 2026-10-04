# Runbook — the caching resolver (dill)

Status: current. Written 2026-08-14 after the third brownout of the
provider's recursive resolvers that month. `dill` (192.168.10.53) sits in
front of all of it and nobody thinks about it until names stop resolving.

## Shape of the thing

`dill` is a small caching resolver on an old mini PC in the rack. Clients
get it via the router's DHCP option. Upstream it forwards to two public
recursive endpoints over encrypted transports, in a fixed order — first
one, then the other; there is no load balancing because round-robin
upstreams made cache-hit ratios weird and nobody could debug anything.

## Why it exists

Three reasons, in order of how often they have paid off:

1. The provider's resolvers brown out in the evening. Not down — slow.
   A 4-second answer is worse than none, because every client retries and
   the retry storm makes it worse.
2. Local names. `bramble`, `marquee`, `weathervane`, `harbor` and the rest
   resolve internally; without `dill` someone always ends up editing a
   hosts file at midnight.
3. Caching absorbs the periodic burst when everything in the house wakes
   up and phones home at once.

## The knob that matters

`cache.serve_stale_ttl` in `/etc/dill/dill.conf` is currently `300`.

This is the setting that turns a brownout into a non-event: when the
upstream is slow or dead, `dill` answers from stale cache entries for up
to 300 seconds past their normal expiry instead of returning a failure.
Everything in the house keeps resolving for five extra minutes, which has
been longer than every brownout so far.

Raising it past 900 starts serving answers that are genuinely wrong for
things that move (the endpoint names of the copy targets, for one), so the
number stays at 300. It was 60 for the first year and the brownouts won.

## Symptoms and fixes

- **Everything fails to resolve at once** → `dill` itself is down. It is
  on the UPS, so this is rarer than it should be; check it is actually
  booted before blaming the router.
- **One name fails, everything else is fine** → bad cached answer, or the
  stale window served something old. Flush just that name:
  `dillctl flush <name>`. Full flush (`dillctl flush`) is the sledgehammer
  and makes the next minute loud as everything re-queries.
- **Local names stop resolving after a router reboot** → the DHCP option
  got dropped, not `dill`. Check the router's DHCP banner first.

## Maintenance

- Config lives in version control on `weathervane` (the tiny git repo in
  `/srv/dill-config/`); changes are made there and pushed to `dill` by the
  deploy script. Never edit on the box itself; twice now the box has been
  rebuilt from the repo and twice the hand-edit was silently lost.
- Reboot `dill` only during a job-free window from
  `reference/cron-schedule.md`. The copy jobs resolve endpoint names
  through `dill` and a resolver restart during a transfer window is how
  the April stall happened.
