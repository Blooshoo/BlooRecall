# Notes — why handsets lose the wireless at 19:00

Written 2026-02-16 after a month of intermittent complaints. Every
evening around 19:00, the handsets and the small portable clients would
disassociate from the 2.4 GHz radio for 20–30 seconds, sometimes
mid-call, then come back on their own. No pattern by device make; the
wired things were never affected.

## What it was not

- Not the AP dying: the 5 GHz radio on the same unit stayed up and served
  the same devices fine when pinned to it manually.
- Not the resolver: sessions that survived the disassociation kept
  flowing; only association broke.
- Not interference from the microwave: the kitchen runs on a different
  circuit of the evening than the complaints did, and the timing followed
  human schedules, not appliance ones.

## What it was

Channel 6 congestion, self-inflicted with a helping hand from the
neighbors. Three things stacked:

1. The mesh node upstairs had drifted onto channel 6 (same as the main
   AP) after its firmware auto-update in January. Two APs on one channel
   is bad; two APs on one channel *and* the neighbor's unit also on
   channel 6 is worse.
2. The 19:00 spike was simply occupancy: everyone settles into the same
   two rooms at that hour, and the band survey showed airtime utilization
   hitting 90 percent.
3. Legacy rates were still enabled, so every re-association negotiation
   crawled at old slow modulations and dragged the channel busy longer
   than it needed to be.

## The fixes (all held since February)

- Pinned the mesh node to channel 11 and disabled auto-channel on both
  units. Auto-channel re-picked "least busy at 04:00", which is exactly
  when the evening problem is invisible to it.
- Disabled legacy rates: minimum basic rate set to the middle OFDM rate,
  so associations negotiate modern modulations only. The one ancient
  gadget that could not cope was due for retirement anyway and moved to
  the gadget segment's own SSID.
- Moved everything with a power cord onto wired where a run existed. The
  two smart displays in the kitchen were the last holdouts and are now on
  the gadget SSID (VLAN 50 per the 2026 segmentation plan).

## What to check first next time

Airtime utilization at the complaint hour, then channel overlap. It has
been, in order: channel overlap (this note), a dying AP power supply
(2024), and one memorable week where the cordless base station next to
the upstairs node was the culprit. The base station moved; the AP supply
was replaced; the channel plan is written on the inside of the rack door.
