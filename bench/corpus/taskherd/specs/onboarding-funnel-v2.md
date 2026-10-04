# Onboarding funnel — v2

- Author: Tomas Lindgren
- Date: 2026-01-12
- Status: ships in taskherd 2.7.0 (2026-03-23)

This spec replaces `specs/onboarding-funnel-v1.md` (2025-10-20). The rationale and the data that drove the change are in `meetings/2026-01-12-onboarding-decision.md`.

## Funnel shape (v2)

Two steps to a usable board; everything else is deferred to a contextual moment:

1. Account creation or sign-in (the carousel is gone entirely).
2. First board: name it and start adding tasks immediately. Invites and profile move out of the funnel.

Contextual asks replace the up-front ones:

- **Notification permission** is requested after the user adds their third task, when the value is obvious. The pre-prompt page is retired.
- **Profile (name, avatar)** is requested when the user first invites someone, because that is the moment a name matters to another human.
- **Invite flow** appears when the user taps "share" for the first time, or on day 3 via a one-time card — whichever comes first.

## Targets and guardrails

- Funnel completion (account created AND one board with one task): **≥75%**, up from 62%.
- Time to first task: median ≤2 minutes 30 seconds, down from 4:10.
- First-week co-retention must not regress below the v1 mark of 78% for invited users; that is a hard guardrail, not a target.

## Early results

Three weeks after the 2.7.0 rollout (data through 2026-04-17): completion 71%, time to first task 2 minutes 05 seconds, permission grant 81% (the contextual ask outperformed both the v1 pre-prompt and the platform benchmark). Co-retention held at 77%, inside the guardrail. The completion number was still 4 points short of target at review time; the 2026-05-18 scale review assigned Dmitri to test a "start with a sample board" variant.

## Rollback plan

If completion drops below 58% on any 7-day window, the release train reverts to the v1 funnel server-side via the flags panel; the v1 code path remains in the client until 3.0.
