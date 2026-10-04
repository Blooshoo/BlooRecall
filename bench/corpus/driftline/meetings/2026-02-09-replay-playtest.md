# Quick Capture playtest review

2026-02-09, 13:00–14:00. Attendees: Priya Raman, Tomás Iriarte, Dev Okonkwo, Marisol Vega (first 20 min). Notes: Priya. Data: 8 testers, one week with the Quick Capture v1 build (12 s ring), 214 captures collected.

## Numbers

- 9 of 10 internal-build testers used capture without being told (v1 success criterion met; the tenth said they "forgot it was there", which is a discoverability win we'll take).
- 214 captures in one week; **63% were starred** (criterion was "at least half").
- Of the starred captures, **61% were of deaths or near-deaths**. People star their failures. We built a highlight reel and the players built a blooper reel, and the players are right.
- Median time from the star-worthy moment to the star press: **8.6 seconds**. On a 12-second ring that means the moment was already half-gone for the median star. This is the headline.
- Torn tails: 3 of 214 (1.4%), all loaded cleanly with the truncation rule (`ERR_CAP_TRUNC_044` path). No data loss complaints.

## Decisions

1. **Ring goes 12 s → 20 s.** Written up as plans/quick-capture-v2.md. The 8.6 s median is the argument; nobody in the room argued for keeping 12.
2. **Pre-roll auto-capture on death** ships in v2, marked with its cause, unstarred, prunes first. The blooper-reel finding says deaths are the content; make saving them free.
3. Editor slice for v2: scrub, trim, slow-mo, silent webm export. Trim is first because starred captures cluster around a moment with slack on both sides.
4. Marisol's note for the perf budget: captures must never compete with the presentation path at save time — the 90 ms save already hides behind the hold animation, keep it that way when the length changes.

## Left the room unresolved

- Ghost races on Marrow Flats want capture data as an input; Dev and Tomás to sketch what a ghost line reads from a capture (spec later; nothing blocks v2).
- Attract-mode cutting (Priya) — Rosa's cutter tool proposal, pending her start date.
