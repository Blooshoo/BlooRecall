# The toboggan hack

Author: Tomás Iriarte. Date: 2026-05-06. Status: shipped since 0.10.0, undocumented until now — Marisol asked what it was during the May war room and the answer was "a paragraph in my head". Now it is a file.

## Name and origin

Tomás named it the toboggan hack because the mental model is "you sit on a toboggan and the hill decides". It is the slope coast solver: the piece of the momentum model that carries Ember over a convex break in the terrain without eating all their speed or launching them on a phantom ramp. specs/momentum-model.md treats it as a black box; this file is the box.

## The problem

At a convex break (a hill crest), the last contact normal and the next surface normal disagree sharply. The naive options both feel wrong: transfer velocity onto the new slope (kills speed instantly — testers read it as "the hill grabbed me") or keep full velocity along the old tangent (produces a launch the level never intended — testers read it as "the hill punched me").

## The hack

Fit a **quadratic through the last three contact normals** (oldest to newest), integrate along the fitted curve for up to **260 ms** of simulated coast, and hand back to normal ground contact at whatever point the fitted curve meets the next surface. Four refinement passes per tick keep the fit honest when the terrain under the arc is itself curved (switchback crests). The fit runs in the tangent plane, so it costs effectively nothing — it is a few dozen flops where the alternative was raycasts.

The 260 ms ceiling exists because the fit degenerates on long airtime: past that, this is just jumping, and the airborne rules should own it.

## When it lies

- **Sawtooth terrain**: three normals from three different teeth of a sawtooth ridge fit a smooth curve through terrain that is nothing like smooth. The normal-cone clamp (below) is the only thing keeping this sane.
- **Moving platforms**: the fit assumes static contact history. On the one kiln platform that moves, we disable the solver and fall back to the naive transfer — which is fine, because the platform is slow.

## The clamp

The fitted exit direction is clamped to a **35° cone** around the new surface normal. If the fit wants to exit outside the cone, it is clamped, and the clamped-away speed is converted to height-for-speed exchange at the 0.85 rate from specs/momentum-model.md. The clamp is why sawtooth ridges are survivable: worst case the hack degrades to a slightly generous version of the naive rule, never to a launch.

## Rules of engagement

- Do not put sawtooth ridges under 480+ u/s routes without telling Tomás. The clamp handles it, but the feel deserves a look.
- Player-facing copy must never mention the solver. If a player can perceive it, it should be as "the hill flowed", not as a mechanic with a name.
