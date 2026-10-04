# Lowline Quarries — world 1 design notes

Author: Dev Okonkwo. Started 2025-10-27, blockout through 2026-01. Status: content-complete for the demo.

## Intent

The quarries teach the whole momentum vocabulary in 14 nodes without a single tutorial board. Every mechanic is introduced by terrain that *only works* if you use it: the pads are placed where jumping is obviously worse, the damper crates are where stopping is obviously better, and the beam hops are where the coyote window is quietly load-bearing.

## Node map (with route targets)

| Nodes | Teaching | Target route time |
|---|---|---|
| N1–N3 | Run and friction feel | 0:45 |
| N4–N6 | Boost pads, pad chaining | 1:10 |
| N7–N9 | Damper crates (landing costs speed) | 1:20 |
| N10–N12 | Beam hops (coyote window earns trust) | 1:30 |
| N13–N14 | Combining all of it; first signature descent | 1:05 |

Full route: **5:50 target**, 6:12 median measured at the November review (see meetings/2025-11-03-momentum-review.md).

## Specifics worth remembering

- **N5 pad chain**: three pads, 300 u apart, timed so the 200 ms friction-immunity windows chain. If a pad moves, re-check the chain — the third pad's window lapses at 340 u spacing and the chain dies quietly.
- **N8 crate gauntlet**: seven crates, the route threads six. The seventh is deliberately easy to hit — it punishes the *careless*, not the *learning*, and testers who hit it reported it as fair.
- **N11 beam gap**: 90 u gap at 240 u/s approach. This is the node the coyote window was tuned on; do not widen the gap without re-reading specs/coyote-time-v2.md's migration matrix.
- **N13–N14 descent**: 60 u vertical drop over 400 u of run, first place speed visibly exceeds the ground maximum. The sparkline gate (70% charge) is reachable here for the first time — most players see their first sparkline at the bottom of N14 and it lands.

## Things that didn't work

- A tutorial board at N1 ("Hold to run!") tested as *slower* than no board — players who read it ran slower for the next two nodes. Removed 2025-12; the terrain teaches.
- Rooftop-style protrusions between N6 and N7 were cut: they invited wall clings before cling exists in the kit, and failing them felt like the game lying.
