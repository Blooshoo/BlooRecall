# Ship checklist review — festival build

2026-08-24, 15:00–16:00. Attendees: full team. Notes: Priya Raman. Purpose: walk the demo-build gate list item by item, assign the last tasks, and agree what "done" means for travel.

## Gate status (from plans/demo-build-plan.md)

| Gate | Status | Owner | Notes |
|---|---|---|---|
| 1. p95 ≤ 16.6 ms, full route, reference box | GREEN | Marisol | closed 2026-08-12, margin 0.4 ms, do not spend it |
| 2. Respawn-cost p95 ≤ 900 ms every node | GREEN | Dev | closed with the 0.16.0 audit; K-07 and K-12 needed the slimmed world deltas |
| 3. Cold tail ≤ 600 ms | GREEN | Tomás | 430 ms on the candidate |
| 4. Zero first-use admission warnings | GREEN | Rosa | log clean three nights running |
| 5. Latency rig 45 ms p95 | AMBER | Tomás | 46.8 ms on the candidate; the capture star freeze trim (0.16.1) is expected to close it, re-run after |
| 6. Telemetry opt-in copy | AMBER | Priya | second draft in; reading time 11 s, needs under 10 |

## Last tasks

- **Attract-mode cut refresh** — Tomás + Rosa, due 2026-08-28. Pull the newest starred captures from the 0.16.1 playtests; the current cut has a torn-tail freeze frame nobody noticed until the big screen test.
- **Grade + letterbox lock** — Marisol, due 2026-09-01. Festival grade becomes the shipped default; cool grade stays behind the debug toggle.
- **Route lock** — Dev, due 2026-08-30. After this date, route changes need Priya plus a re-audit, per the freeze rules.
- **Telemetry copy final** — Priya, due 2026-09-05.
- **Latency re-run** — Tomás, due 2026-09-03, on the same rig, 5,000 presses, no shortcuts.
- **Full rehearsal on the show-floor box** — everyone, 2026-09-08. Twenty minutes, the actual route, the actual box, travel case closed after.

## Agreed definition of done

All six gates green on the *festival candidate tag*, the show-floor box build installed and rehearsed, and a printed one-page run sheet in the travel case. If gate 5 is still amber on 2026-09-05, we ship 0.16.2 with the latency fix or we accept 46.8 ms — decision meeting 2026-09-06, no later, because Rosa's build cut cadence needs the answer.
