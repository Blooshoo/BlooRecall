# Q4 2025 roadmap (October–December)

- Owner: Tomas Lindgren
- Date: 2025-09-22
- Status: historical — superseded in practice by `plans/2026-midyear-roadmap-refresh.md` for anything after Q1

## Theme

Get shared boards right before making anything new. The quarter has three commitments and two stretch items; nothing else enters a train without displacing something here.

## Commitments

### 1. Shared boards GA — taskherd 2.0.0, 2025-10-27

Boards leave beta with roles (owner, editor, viewer), the change feed, and invite-by-email. Entry criteria, agreed 2025-09-15: 900-board beta cohort stable for 3 weeks, fewer than 2 data-loss-grade bugs per week, sync p95 apply latency under 400 ms. Owner: Priya (backend), Maya and Dmitri (clients). Beta stood at 612 boards on 2025-09-19; the funnel to 900 was the schedule risk, and we committed to cutting beta invites rather than moving the date.

### 2. Sync hardening — through the quarter

The October incident risk is known: failover produces reconciliation storms (see the postmortem that followed, and the v2 protocol work it started). Q4 deliverables: storm guard in conservative mode by 2025-10-05, per-device throttle policy live (spec dated 2025-09-28), reconciliation pass-success dashboards. Owner: Priya.

### 3. Quick Capture — taskherd 2.4.0, 2025-11-24

The fast task-entry surface: swipe-down composer, notification capture action, quick-saved drafts. Targets set at the 2025-10-20 product review: 30% of new tasks via capture within 60 days of ship, median capture-to-save under 4.5 seconds. Owner: Maya, with Dmitri on gesture conflicts. Shipped on time; actuals at 2026-01-15: 41%, 3.6 seconds.

## Stretch (explicitly droppable)

- **Badge correctness pass** — drift after restore-from-backup annoyed the beta cohort; the real spec landed in December (`specs/badge-counts.md`).
- **Reminder groundwork** — telemetry only. The reminder rework needed the never-fires number (3.1%) before anyone would fund it; that instrumentation ships this quarter.

## Explicitly out

Localization beyond the five launch locales, tablets as a first-class target, web companion. All three are the 2026 conversation, recorded in the midyear refresh.

## Capacity note

Four people. Priya carries the heaviest quarter (GA plus hardening); the team agreed on 2025-09-15 that if commitments collide, GA wins and hardening slips to January — which is, in the event, exactly what the January sync had to formalize.
