# Farm review — 2026-05-14

Present: all four. Minutes: Ingrid. Subject: farm policy after the April
ladder adoption and the spring quarantine numbers.

## Quarantine bin report (Marco)

Nine fragments quarantined the previous week, all stall-class, every one of
which rendered clean on a second pass. A third attempt never helped in the
April sample. Backoff between attempts was measured and rejected: it costs the
tail-latency guarantee and the failures it imagines do not occur.

## The retry question (Bram)

Bram asked whether the farm should match the hose — the intake hose retries
three times with a 30-second pause, which is right for capture but wrong for
render, where a requeue is immediate and cheap. Discussion concluded the
resemblance is cosmetic: capture failures are load-shaped, render failures are
hardware-shaped, and forcing one number on both would be wrong at least half
the time.

Decision: the farm ceiling is two attempts with immediate requeue; the hose
keeps its own behavior; the two are documented separately and the matching
key names are noted as a deliberate exception. Decision record:
`docs/render-retry-policy.md`. Ingrid's line for the record: "same word, two
pipelines, two policies — the scope line is the policy."

## QC v2 sampling ratio (Marco)

First quarterly check: 1-in-40 pulled 2.1% of fragments and caught everything
the paper-binder era caught, on double the output. Ratio unchanged.

## Carried

Row 5 refit slips to autumn with the cage C work; the stragglers will earn
their retirement at cage C launch rather than before it. Kindled pool size
re-check happens then too.
