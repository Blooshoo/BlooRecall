# Runbook — VLAN and switch misbehavior

Status: current. Written 2026-03-15, six days after the bridge-loop
incident, because the next occurrence should take ten minutes instead of an
evening.

## The one error that matters

When `harbor` (or anything upstream) logs `ERR_BRIDGE_LOOP_77`, stop
reading logs and start walking cables. That code means the switch has
detected a Layer-2 loop — the same frames arriving on more than one path —
and it will be right. Broadcast storms do not fix themselves and they do
not stay polite: the storage VLAN flaps first, then everything stacked on
top of it (copy jobs, sessions, the monitoring scraper) falls over in a cascade that looks like six unrelated
problems.

## Fast diagnosis, in order

1. `harbor` web panel → *Diagnostics → Loop events*. The log names the two
   ports that saw the duplicate frames. That pair is your loop.
2. One of the two ports is almost always the spare patch lead. In this
   rack the spare grey lead lives coiled next to the switch and, being
   pre-patched at both ends since June, will happily re-create the loop if
   it falls behind the rack and lands on itself. See the sticky note in
   `notes/sticky-label-cables.md`.
3. `weathervane` board *network · storage · latency* will be a flat-lined
   zero or a sawtooth. A sawtooth that started minutes before the loop
   event is the storm's arrival time.

## The fix

1. Unplug ONE end of the offending patch lead. One end. Unplugging both
   means you no longer know which run it was.
2. Watch `ERR_BRIDGE_LOOP_77` counters go quiet within a minute.
3. Verify the storage VLAN holds: ping `bramble` (192.168.30.10) from
   `weathervane` for five full minutes. The March incident had a bounce-back
   at minute four when a second loop, from the same coiled lead, re-formed.
4. Only then re-enable anything that auto-started and stopped.

## Prevention (all in place as of 2026-03)

- Spanning tree enabled on `harbor` and on `gatehouse`. It was off on the
  old unmanaged switch, which is why March happened at all.
- Storm control: shut the port after 200 broadcast frames/second for 5
  seconds, recover after 60. Default recovery of "instant" made the first
  fix look like it had failed.
- The spare lead is now labeled at both ends and hangs on a hook, not in
  the rack.

## If it is not a loop

If loop counters are zero but the storage VLAN still flaps, suspect the
PoE injector on the upstairs wall-plate run. It browns out above 30 °C and
its symptoms (port up/down every few minutes) mimic a loop without ever
logging one. Swap the injector before re-cabling anything. This cost a
full Saturday in July to learn.
