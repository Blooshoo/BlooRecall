# Checklist — vacation mode

Status: current. Used 2026-08-03 → 2026-08-16; next trip penciled for
December. Written 2026-07-27 after the spring trip, during which the
board filled with three days of noise about things nobody could act on
from a beach.

## Day before departure

- [ ] Confirm the nightly mirror and weekly verify are green **today**, so
  the pipeline enters the trip healthy.
- [ ] Mute, do not disable, the board alerts that require a human in the
  building: pool pressure, UPS self-test reminder, the humidity gauge
  (`notes/humidity-damp-rack.md` — the basement drier gets switched off
  at the breaker while away, so the gauge WILL drift; muting it is the
  correct response, not disabling it, so the drift is visible on return).
- [ ] Leave running: mirror, verify, scrub if scheduled, resolver, board.
  These are the unattended-safe jobs; everything else on the schedule
  table gets its "away" flag.
- [ ] Pause the media download queue. Unattended mass fetching onto the
  pool right before a capacity-crossing is exactly how the July red gauge
  happened.
- [ ] Set the cyan network's lease pool to a short window (visitors may
  look after the cats; they do not need permanent leases).
- [ ] Print the one-page card for the house sitter: board URL (works from
  the cyan network), what green means, and the single instruction — "if
  the storage tile goes red, unplug nothing, call the number on the card".

## On return

- [ ] Un-mute the muted alerts before doing anything else, or the first
  real incident back will be invisible.
- [ ] Read the board's event history for the whole trip. Both trips this
  year had exactly one real event each (April: an endpoint stall; August:
  a self-test badge) — both were visible in history and neither needed
  the beach-side panic the live board would have invited.
- [ ] Resume the download queue deliberately, checking the capacity gauge
  first.
- [ ] Flip the cyan lease pool back.

## The rule this checklist encodes

Vacation mode is about *noise discipline*, not about turning things off.
The pipeline runs fine unattended; what does not run fine is an alert
board screaming into an empty house until it trains everyone to ignore it.
