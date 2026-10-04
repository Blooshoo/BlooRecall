# Analog stick handling

Author: Tomás Iriarte. Date: 2025-12-04. Status: shipped in 0.11.0.

## Decision

The deadzone is **radial, 0.18**, applied to the raw vector magnitude. We replaced the per-axis deadzone (0.15 horizontal / 0.12 vertical) that shipped in 0.9.0, because per-axis zones made the four quadrants of the gate feel inconsistent: a deflection halfway between two axes could sit inside one axis's zone and outside the other's, and the resulting motion direction snapped unpredictably. Three of twelve testers in the December pass described it as the character "twitching" on gentle nudges.

## Magnitude rescale

Raw magnitude is rescaled from the deadzone to full deflection with a fixed curve:

`output = m^1.6`, where `m` is the raw magnitude remapped so the 0.18 ring maps to 0.0 and the outer rim maps to 1.0.

The exponent was chosen by sweep: at 1.0 (linear) testers overshot the quarry beams on gentle nudges — 9 of 12 overshot at least once per run. At 2.0 the low end felt unresponsive. 1.6 put the overshoot count at 2 of 12 with no complaints about responsiveness.

## Rim snap

Within **12° of a cardinal axis** and magnitude at or above 0.9, the direction snaps to the axis. This exists because a pure radial zone means "almost perfectly horizontal" is nearly impossible to hold, and the beam sections want honest horizontals. The snap angle was 8° first; that was too narrow to catch real hands, 15° ate deliberate near-axis inputs. 12° split the difference on the recorded traces.

## What we deliberately did not do

- No per-title curve presets. One curve, shipped everywhere.
- No velocity-based assistance of any kind. The moment the character's speed changes what the stick means, the tuning passes in plans/ stop being interpretable.
- No inner-ring snap. The radial zone is already round; snapping inside it re-created the quadrant problem we just fixed.

## Traces

The recorded stick traces from the December pass (12 testers × 3 routes, 250 Hz) live with the build artifacts for 0.11.0. Re-run the sweep against them before touching the exponent again — the numbers above are only meaningful against that population.
