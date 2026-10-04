# Plan — media box relocation (2026 edition)

Status: current. Replaces `plans/media-server-relocation-2025.md`, which is
kept for the record. Written 2026-06-20; execution targeted for the
September long weekend, cable work first.

## Idea

Reverse the 2025 decision: `marquee` goes back to the basement rack, and
the TV-side problem is solved with a proper HDMI run instead of proximity.

## Why reverse it

The 2025 move traded a cable problem for three worse ones: wireless into a
wooden cabinet, heat with nowhere to go, and dust. The box was always a
rack citizen; the cabinet experiment was cheap to try and cheap to undo,
which was the point of writing the 2025 plan down at all.

## Plan of record

1. **Cabling first** (the long-lead item): drill the two-hole path from
   the rack to the TV wall plate and pull:
   - HDMI over a pair of baluns on the existing spare Cat6 run (tested
     2026-06-21 at 4K/60 with no dropouts over one evening).
   - One spare Cat6, for the day the baluns die.
   Cable work happens the weekend of 2026-09-05; parts already on the
   `plans/shopping-list-q3-2026.md` list.
2. **Move the box** to rack slot 3, on the shelf above `harbor`, feet on
   the rubber pads (the one good idea from 2025).
3. **Networking**: wired, port 1 on `harbor`, tagged onto VLAN 40. No
   wireless, ever, for this box — that sentence goes in the plan so
   future-me reads it before "temporarily" putting it on wireless for one
   evening, which is how the 2025 mess started.
4. **Cabinet cleanup**: the receiver and the TV dongle stay in the
   cabinet; everything else comes back to the rack. Dongle keeps using the
   low-light preset (`runbooks/media-transcode-preset.md`).
5. **Verification evening**: full session on the main telly at 21:00 with
   a recordings job running against the pool. If that evening is clean,
   the relocation is done; if not, latency first, network second, box
   last, in that order (see `runbooks/media-playback-hitches.md`).

## Risks

- The wall path may hit a fire block; if the drill binds, stop and
  reassess rather than forcing it. Fallback: surface-mount raceway along
  the stair closet, which is ugly but has been pre-approved by the
  household.
- Baluns add one more powered thing in the cabinet — they go on the
  receiver's switched outlet so they cannot sit on overnight.

## Out of scope

The projector. It keeps its direct HDMI to `marquee` via the existing
wall plate and does not move in this plan.
