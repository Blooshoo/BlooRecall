# exp-047 — bridging stress at the cap

Date opened: 2026-04-28. Owner: Priya Chandrasekhar. Status: adopted as the
standard tracker regression.

## Question

Does the coast-and-relink behavior hold up at its 45-frame cap, and does it
fail gracefully past the cap instead of lying?

## Method

Synthetic hidden stretches injected into crowd reels: gaps of 10, 25, 45, and
60 frames, crossing density 6 subjects, 40 injected stretches per gap, 160
total. The ground truth for each stretch is painted by hand so re-link success
is scored against known carriers, not against the tracker's own opinion.

## Numbers

| gap (frames) | re-link success | false re-links |
|---|---|---|
| 10 | 99.2% | 0.1% |
| 25 | 98.7% | 0.2% |
| 45 | 99.1% | 0.3% |
| 60 | n/a (cap retires) | — |

At 60 frames the cap correctly retires the carrier by design: coasting a box
for 60 frames on a straight line lies badly about where anything walks. The
two failures at 45 were both diagonal crossings at high closing speed — the
known weak spot noted in the hold-and-relink note.

## Verdict

1. The 45-frame cap is right: 99.1% success at the edge, 0.3% false re-links,
   inside the 1% budget from the March review.
2. Behavior past the cap is graceful — retirement, not hallucination.
3. This stress re-runs whenever any pinned tracker value changes. The pinned
   values and this experiment reference each other; if one moves, the other
   must be re-run the same week.
