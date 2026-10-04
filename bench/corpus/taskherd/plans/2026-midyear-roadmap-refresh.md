# 2026 midyear roadmap refresh (H2)

- Owner: Tomas Lindgren
- Date: 2026-07-13
- Status: current planning baseline; reviewed at the 2026-10-05 session

## Where we stand in July

The first half delivered what Q4-2025 seeded and Q1 promised: the Herd Sync v2 cutover landed 2026-04-06 with no rollback (drill timings held; soak runs to 2026-04-20 when v1 retires), the herd-store schema v2 migration shipped in the May patch train, onboarding funnel v2 is at 71% completion and climbing, and the reminders rework is approved for the 3.0 line with beta staged in September. Cold start finished under budget at 870 ms p95 against the 900 ms target.

## H2 commitments

### 1. Reminders rework to GA — taskherd 3.0

Beta from 2026-09-08 at 5%, doubling every two weeks contingent on the punctuality metric (98% within 60 seconds) and shelf-occupancy stability. GA target: 2026-11-16. Entry criteria are in the rework spec; the open questions there (digest section merge, 48-hour shelf for stale boards) close by 2026-10-15. Owners: Maya and Dmitri, with Priya on the mirror and digest feed.

### 2. Supportability quarter

The incident load of H1 (storm drill, migration wipe-and-resyncs, the kangaroo and tumbleweed episodes) showed the gap is not reliability but repairability. H2 deliverables: quarantine batch-inspect tool (Priya, 2026-09-30), delivery report in Settings (Maya, with 3.0), and the escalation playbook refresh (Tomas, 2026-08-31). Success measure: median time from user report to informed reply under 24 hours, from 38 hours in June.

### 3. Localization completion

The July pass added 12 locales (`plans/localization-pass.md`); H2 closes the loop with translated store listings, the two truncated channel labels fixed in the 3.0 train, and the pseudo-localization gate wired into the release checklist. Owner: Dmitri.

## H2 stretch

- **Watch-face reminder spike** — pending platform confirmation callbacks; 3.1 window at the earliest.
- **Sample-board onboarding variant** — the experiment Dmitri took from the May scale review; runs behind the flags panel in October.

## Explicitly deferred to 2027

Collaborative timers, board polls, ASCII confetti — parked formally in `plans/parked-ideas.md`. Also deferred: the web companion, which the midyear survey (2,400 responses, 2026-06) ranked behind offline reliability by 31 points; offline reliability is served by the reconciliation work already shipped, so the honest H2 answer to web is "not this year, and here is the data."

## Capacity

Four people, no hires before 2027 per the company plan. The commitments above assume Priya's quarantine tool and the 3.0 mirror work coexist — if they collide, the tool slips, not the beta.
