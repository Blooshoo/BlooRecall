# Support escalation playbook

- Owner: Tomas Lindgren
- Effective: 2026-04-27 (this revision; supersedes the January draft)
- Audience: whoever is holding the support rotation this week

## Severity ladder

| Level | Definition | First response | Escalate to |
| --- | --- | --- | --- |
| SEV-4 | Question, how-to, one user, no data at stake | 48 hours | none |
| SEV-3 | Feature broken with a workaround in `known-issues.md` | 24 hours | owning dev, next standup |
| SEV-2 | Feature broken, no workaround, small group affected | 8 hours | owning dev same day |
| SEV-1 | Suspected data loss, or any user-facing outage of sync or reminders | 1 hour | page backend (Priya) or client (Maya/Dmitri) on call |

SEV-1 is a page, not a ticket. The pager goes to the rotation in `runbooks/` order; if nobody acknowledges in 15 minutes, the second name is paged automatically. There have been four SEV-1s in the twelve months to 2026-04: the October 2025 storm, two migration wipe-and-resync tickets in May 2026, and one false positive (a user whose co-owner had deleted a board, a permissions question wearing a data-loss costume).

## The rotation

Support is a team sport with a named holder each week, Monday to Monday: Tomas (weeks 1 and 3), Priya (week 2), Maya and Dmitri alternating week 4. The holder answers first responses; engineers own their escalations regardless of who holds the week. Vacation swaps go in the calendar, not in chat.

## What always escalates immediately

- **Any mention of lost text or missing tasks.** No macro, no template — the reply is written by the diagnosing engineer (the store-review plan has the two examples; both needed specifics no macro could carry).
- **Review-reply path:** reviews reporting data loss go to Priya the same day with the review text attached.
- **Quarantined reconciliation entries** surfaced by a user ("my edit is stuck"): backend on call, same day. The user-visible symptom is a task that will not stop showing "pending".

## During incidents

When a SEV-1 is confirmed, support switches to the holding-response pattern: acknowledge, state what we know in one sentence, commit to a next update time, and stop replying individually until the incident channel says otherwise. The comms template from the October 2025 postmortem action items is the starting text. The April cutover week was the dry run: zero holding responses needed, which is the outcome we want from every drill.

## Weekly review

Every Monday the holder closes the week: tickets by severity, macro hit rate, and any ticket that took more than two replies. The two-reply rule: if a ticket needs a third reply, the Monday review asks whether a macro, a known-issue entry, or a spec is missing. That review is where the first-launch macro and the badge-repair macro both came from.
