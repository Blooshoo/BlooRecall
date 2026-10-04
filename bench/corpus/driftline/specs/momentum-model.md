# Momentum model — core structure (v1, 2025-10)

Author: Tomás Iriarte. Reviewed with Dev Okonkwo. Date: 2025-10-20. Status: implemented as of 0.9.0.

This file fixes the *structure* of the movement rules. The numbers below are the 0.9.0 baseline; the tuning passes in `plans/` own revisions to them. Structure changes need a new spec file.

## Ground contact

- Ground acceleration: 42 u/s² while the stick is deflected past the deadzone.
- Ground maximum: 480 u/s. Beyond that, only external forces (boost pads, vents, dives) can push; the clamp does not fight them, it just stops player-owned acceleration.
- Friction: 260 u/s² of deceleration when the stick is neutral. Friction never applies against the direction of external impulses within 200 ms of the impulse landing.

## Slopes

Slope influence is projected onto the surface tangent. Downhill adds up to 140 u/s² of assist at 35°, scaled by the sine of the slope angle. Uphill costs the same, capped so that walking speed uphill is never below 120 u/s. Above 50° the surface stops being ground and becomes a cling candidate (see specs/wallride.md).

Coasting over convex breaks is handled by the slope coast solver — the internals are documented separately (see specs/toboggan-hack.md); from this spec's point of view the solver is a black box that preserves tangent speed across the break.

## Boost pads

A pad applies an impulse of +180 u/s along its arrow, then 200 ms of immunity to friction and to the ground maximum. Stacking two pads within the immunity window adds the impulses but does not extend the window — the second pad refreshes it instead.

## Friction bands

| Surface | Deceleration (u/s²) |
|---|---|
| Quarry stone | 260 |
| Damp moss | 180 |
| Polished kiln tile | 120 |
| Damper crate top | 420 |

Damper crates are the teaching tool for the first world: players learn that landing on one costs speed, and that avoiding them is a choice.

## Air control

Once Ember leaves the ground plane, stick influence scales to 35% of the grounded value and drag falls to 12 u/s². A held direction commits after 80 ms; releasing before that returns 60% of the spent effort on landing. The height-for-speed exchange on a held dive is fixed at 0.85 and does not stack with boost pads. Nothing in this section applies during the grace window described in specs/coyote-time.md — during that window Ember is still treated as grounded for press purposes.

## Integration

Fixed 60 Hz simulation step, semi-implicit Euler, all forces accumulated before integration. The renderer interpolates poses between ticks; gameplay never reads render-frame time.

## Guard rails

If position or velocity ever becomes non-finite, the simulator raises `ERR_MOM_NAN_401` and snaps Ember to the last good node with velocity zeroed. This has fired exactly twice since 0.9.0, both times from a vent and a pad applying impulses in the same tick at the world border seam. The seam is fixed; the guard stays.

## Open items

- The 0.85 dive exchange is tuned for the quarry; Kiln Run's verticality may want a separate constant. Decide when the kiln blockout is playable.
- Whether damper crate tops should also damp air drag for one tick after landing (they currently do not).
