# Marrow Flats — world 3 design notes

Author: Dev Okonkwo. Blockout 2026-02, pacing pass planned 2026-08 (see plans/tileset-refresh.md). Status: full-game content, not in the demo.

## Intent

The flats are the payoff: wide open pan country where the ground maximum stops mattering because everything is downhill, downstream, or on purpose. Design speed band is **480–620 u/s sustained**. The quarries teach, the kiln examines, the flats let you use it.

## The three trial courses

1. **Saltline**: 1,400 u straight-ish sprint, banked edges, one damper crate field as the single mistake cost. Par time 11 s.
2. **Windrows**: 1,900 u with crosswind gusts (momentum toggles — each gust is a ±60 u/s impulse along its normal). Par 16 s. The gusts are fixed-pattern, never random; speedrunning this course is a memory skill.
3. **Longmarrow**: 3,200 u, no obstacles, just the pan curving. Par 24 s. It exists so players can hold a sparkline until it physically can't get longer, once, on purpose.

## Ghost lines

Every trial records your best run as a **ghost line** replayed from the capture data — this is Quick Capture data used as an input, not just a saved file (the sketch Tomás and Dev did after the February playtest). The ghost runs at the recorded input timeline through the current world; if the world changes, the ghost changes with it, which is why trial courses are the one place world edits are cheap.

## Why the flats stayed out of the demo

They need the tileset refresh (plans/tileset-refresh.md) to read as fast — quarry tiles read as "slow down" and the flats are the opposite of that. Scoped honestly: without the art the demo would ship a fast level that feels slow, which breaks pillar one.

## Numbers to keep

- Ground maximum 480 u/s is a *player-owned* clamp; the flats' sustained 620 comes from slope assist (specs/momentum-model.md) and windrows' tailwinds, never from raising the clamp.
- The toboggan hack's sawtooth warning (specs/toboggan-hack.md) applies to the Windrows' eastern rim: 520+ u/s routes there got Dev's note, per the rules of engagement.
