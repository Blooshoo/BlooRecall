# Drift audit — June 2026

2026-06-18 — Bram Oosterhuis. Quarterly audit of clock agreement across the
capture rigs. Ritual since 2025-11; kept quarterly even when boring, because
the quarter it is skipped is the quarter it is needed.

## Method

The clap-board rig fires a flash; every rig records when it saw the flash; we
tabulate the spread of the readings against the reference card. Two passes
per rig, morning and night, so temperature-dependent paths show themselves.

## Findings

- Rig 3 coasted 1.9 ms late for the entire quarter. Cause: the fan swap of
  2026-04-30 left its timing card on the shared bus instead of the dedicated
  slot. At 240 fps a frame lasts 4.17 ms, so every crossing judgment that used
  rig 3 as the reference view was reading boxes half a frame early.
- Rig 7 improved after the April fiber reseat: 3.4 µs down to 210 ns. The
  reseat note in the skew ledger is confirmed by this audit.
- Cages A and B agree to 480 ns end to end. Night pass matched the morning
  pass everywhere except rig 14, which drifts 40 ns warmer — logged as a
  pattern, not a fault.

## Why the April stress test missed it

The bridging stress (exp-047) ran mostly on rig 7 reels, which were clean.
This is the audit doing its job: the fault was invisible to every single-reel
check and obvious in the cross-rig table.

## Actions

Rig 3's card moved to the dedicated slot on 2026-06-15; margin re-verified;
ledger updated. exp-051 scheduled to re-run the bridging stress on rig 3
reels. The audit keeps its quarterly slot.
