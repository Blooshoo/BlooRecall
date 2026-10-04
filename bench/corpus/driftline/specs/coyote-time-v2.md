# Coyote time — v2

Author: Tomás Iriarte. Date: 2026-03-11. Status: shipped in 0.13.0.

**Supersedes specs/coyote-time.md (2025-10-08).** The flat 120 ms window described there is gone. Replace it with the layered rule below; the old file remains only as history and for its test-harness notes, most of which still apply.

## Layered window

- **Base window: 100 ms.** Applies to every grounded leave, any speed.
- **Speed extension: up to +60 ms**, scaled linearly for leave speeds between 120 u/s and 420 u/s. A committed run that over-runs a ledge at 420 u/s or faster gets the full 160 ms. A stumble off a beam at 90 u/s gets the bare 100 ms.
- **Wall exits get nothing.** Unchanged from v1: a detach is deliberate.
- **Press-side buffer shrinks 100 → 80 ms.** The extra forgiveness now lives entirely on the leave side; keeping it on both sides made the top end feel floaty rather than generous.

## Why the change

Kiln build playtests (February 2026), 8 testers, 61 recorded overruns: at leave speeds above 400 u/s the flat 120 ms window covered 58 u of travel, and testers described fast overruns as "the press didn't come out" even though the timing was identical to slow overruns they described as fine. The extension is proportional to what the eye tracks — distance, not time — which is why the curve is linear in speed rather than in log speed (we tried the log fit first; it over-forgave mid speeds and testers noticed the inconsistency).

## Interaction with the rest of the model

- The window still applies only to grounded leaves; pads, vents, and wall detaches are excluded exactly as in v1.
- The 160 ms ceiling is deliberately below the 200 ms friction-immunity window from boost pads. Stacking the two felt like free flight in the northwest quarry shaft; the ceiling keeps them distinguishable.
- specs/momentum-model.md's section on the grace window should now be read as pointing at this file.

## Migration matrix

Debug harness speeds {90, 240, 420, 520} u/s × surfaces {flat, beam, 35° slope}, press offsets swept 0–200 ms in 10 ms steps. Pass criteria: press counts as grounded for the full computed window at every combination, and the window reads as 100 ms flat at 90 u/s and 160 ms at 420+ u/s. All 12 combinations green on the 2026-03-06 build before this shipped.
