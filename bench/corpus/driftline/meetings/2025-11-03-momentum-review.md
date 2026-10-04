# Momentum review

2025-11-03, 14:00–15:30. Attendees: full team. Notes: Priya Raman. Instrument: 12 internal testers, 41 recorded route completions on the 0.10.0-candidate quarry build.

## What the data said

- Completion times: median 6:12 on the quarry teach route, spread 4:40–9:05. Fine.
- **"Too slippery on small landings"**: 9 of 12 testers, unprompted. The dominant complaint by a factor of three.
- Boost pads: uniformly loved, nobody described them as mistimed.
- Beam hops: failure rate down at 9% with the coyote window (specs/coyote-time.md), nobody complained about it — the window is doing its job invisibly.
- Air steer: no complaints, but nobody used it deliberately either. Watch, don't touch.

## Diagnosis

The slipperiness traces to the landing interaction, not the friction constants: a small hop keeps 60% of whatever velocity you had, and players *abandon* velocity on small hops. The 60% keep number is right for big landings and wrong for small ones.

## Decisions

1. Tomás writes a tuning pass plan that changes the landing interaction first and the six core knobs **not at all** unless the landing fix misses. Plan due 2025-11-05 (it became plans/momentum-tuning-v1.md).
2. Dev raises the damper-crate count on the early route so the "landing costs speed" lesson is taught before it's tested (4 → 7, quarry nodes 1–9).
3. Dev audits boost pads that fight friction within 300 u of a damper crate; three qualify, they get moved.
4. The six core knobs come back on the table only if the complaint count doesn't halve — the trigger is written into the tuning plan so we can't quietly skip it.

## Carried observations

- The kiln blockout is far enough along to play but not to tune; December gets it in front of testers for the first time.
- Marisol: atlas page-in stalls are "annoying but rare" on the current route; she'll have real numbers when the pose art is final. Noted as a watch item, no action today.
