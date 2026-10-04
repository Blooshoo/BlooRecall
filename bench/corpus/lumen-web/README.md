# lumen-web — working notes

lumen-web is our analytics dashboard product: boards of chart tiles, threshold watchers that page when a metric misbehaves, and scheduled Monday summaries. Small team, four people, one web app.

## The team

- Juno Park — frontend lead (rendering, interactions, performance)
- Rafa Lindqvist — data engineering (ingest, storage, query)
- Cece Marlow — design (palette, motion, layout)
- Dot Ferris — product (scope, audits, pager schedule)

## Where things live

- `specs/` — feature and system specifications, dated. Revised specs keep both versions side by side.
- `adr/` — numbered architecture decision records. Once merged, a record is never edited; a successor replaces it and the old file stays for history.
- `meetings/` — kickoff, syncs, retros, planning notes.
- `runbooks/` — operational procedures the on-call rotation follows.
- `incidents/` — postmortems. We name the memorable ones.
- `onboarding/` — setup guide and glossary for new teammates.

## Current state (late September 2026)

The 4.x line is stable; the next minor is in release-candidate. Focus areas this quarter: the query planner rewrite, the compaction overhaul, and focus mode. The 2026-09-30 standup notes are the freshest signal on where each workstream stands.

## House rules

- Specs carry concrete numbers or they are not done.
- Every error code that appears in the UI gets a runbook entry.
- Palette changes ship behind flags with screenshot diffs. We learned this the hard way in March.
- Postmortems blame the system, not people.
