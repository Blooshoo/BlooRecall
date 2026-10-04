# Decision meeting — replace the onboarding funnel

- Date: 2026-01-12, 60 minutes
- Attendees: Tomas Lindgren, Maya Okafor, Dmitri Vale, Priya Raghunathan
- Outcome: onboarding v2 approved; spec `specs/onboarding-funnel-v2.md` authored same day

## The case for change

Tomas presented the v1 funnel data (n = 88,400 installs, 2025-10-27 to 2025-11-30): completion stuck at 62%, time to first task 4 minutes 10 seconds. Two specific failures:

1. **The up-front notification pre-prompt** costs 5 points of permission grant versus platform benchmark. Users grant when they have seen value, not before.
2. **The welcome carousel** is skipped by 16% of users, and skippers complete the rest of the funnel 9 points better than non-skippers. We built a wall and charge admission to go around it.

Counter-consideration: the invite step at the end of v1 produces the best co-retention in the product (78% week 4 for invited users). Whatever replaces v1 must protect that, which is why invites move to a contextual moment rather than disappearing.

## The decision

Replace v1 with the two-step funnel in the v2 spec: account creation, then a live board. Notifications asked contextually after the third task; profile asked at first invite; invites at first share or day 3, whichever first. Carousel deleted.

- Guardrail: co-retention for invited users must not drop below 78%. Tomas holds the line on this even if completion climbs — a funnel that completes better but retains worse is a loss.
- Rollback: v1 stays server-selectable via the flags panel; the v2 funnel must beat 58% completion on any 7-day window or the train reverts.
- Ship vehicle: 2.7.0 (2026-03-23), riding with conflict resolution v2 and the rate-limit swap. Three changes, one train, all independently flaggable — the team checked the one-change-per-train rule and agreed these are independent enough; Priya noted the rate-limit change is server-only and the other two are client, so attribution is preserved.

## Votes and dissents

Approved 4-0. Dmitri's recorded caveat: the contextual notification ask needs an OS-behavior test on builds that throttle permission prompts after recent denials; he owns that spike before the 2.7 freeze (closed 2026-02-20, no issue found).

## Follow-ups

- Tomas: v2 spec by 2026-01-12 EOD (done, same file).
- Dmitri: permission-prompt spike by 2026-02-20 (done).
- All: review early numbers at the 2026-03-02 reminders review (71% completion and 81% permission grant reported there; completion still 4 points under target, sample-board variant assigned to Dmitri).
