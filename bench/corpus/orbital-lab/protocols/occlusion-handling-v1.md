# Protocol: occlusion handling — v1

Issued: 2025-11-12 by Priya Chandrasekhar.
Status: SUPERSEDED — see protocols/occlusion-handling-v2.md. Kept for the
record; do not follow.

## 1. Hidden stretches

When a subject is hidden from all reference views, hold the box for up to 30
frames. Beyond 30 frames, end the carrier; open a new one on reappearance.

## 2. Re-association

On reappearance, re-associate by appearance histogram: 16×16×8 RGB bins over
the box interior, cosine similarity threshold 0.55 against the carrier's
frozen reference histogram.

## 3. Bookkeeping

Every re-association is logged in the ledger with both histograms' scores, so
disagreements with manual review can be replayed.

## Known problem, noted 2026-01

In crowd reels the histogram confuses carriers who dress alike — which in this
lab is everyone, given the coveralls. Swap rate measured at 2.9% per crossing
in December's sample. Under three subjects the protocol is fine; that is the
regime it was written for.

## Fate

The February rewrite moved re-association to a motion prior and this protocol
was rewritten as v2 in April. v1 remains the reference for the histogram era's
behavior, and for why the 30-frame cap existed: it was tuned to how long the
histogram could be trusted, not to how long a box should coast.
