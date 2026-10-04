# Feature review — Quick Capture staged rollout

- Date: 2025-11-17, 45 minutes
- Attendees: Maya Okafor, Dmitri Vale, Tomas Lindgren; Priya Raghunathan excused (storm-guard work), written input appended
- Subject: `specs/quick-capture-gesture.md`, in staged rollout since 2025-11-10; the 2.4.0 train goes wide on 2025-11-24

## Telemetry (first staged week, 5% of accounts)

- Adoption: 34% of new tasks created via capture (target was 30% at 60 days — we passed it in week one).
- Median capture-to-save: 3.9 seconds; p90: 9.4 seconds.
- Draft recovery (quick-save) used by 12% of capturers; 88% of recovered drafts were completed to save. The quick-save is doing its job.
- The replay row is the story: 61% of captures went to a replayed board chip rather than the default. The "instant replay of your last three boards" row is carrying the feature.

## Discussion

- **Dmitri, gesture conflicts:** the accidental-trigger rate measured 0.19% fleet-wide, concentrated on the two wide-gesture launcher builds flagged in the September spike. He proposes shipping as-is and tracking, rather than adding a dismiss-tolerance heuristic that would slow the gesture for everyone. Agreed.
- **Maya, haptics:** the double-tick on save tested as "confirms it stuck" in the beta interviews; she wants to keep it despite one reviewer calling it "the world's smuggest vibration." Kept — Tomas: "we do not redesign haptics on one review."
- **Priya (written):** capture pushes are class-1 (user-visible edits) in the upcoming rate-limit model, so heavy capturers cannot starve their neighbors. No objection to ship.
- **Tomas, the wording question:** marketing wants to call the replay row "instant replay" and the drafts "quick-save." The team agreed both terms are fine as long as specs keep the formal names — replay of board targets, quick-saved drafts — so support can map complaints to mechanics.

## Decisions

1. Gesture ships unchanged; wide-gesture launcher builds get a tracked footnote, not a fix.
2. Quick-saved drafts expire after 24 hours (as speced); the "recover draft?" bar wording was simplified after the funnel review.
3. Replay-of-last-boards default: on for everyone, no setting. Settings that restate defaults are how we got 14% of boards demoting notifications.
4. Success re-review at 60 days post-train (late January agenda slot), with the 30% share target to beat.

## Action items

- Maya: capture share and latency on the product dashboard by 2025-12-01.
- Dmitri: footnote the launcher builds in the spec (done, see spec section on gesture conflicts).
- Tomas: reply template for capture-related store reviews (folded into the review program that followed in June).
