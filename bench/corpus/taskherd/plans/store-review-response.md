# Plan: store review response program

- Owner: Tomas Lindgren
- Date: 2026-06-15
- Status: active, reviewed monthly

## Why

The storefronts let developers reply to reviews once, publicly. We currently reply to almost nothing: 6 replies in the twelve months to May 2026, all ad hoc. Meanwhile the reviews that mention a fixed bug keep their old score forever. The program: reply within 5 business days to every review of 3 stars or fewer that describes a concrete bug, and to 5-star reviews that name a specific feature (the "advocacy reply").

## The seeded example

The template set includes one advocacy reply already drafted, for the review we all remember (posted 2026-05-09, 5 stars):

> "herd mode is basically magic — our whole flat plans the week on one board now, and the capture thing means nobody 'forgets' to add the shopping run."

The draft reply thanks the reviewer, names the feature properly (Quick Capture, with a one-line pointer to the gesture in case their flatmates have not found it), and asks nothing. Advocacy replies never contain asks — no "rate us higher," no "tell your friends." The 2026-03 A/B run by Tomas showed asks in advocacy replies correlated with a 0.4-star drop in the reviewer's follow-up activity; we dropped asks permanently.

## Rules of the road

1. **Reply window:** 5 business days from review appearance. Volume is low enough (about 40 qualifying reviews per month as of May 2026) that this is one hour of Tomas's week.
2. **Never argue.** A reply restates what we shipped or what we cannot do yet, and links to one doc: a spec, a plan, or the known-issues page. Reviews alleging misbehavior get the factual pointer, not a defense.
3. **One reply per review, ever.** The storefront allows exactly one; drafting a second means the first was wrong, and the fix is to write better macros, not to wish for exceptions.
4. **Bug reports found in reviews** get filed into the tracker the same day, tagged `from-store`, so the reply can later reference the actual fix. Eleven `from-store` issues were filed in May; two became the impetus for the tumbleweed timer plan's interim fix priority.

## Measured effect

From the 2026-05 cohort analysis: reviews that received a factual reply and whose bug shipped in a later release were edited upward by their authors 34% of the time (sample: 41 reviews). Average rating of replied-to reviewers' subsequent review activity: +0.6 stars versus unreplied cohorts. Small sample, consistent direction, cheap program — Tomas recommends continuing and re-measuring in November.

## Escalation

Reviews reporting data loss bypass the queue and go straight to Priya the same day, with the review text and the account's board identifiers if the reviewer included them. Data-loss replies are written by the engineer who diagnosed the case, not from a macro, because the two we have written (2026-02, 2026-04) each needed specifics no macro could carry.
