# orbital-lab — working notebooks

Working repository for the ORBITAL pipeline: capture cages, frame intake, motion
tracking, and the render farm. This is our lab notebook, not product
documentation. Entries are written by the people who did the work, on the day
they did it, with the numbers we actually measured.

## People

- Ingrid Halvorsen — principal investigator; owns decisions, budgets, and the roadmap.
- Priya Chandrasekhar — tracking stage; association, bridging, benchmarks, colormaps.
- Marco Deluca — render farm; scheduler, QC gates, heat and maintenance.
- Bram Oosterhuis — intake side; capture cages, the hose, timing and digests.

## Layout

- `experiments/` — numbered experiment records (`exp-NNN`). One question per
  record, with method, numbers, and a verdict. Numbers ascend over time; the
  number is assigned when the experiment is opened, not when it is written up.
- `notes/` — working notes, incident sagas, cheat sheets, living tables.
- `protocols/` — operating protocols. When a protocol changes materially we cut
  a new version and withdraw the old one; a withdrawn protocol is never edited
  in place beyond its status banner.
- `docs/` — long-form references: architecture, operations, configuration.
- `meetings/` — minutes, one file per meeting, named by date.

## Conventions

- ISO dates everywhere (2026-04-22). Times are lab-utc unless marked otherwise.
- Frames are counted in this repo, never stored in it.
- Error codes get registered in the week's ledger note before first use; each
  code lives in exactly one place.
- A decision that overrides an earlier one says so in its first line, with the
  path of the document it replaces.
- Farm nodes are `renderlet-NN` and are never renamed. See
  `notes/renderlet-naming.md` for why.

## Start here

- Tracking: `docs/tracker-architecture.md`
- Farm: `docs/render-farm-operations.md`
- Configuration: `docs/pipeline-config-reference.md`
