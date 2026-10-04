# Runbook — the nightly mirror stalls

Written 2026-04-21, 23:05, during a stall. Updated 2026-05-02 after the
third occurrence. This is the playbook for the 03:17 job on `bramble` that
pushes the newest snapshot generation to the offsite endpoint.

## Symptoms, in the order they usually show up

- The board tile (*copy · bramble · nightly*) stays amber past 07:00 instead
  of going green.
- The transfer counter on the endpoint dashboard sits at the same percentage
  for twenty minutes or more — typically somewhere in the 60–70 percent
  range, which is where the stall class we get always parks itself.
- `journalctl -u nightly-mirror` shows the last progress line stopped
  mid-stream, with no error after it. A crash looks different: there is a
  traceback. A stall is silence.

## What it usually is

1. **Endpoint throttling.** The rented storage host meters burst bandwidth.
   Large generation deltas get squeezed after the first few gigabytes and
   the effective rate drops to a trickle that never times out.
2. **Leftover evening congestion on the uplink.** If the household was
   streaming in big resolutions all evening, the router's flow table
   sometimes holds stale entries and the first push of the window crawls.
3. **Stale DNS on `dill`.** After a resolver restart the endpoint name
   occasionally resolves to an old address; the connection opens and then
   hangs forever instead of erroring.

## The playbook, in order

1. Confirm it is actually a stall and not a slow night: two identical
   progress readings twenty minutes apart is the bar.
2. `systemctl stop nightly-mirror`, then `systemctl start nightly-mirror`
   once. Roughly half of all stalls clear on a clean restart because the
   wrapper re-opens the connection fresh.
3. If it stalls again at the same percentage: rotate to the secondary
   endpoint (`runbooks/offsite-rotation-v2.md`, steps 2–4) and let the
   wrapper push there instead.
4. While the secondary push runs, prune snapshots older than the retention
   window on the primary endpoint only. A fat generation delta is often
   itself the trigger; the next night usually goes clean.
5. Flush `dill`'s cache if the endpoint name resolves oddly
   (`runbooks/dns-caching-layer.md` has the two commands).
6. Note the stall in the notebook page: date, percentage where it parked,
   which fix worked. Three data points is a pattern; the pattern so far says
   throttling, with congestion a distant second.

## What not to do

- Do not raise the wrapper's attempt count to "power through". Four tries
  with a quarter-hour backoff is enough for every stall we have seen; a
  fifth attempt has never once been the thing that rescued a night.
- Do not restart mid-prune. The prune stage is idempotent, but interrupting
  it leaves the next night's delta fatter than it needs to be.

## Escalation, such as it is

There is no on-call. If the mirror has not landed by the evening, run the
playbook again after dinner; if it stalls a second full night in a row, run
the bare-metal sanity checks in `runbooks/restore-from-bare-metal.md`
section 2 against `bramble` itself (read-only steps only).
