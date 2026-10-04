# Performance war room — kiln descent

2026-05-18, 10:00–13:00 (ran long). Attendees: full team. Notes: Priya Raman. Trigger: the May measurement pass put the kiln descent p95 at **21.4 ms** on the reference box against a 16.6 ms line. The average is fine. The tail is the problem.

## The 21.4 ms, taken apart

Marisol's capture of the worst percentile frames:

1. **Particle simulation overruns** during vent storms — emitters are unbounded exactly when the kiln is at its best. ~2.1 ms of the tail.
2. **Atlas service stalls** colliding with pose solves — the service and the pose system contend for the same upload window, and the pose system is not allowed to lose. ~1.4 ms.
3. **Batch rebuilds** on world transitions — the third sort-key tier turns out to sort nothing on real routes. ~0.9 ms.

The two concurrent sparklines at full detail are *in* the 16.6 ms baseline, not the tail — the ribbon cost is flat and predictable and stays.

## Decisions

1. **Emitter retirement policy**: protect the newest 2 emitters, shed detail from the rest under pressure. Marisol, due 2026-06-01. The sparkline ribbon itself counts as "newest" while it is being drawn — a sparkline that degrades mid-jump reads as a bug (this is also written in specs/sparkline-trails.md; the war room confirms it as policy).
2. **Admission cap enforcement moves into the atlas service** (2 pages per delivered frame, hard). Marisol, 2026-06-01. The cap existed as a rule for callers; making the service enforce it closes the gap the stalls came through.
3. **Prewarm tie-in**: route-critical pages are never admitted mid-route. Tomás, 2026-06-08. Extends specs/cold-start.md to the in-route case.
4. **Sort keys drop from 3 tiers to 2.** Marisol, 2026-06-08.
5. **Marisol writes the budget document** with final measured numbers, due 2026-06-18 — it will become specs/rendering-pipeline.md. Priya: this is the doc we point new hires at; do not let it become a wiki page.

## The gate (restated so it is in the notes)

p95 ≤ 16.6 ms on the reference box, full kiln descent, two sparklines, all vents. Closes only on the reference box, never on a dev machine. The push plan (plans/perf-push.md, 2026-05-25) carries the action table and the memory ceiling.
