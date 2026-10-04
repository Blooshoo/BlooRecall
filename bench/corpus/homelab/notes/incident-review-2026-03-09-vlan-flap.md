# Incident review — 2026-03-09 storage VLAN flap

Status: final. Written the same night, reviewed and closed 2026-03-15.
Severity: household-critical (everything stopped at once). Duration:
2 h 40 m of impact, 47 minutes of actual fault.

## Summary

At 20:12 the storage VLAN (30) began flapping. Sessions on the main telly
died mid-scene, the nightly mirror's predecessor job aborted, and the
board painted itself amber-then-red in a cascade that initially looked
like six unrelated problems. Root cause: a Layer-2 loop created by the
spare patch lead, which had been coiled live (patched at both ends,
parked behind the switch) since the January tidy-up.

## Timeline (all 2026-03-09, UTC)

- 20:12 — board: storage latency tile flatlines. TV session dies.
- 20:15 — first wrong hypothesis: "the NAS fell over". `bramble` was up
  and answering on its management address the whole time; the flap was
  only on VLAN 30's path.
- 20:31 — second wrong hypothesis: the provider. Checked the router's
  WAN; clean. (This cost fifteen minutes because "everything at once"
  *feels* like the internet.)
- 20:44 — noticed the switch's storm counters climbing. The old unmanaged
  switch under the stairs had no counters, which is when the switch moved
  from "innocent" to "suspect".
- 21:05 — loop event identified on the spare lead. One end unplugged.
- 21:12 — storage VLAN stable, but a bounce-back at 21:23 (the same lead
  re-formed its loop when the coil shifted). Both ends unplugged this
  time, lead hung on a hook.
- 21:39 — jobs restarted; session resumed; board green by 22:52 after the
  alert windows cleared.

## What went well

- `bramble`'s shutdown hooks did NOT fire; the box rode it out, so no
  copy generations were in flight and nothing needed repair afterwards.
- The paper notebook on the rack door got the timeline in real time,
  which is why this review has minute-level times at all.

## What went badly

- The old unmanaged switch was blind: no counters, no logs, no loop
  detection. Every minute spent on it was a minute trusting a box that
  could not testify.
- The spare-lead-lived-in-the-rack arrangement was a known untidiness
  that had survived two "I should fix that" moments. It took an incident
  to promote it to a sticky note (`notes/sticky-label-cables.md`).
- Diagnosis order followed plausibility ("the NAS!", "the internet!")
  instead of following the blast radius (everything that touches VLAN 30
  at once = layer 2 until proven otherwise).

## Actions

- [x] Spare lead labeled both ends, hung on a hook, never coiled live.
  Done 2026-03-09.
- [x] Spanning tree enabled on `gatehouse`; the switch upgrade to a
  managed unit was pulled forward into
  `runbooks/switch-stack-replacement.md` (done 2026-06-14).
- [x] Storm control tuned with a 60-second recovery window (instant
  recovery had made the first fix look failed). Done 2026-03-15.
- [x] Written up as `runbooks/vlan-troubleshooting.md` so the next
  occurrence starts at the counters, not at the provider.
