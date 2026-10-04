# Thermal postmortem — 2026-01-19

Present: all four. Minutes: Priya. Subject: the melting GPU week
(2026-01-12 to 2026-01-16); saga in the note of the same name.

## Timeline recap

Monday: exhaust 47 °C, dies 91 °C, clocks sagged to 610 MHz, throughput −38%.
Tuesday: fans to 100% made it worse (recirculation through packed filters).
Wednesday: three-way root cause — heating loop overshoot (facilities), row 2
filters packed since before kickoff, poster blocking renderlet-17's intake.
Thursday: fixes applied, dies back under 83 °C. Friday: fan curve v3 shipped,
throughput to 97% of baseline.

## What worked

The exhaust probes told the truth the whole week; nothing in the monitoring
lied. The night operator's Tuesday log ("farm is very warm and very slow")
was, in retrospect, accurate triage.

## What did not

- No filter rotation existed at all. Nobody owned filters.
- Fan control was keyed to die temperature, which oscillates; the room is the
  slower, honest signal.
- The farm shed no load when throttled — it just got slower, and nobody
  watching the queue knew why.

## Actions

1. Filter rotation quarterly, Bram's calendar, starting 2026-04. Done since.
2. Fan curve v3 keyed to exhaust probe. Shipped 2026-01-16.
3. Scheduler refuses new fragments at a die reading of 83 °C. Landed with the
   topology note on 2026-01-22.
4. Facilities loop controller added to the quarterly audit alongside the
   clock check.

## Carried

Row 5 refit proposal (the stragglers run hot relative to their output) is
deferred to the autumn roadmap. Ingrid's closing note: the week cost us four
points of throughput for five days and bought us a maintenance culture;
acceptable trade, once.
