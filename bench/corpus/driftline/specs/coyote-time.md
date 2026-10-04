# Coyote time — v1

Author: Tomás Iriarte. Date: 2025-10-08. Status: shipped in 0.9.0.

## Decision

A flat **120 ms** grace window after Ember leaves the ground. During the window, a press is still counted as if Ember were grounded — same strength, same pose rule, same sound. After the window closes, presses are handled by the airborne rules in specs/momentum-model.md.

## Why

From the quarry blockout, before the window existed: beam hops failed 31% of attempts across 12 internal testers at 60 fps. With the 120 ms window, the failure rate dropped to 9%. The failing attempts clustered at 40–90 ms after leaving the edge — exactly the range the window absorbs. We picked 120 ms because it covered the observed late-press cluster with margin and still felt "honest" to the two testers who were told the mechanic existed.

## Scope and interactions

- The window applies only when leaving ground by *running off* an edge. It does not apply when leaving a wall — a wall detach is a deliberate act (see specs/wallride.md) and gets no grace.
- It stacks with the press-side input buffer (100 ms) but they are separate budgets: the window forgives *late* presses after leaving ground; the buffer forgives *early* presses before landing.
- Boost pad launches are unaffected — a pad launch is not an edge leaving, and giving a grace window there made pads feel mushy.
- During the window the pose system keeps the grounded locomotion pose, which is also what hides the transition from the player.

## Tests

1. Run off a flat edge at 240 u/s, press at 60/90/119 ms — press counts as grounded in all three.
2. Run off a beam at 480 u/s, press at 119 ms — counts.
3. Detach from a wall, press at any offset — never counts as grounded.
4. Press 121 ms after leaving — airborne rules apply.

## Revisit trigger

If the top-end speed range grows past roughly 600 u/s, re-measure. A flat window is proportionally stingy at speed: 120 ms at 480 u/s covers 58 u of travel, but at 700 u/s it would need to cover much more ground for the same *felt* margin. No change today; flagging the condition so whoever picks this up next starts from data instead of vibes.
