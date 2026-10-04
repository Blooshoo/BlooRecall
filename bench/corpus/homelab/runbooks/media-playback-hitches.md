# Runbook — evening sessions hitch on the main telly

Written 2026-01-22 after the holiday week of complaints. Updated 2026-01-27
with the fix that held. This document exists because the same five-minute
conversation kept happening: the picture hitches every few minutes after
21:00 on the downstairs TV, everyone blames the internet, and the internet
is not the problem — nothing here touches the outside world during a
session.

## What it looks like

- The picture stalls for two to six seconds, recovers, and is fine for
  another three or five minutes. The spinning ring shows up on the player
  overlay, so it *smells* like a network thing, which is why this took two
  weeks to chase properly.
- It only happens on sessions started after 21:00. A lazy Sunday afternoon
  session is flawless.
- It does not happen on the bedroom panel. The bedroom panel is on wireless;
  the main telly is wired to `harbor`. You would expect the opposite.

## Root cause, as of January

Two jobs were colliding. The tuner recordings job wrote to `bramble` at
21:00 sharp (it had been scheduled against an old TV guide grid and nobody
moved it when the grid changed in November). At the same hour, sessions on
the main telly pull from `marquee`, which reads from `bramble` over the
storage VLAN. The concurrent writes pushed the pool's read latency just over
what the player tolerates, and the player stalls instead of degrading
gracefully.

## The fix

1. Moved the recordings job to 04:00 (it is in the job table,
   `reference/cron-schedule.md`). Do not move it back "just for one
   evening" — that evening will be a birthday.
2. Confirmed `marquee` is wired, not wireless, and that its switch port
   negotiated 1 Gbit, not 100. A 100 Mbit negotiation produces the same
   symptom for a completely different reason; check the port lights.
3. Left a note on the board: if hitches come back, check what else now runs
   at 21:00 before touching the network.

## If it comes back

- Reproduce with a session at 21:05 with one eye on `weathervane`'s storage
  latency tile. If the latency tile spikes in lockstep with the hitches, it
  is a contention problem again — find the new job, move it.
- If latency is flat but the picture still hitches, it is the player device
  itself; power-cycle the telly's dongle before descending into the rack.
  Once, embarrassingly, that was all it was.
