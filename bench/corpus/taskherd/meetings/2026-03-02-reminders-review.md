# Spec review — reminders rework (3.0)

- Date: 2026-03-02, 75 minutes
- Attendees: Maya Okafor, Dmitri Vale, Priya Raghunathan, Tomas Lindgren
- Subject: draft of `specs/reminders-rework-spec.md` (spec finalized 2026-03-30)

## What was reviewed

Maya and Dmitri walked the draft: the alarm shelf, the state machine (scheduled, armed, delivered, shelved, completed), the server mirror, and the quota framework. The punctuality goal — 98% within 60 seconds on powered devices — and the no-silent-drop goal both went unchallenged; the room spent its time on the numbers and the migration.

## The numbers debate

The draft carried placeholder quotas. Fixed in this meeting and later written into spec section 5:

- **Pending alarm quota:** Dmitri proposed 128; Maya argued the platform worst cases bite well below that and the dogfood p99 was 11 — settled on a number generous to the platform, tight against reality. The exact value and its reasoning live in the spec; this note records only that both parties accepted it.
- **Shelf retention:** the 72-versus-168-hour argument. Maya: 7 days because "a shelve while camping is normal." Dmitri: shelf anxiety is real, the UX sessions showed it. Tomas split it toward the shorter horizon, with the digest line as the safety net for auto-dismissals.
- **Retry policy:** Priya proposed matching the reconciliation ladder's shape but faster — reminders are interactive, drains are background. Agreed; exact intervals in the spec.

## Migration

The lazy-mirror migration (mirror rows created from client state on first launch) passed without dissent. Priya's one condition, recorded: the 14-day soak in the cutover plan must be over before 3.0 beta eats v2 sequence numbers at scale — satisfied by the September beta date against the 2026-04-20 v1 retirement.

## Product calls

- The delivery report ships in 3.0 Settings, not before: users asking "did taskherd even try" is the top reminder-ticket opening line, and the report answers it with state, not apology.
- Digest section layout (one merged section versus two) stays open for beta feedback, decision by 2026-10-15 — Tomas wants one section, Maya wants two, nobody moved, so beta decides.
- The 3.0 beta stages at 5% on 2026-09-08. Locked.

## Action items

- Maya + Dmitri: finalize quotas in the spec from dogfood data (done, spec section 5, 2026-03-30).
- Priya: mirror write-path review before the beta freeze (done 2026-08-14).
- Tomas: draft the beta exit criteria by 2026-08-31 (done; punctuality 98%, shelf occupancy p95 stable under 9, digest open rate non-degrading).
