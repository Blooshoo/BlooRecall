# Plan — UPS replacement evaluation

Status: open. Opened 2026-07-19. Decision due before the heating season,
because the furnace-beep confusion (`runbooks/ups-maintenance.md`) gets
worse every winter and the current brick is on its third battery.

## The incumbent

1500 VA line-interactive unit, bought secondhand circa 2019, no readable
brand label, three batteries deep. Measured behavior:

- ~85 W household evening load → ~50 min claimed runtime, never tested
  past 10.
- Beeps on furnace blower start (inductive load sag, presumably).
- Monthly self-test: passes, but "battery weak" badge has appeared twice
  since May.
- No network card, no API. Shutdown scripts run off the NAS's own USB
  link, which works but means the monitoring box cannot see battery
  events directly.

## Candidates

1. **Replace with a new 1500 VA unit, network card optional.**
   Predictable, boring, ~350–450. Solves nothing except age.
2. **Replace with a 1500 VA unit with a network interface.** ~500.
   Lets `weathervane` see battery events directly, which means the board
   could show "on battery" as an event instead of "everything is dark"
   as a mystery. This is the real argument for replacing at all.
3. **Keep the incumbent, bridge with a fresh battery.** ~80. Buys a year.
   Network visibility stays unsolved; the brick keeps its mystery beeps.

## What the decision hinges on

- Whether "on battery" visibility is worth ~400. Honest answer as of
  today: probably not yet — the 90-second shutdown order has worked every
  time it has been exercised, and nobody has been home confused during a
  real event.
- The fan on the incumbent has a faint bearing noise that the basement
  hum mostly hides. If it gets loud before October, option 2 wins by
  default because option 3 does not fix fans.

## Next step

Run one deliberate, supervised on-battery test in September (load the
household evening load, watch actual runtime, log it in the notebook).
That number decides more than any spec sheet.
