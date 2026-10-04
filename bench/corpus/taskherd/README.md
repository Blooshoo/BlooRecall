# taskherd — team notes repository

taskherd is a mobile task manager for small groups: shared boards, due-date reminders, and a sync engine that tolerates long connectivity gaps. This repository holds the team's specs, plans, meeting notes, support material, and runbooks.

Team roster (as of 2026-09):

- Maya Okafor — iOS client lead
- Dmitri Vale — Android client lead
- Priya Raghunathan — backend and sync engine
- Tomas Lindgren — product management

## Repository map

- `specs/` — normative product and system specifications. A spec is authoritative once it ships; revisions are separate files (for example `offline-conflicts-v2.md`).
- `plans/` — implementation plans, incident follow-ups, roadmaps, and audits. Plans are proposals until a meeting note records the decision.
- `meetings/` — decision notes from weekly syncs and postmortems, named by date.
- `support/` — reply macros, the known-issues list, and the escalation playbook for the on-call rotation.
- `runbooks/` — operational procedures for the on-call engineer.

## Core vocabulary

- **Herd Sync** — the replication protocol between clients and the backend. v1 shipped in taskherd 2.0.0 (2025-10-27); the v2 protocol cutover completed 2026-04-06.
- **Board** — a shared list. Boards have members, roles (owner, editor, viewer), and a change feed.
- **Quick Capture** — the fast task-entry surface: a swipe-down composer available from any screen, plus the Capture action on taskherd notifications. Shipped in 2.4.0.
- **Local queue** — the on-device store of edits made while the app cannot reach the backend, drained by reconciliation.
- **Recovery shelf** — where a losing edit lands when a conflict is resolved, and where reminders land when they cannot be delivered. (The reminder-side shelf is a 3.0 concept; see `specs/reminders-rework-spec.md`.)
- **Badge** — the app icon count: assigned, open items due today or overdue.

Current release line: 2.9 (2026-07-06). The 3.0 line is in a staged beta at 5% of accounts as of 2026-09-08. Patch releases are not itemized in `CHANGELOG.md`; see the release train notes in `plans/`.

## Conventions

Every spec starts with an author, a date, and a status line. Meeting notes record attendees and decisions, never transcripts. Runbooks assume the reader is on call and mildly annoyed; keep them short and numbered.
