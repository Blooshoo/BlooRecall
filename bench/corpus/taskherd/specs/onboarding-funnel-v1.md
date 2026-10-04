# Onboarding funnel — v1

- Author: Tomas Lindgren
- Date: 2025-10-20
- Status: replaced — see `onboarding-funnel-v2.md` (2026-01-12)

## Funnel shape (v1)

Five steps, all up front, before the user sees a real board:

1. Welcome carousel (3 swipe panels).
2. Account creation or sign-in.
3. Notification permission pre-prompt (the "why we need it" page).
4. Profile: display name, avatar, timezone confirmation.
5. First board: name it, invite up to 5 members by email.

Measured on the 2.0.0 GA cohort (2025-10-27 to 2025-11-30, n = 88,400 installs):

- Carousel completion: 84%.
- Account creation: 71%.
- Permission grant (after pre-prompt): 66%.
- Reached a named board with at least one member invited: **62%**.
- Time to first task: median 4 minutes 10 seconds.

## What v1 got right

The invite-by-email step at the end produced an unusually high first-week co-retention: users who completed step 5 with at least one invite accepted retained at 78% week 4, versus 41% for solo completers.

## What v1 got wrong

Two things, both visible by mid-November:

- The up-front notification pre-prompt cost 5 points of permission grant versus the platform benchmark, because users had not yet seen any value.
- The 3-panel carousel was skipped by 16% of users, and skippers completed the rest of the funnel 9 points better than non-skippers — the carousel was pure friction.

These findings, and the decision to replace the funnel, are recorded in `meetings/2026-01-12-onboarding-decision.md`. v2 of this spec takes over from that meeting forward.
