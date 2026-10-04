# Kiln Run — world 2 design notes

Author: Dev Okonkwo. Blockout playable 2026-01, tuned through June. Status: nodes K-01–K-08 ship in the demo; K-09–K-12 are full-game.

## Intent

The kiln is vertical: a 220 u descent through a tiled shaft where heat vents push you back *up*, and the game is about spending altitude as speed without the vents stealing it back. Where the quarries teach, the kiln examines. Wall cling (specs/wallride.md) becomes load-bearing here, and the sparkline is the reward for doing it well.

## Node map

| Nodes | Idea |
|---|---|
| K-01–K-02 | Entry shelves; cling teach (approach speed built by the shelf dive) |
| K-03–K-05 | Vent corridors; read the up-blast, route around it |
| K-06 | The long vent — 140 u/s up-blast, the route hugs the west wall |
| K-07–K-08 | **The flue**: vertical run where cling → detach → cling chains; demo's final overlook |
| K-09–K-12 | Full game: the flue continues, vents and detaches interleave, bottom exit into Marrow Flats |

## Vent numbers (changed twice, this is current)

Up-blast is **140 u/s** applied inside the vent column for as long as Ember overlaps it. The 0.16.1 fix made vent K-06 consistent — it had been drifting low at high tick counts, which testers experienced as "the kiln got easier, did I break it?".

## The flue (K-07–K-08)

The signature section. A cling window is 900 ms with decayed creep after 500 ms (specs/wallride.md); the flue is tuned so the *comfortable* detach is at 600–700 ms — late enough that the creep is visible, early enough that the decay never costs height. Detach at 520 u/s and 112° carries wall-to-wall in one arc; the walls are 190 u apart, which makes the arc read. Most players hit their longest sparkline of the demo here.

## Perf personality (from the war room)

The kiln is the heaviest scene we ship: vent emitter storms plus two concurrent sparklines is the load case in specs/rendering-pipeline.md's budget. Node edits in the kiln need a p95 re-run — this is written in plans/perf-push.md and it is not optional. Twice in May, an "innocent" vent move cost 0.8 ms of tail.

## Playtest notes worth keeping

- Testers read the tiled shaft as "clingable" and the rough rock as not — the tile pattern is doing real work; never put cling surfaces on rough rock (also in specs/wallride.md).
- The kiln's first tile turn overshoot drove momentum tuning pass 2 (plans/momentum-tuning-v2.md). If the turn moves, re-run the overshoot count.
