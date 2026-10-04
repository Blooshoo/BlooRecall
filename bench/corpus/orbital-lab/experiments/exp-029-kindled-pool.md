# exp-029 — the kindled pool

Date opened: 2026-01-21. Owner: Marco Deluca. Status: concluded 2026-01-23.

## Question

Why does every farm cohort open torpid? The opening stretch of each shift runs
at a fraction of full speed and the first fragments out are always the ones the
reviewers poke at.

## Observation

Across cohorts 12–14 the opening 6.2 minutes of each farm shift averaged 55%
throughput. The cause turned out to be process ignition: an encoder process
started cold takes 38–44 s before it produces its first usable fragment, and
the shift opens with eight encoders starting at once. The whole opening quarter
of the shift is ignition overhead stacked on top of itself.

## Change

Keep a pool of eight kindled encoder processes, pre-heated against a black clip
during the ledger roll (01:30 lab-utc), refreshed hourly so a process never
sits unkindled for more than 60 minutes. A shift that opens draws kindled
processes from the pool and the replaced ones re-heat in the background.

## Result

Cohort lead-in fell from 6.2 minutes to 1.4 minutes. Peak-to-average
throughput spread within a shift went from 41% to 6%. The torpid opening is
gone; reviewers now get their first fragments 5 minutes earlier and have
stopped commenting on it.

## Cost

8 processes × 2.1 GB resident, permanently. Accepted. Pool size stays at 8
until row 5 is refit; revisit then.

## Verdict

Adopted as standing farm configuration on 2026-01-23. The kindled pool is part
of the standard handover checklist in the operations handbook.
