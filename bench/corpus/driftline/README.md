# driftline — working notes

driftline is a 2D momentum platformer built on Ridgeline, our in-house engine. You play a fox (internal codename: **Ember**) who chains dives, wall clings, boost pads, and slope coasts into long, readable speed lines. Hard targets: 60 fps on every tier we ship to, no loading stalls mid-route, and a demo festival build in autumn 2026.

## Team

- **Priya Raman** — producer. Keeps the schedule honest, owns the changelog and the ship checklist.
- **Marisol Vega** — graphics programmer. Renderer, atlas system, particles, post stack.
- **Tomás Iriarte** — gameplay programmer. Momentum model, input, wall cling, Quick Capture.
- **Dev Okonkwo** — level designer. Worlds, blockouts, pacing audits.
- **Rosa Lindqvist** — tools programmer. Joined June 2026; owns builds and the capture tooling after the July handoff (see handoffs/2026-07-10-tools-handoff.md).

## Layout

- `specs/` — design and engine decisions, one topic per file. When a decision changes materially we write a `-v2` file rather than editing history.
- `plans/` — dated plans. Same rule: a revised plan is a new file.
- `meetings/` — notes, decisions, owners. If it isn't in the notes, it didn't happen.
- `levels/` — per-world design notes and audits.
- `reference/` — engine API notes, error codes, config keys, build matrix, glossary.
- `handoffs/` — ownership transfers between people.

## Start here

- `specs/momentum-model.md` — the core movement rules everything else leans on.
- `specs/quick-capture-architecture.md` — how instant replay capture works under the hood.
- `specs/rendering-pipeline.md` — the full renderer doc, including the frame budget.
- `reference/glossary.md` — what "toboggan hack", "sparkline", and "trusted node" mean *here*.
- `CHANGELOG.md` — what changed and when, one line per shipped internal build.

## Conventions

Speeds are in u/s (engine units per second), distances in engine units (u), times in ms unless the sentence is about seconds. The reference box is the 4-core x86 mini-PC with an integrated GPU in the lab; "p95" means 95th percentile over a full route run. Numbers in specs are the decisions; if a plan revises them, the plan wins until the next spec lands.
