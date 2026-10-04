# Marrow Flats tileset refresh — plan

Owner: Dev Okonkwo, with Marisol Vega on palette and lighting. Date: 2026-07-06. Runs parallel to the demo content freeze — Marrow Flats is full-game content, so it may proceed while the demo route is frozen, as long as it touches nothing the demo ships.

## Why

The Marrow Flats blockout was built from quarry-placeholder tiles and it shows: the flats are supposed to read as *fast, open, endless*, and the quarry tiles read as *vertical, cramped, careful*. First-time testers described the area as "the part where the game slows down", which is the exact opposite of its design intent.

## The plan

1. **Palette shift**: from quarry gray-brown to rust and ochre, with a high sky band. The ochre end of the ember ramp (see specs/sparkline-trails.md) anchors the warm end so trails stay visible against it.
2. **Parallax 3 → 4 layers**: the flats need a distant horizon layer the quarry never used. The new layer is a static mountain silhouette strip, drawn at 0.1× scroll, no lighting response (it is past the light volume range by construction).
3. **New tiles**: 60 new tiles (flats ground, cracked pan, wind-scoured beam), reusing 40 existing tiles where the read is identical.
4. **Lighting**: two gradient volumes max per screen in the flats (sun band + ground bounce); the six-light cap from specs/rendering-pipeline.md is not reachable here and that is fine.

## Division of labor

- Dev: tile shapes, blockout revision, pacing pass with the new tiles (done when the flats test course reads as "faster than the quarry" to 5 of 5 fresh testers).
- Marisol: palette bake, horizon layer, one lighting volume pass.
- Nobody: new mechanics. The flats test speed the game already has.

## Dates

Tile art done 2026-07-24. Blockout revision done 2026-08-03. Pacing pass 2026-08-07. If the pacing pass slips past 2026-08-14, the flats slip to post-festival and this plan is paused — the demo comes first, in writing, so nobody has to relitigate it in August.
