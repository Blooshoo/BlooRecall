# Tools and capture tooling — handoff, Tomás → Rosa

Date: 2026-07-10. Outgoing: Tomás Iriarte. Incoming: Rosa Lindqvist (joined 2026-06).CC: Priya Raman. This file is the checklist we walked through together on Rosa's third week; it is written down so the next handoff starts from a document instead of a whiteboard photo.

## What transfers

1. **Build ownership** — the nightly cut (02:00), weekly candidates from 2026-08-10, the festival tag process, and reference/build-matrix.md, which you now maintain. The escalation rule bears repeating: two failed nightlies in a row goes to Priya the same day. The March double-failure sat quiet for four days; never again.
2. **Capture tooling** — the ring, the save path, and the cutter that assembles attract mode from starred captures. The architecture is specs/quick-capture-architecture.md and the format pin is specs/replay-format.md; both are current. The cutter lives with the toolpack, not the game build.
3. **The debug overlay** — keys are in reference/debug-overlay-keys.md. The Alt+K conflict (it shadows the node picker on some layouts) is yours now; two testers lost screenshots to it in June.
4. **The latency rig** — the 5,000-press hardware counter harness. It must re-run before any presentation-path change ships (specs/input-latency.md). Tomás remains co-owner of the *numbers*; you own the rig's upkeep.

## What stays with Tomás

Gameplay and input code, the momentum model, coyote logic, wall cling, the toboggan hack, checkpoint respawn behavior. Ask him before touching anything in specs/momentum-model.md's orbit — several constants there are tuned against recorded traces and the traces are the truth, not the comments.

## Known sharp edges (the things Tomás said out loud during the walk)

- The capture star freeze is 40 ms as of 0.16.1, hidden behind the 3-frame hold animation. If you ever lengthen the save path, re-check that the animation still covers it — testers read an uncovered pause as a crash (this exact bug shipped once, briefly, in 0.16.0).
- The cutter assumes the starred bit and checksum offsets in the capture header are frozen. They are frozen. If a format revision moves them, the cutter is in the blast radius and Rosa owns the fallout on both ends.
- The nightly sweep runs at the build cut on purpose. Do not move it to an hour a person might be playing; the sweep touching a live session is the bug class we fixed in February.
- Editor trim-handle snapping is 0.5 s and slightly wrong on captures shorter than 3 s (trims clamp to 1 s instead of 0.5 s). Filed, low priority, fix lands in toolpack 3.5.1.

## Who to ask, mapped

- Priorities and scope: Priya. She keeps the gate list; argue with the list through her.
- Renderer, atlas, particles, the budget: Marisol. Her budget doc (specs/rendering-pipeline.md) is the renderer's constitution.
- Content, nodes, audits: Dev. Node edits trigger his re-measurement rules, not yours, but you will hear about it.
- Everything gameplay-constant: Tomás, until the traces tell you otherwise.

## First month, agreed

Week 1: shadow the nightly. Week 2: run the cutter end-to-end once alone. Week 3: own the weekly candidate. Week 4: re-run the latency rig with Tomás watching, then alone. If any week slips, it slips in the open — the handoff worked when the checklist above has checkmarks, not when it has vibes.
