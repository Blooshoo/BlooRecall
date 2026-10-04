# Sparkline visual notes — motion and the trail

Cece Marlow, 2026-02-06. Companion to the `<Sparkline>` component spec.

## The trail

The comet trail is the signature. On hover-scrub, the trail follows the cursor along the line with a soft decay: opacity 0.9 at the head easing to 0.05 over 28 px of tail. The trail must read as motion, not decoration — if it reads as sparkle, we failed. Think of it as the wake behind the newest data, not as an effect bolted on top.

## Glow

Glow lives only on the terminal (newest) point: radius 6 px, breathing at a 2.2 s period with 6% amplitude. No glow anywhere else on the component. Reduced-motion users get a static full-opacity dot instead of the breathing pulse.

## Velocity cue

Dense mode drops the dot and doubles the trail decay length so fast-moving series read as streaks. A flat series should look calm: the trail collapses onto the line itself and effectively disappears.

## Motion budget

All trail and glow animation resolves inside 180 ms after the pointer stops. Anything longer reads as lag, not polish. This matches the 180 ms budget in the component spec — one number, two documents, no drift.

## Palette

Use the standard series tokens; the trail tint is the series color at 45% alpha. History: the March accent regression briefly turned every trail violet (fixed in the 4.1.2 hotfix). Rule since then: never hardcode a trail color.
