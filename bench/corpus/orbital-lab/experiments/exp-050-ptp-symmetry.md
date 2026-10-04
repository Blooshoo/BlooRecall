# exp-050 — timing-path symmetry

Date opened: 2026-07-21. Owner: Bram Oosterhuis. Status: concluded same day.

## Background

Our phase-timing protocol (the lowercase ptp we run across the cage timing
network) assumes the path delay is near-equal in both directions. Any
asymmetry shows up as a constant offset on the rig's clock — invisible to the
rig, visible to the ledger as a rig that disagrees about when things happen.

## Method

A loop-back box is moved rig to rig; each rig timestamps the same physical
pulse train, and the half-difference of the two directions gives the path
asymmetry directly. 20 rigs measured over one afternoon.

## Numbers

Median asymmetry across the estate: 112 ns. Worst case before attention: rig 7
at 3.4 µs — this was the fiber that got reseated in April, and it measured 210
ns after, so the reseat did its job. Cages A and B agree to 480 ns end to end.

## What the number is for

The skew ledger carries a margin of 400 µs, four
orders of magnitude above anything we measure on a healthy path. That is
deliberate: the margin exists to catch a *broken* path (a card on the shared
bus, a dying fiber), not to referee healthy ones. exp-050's job was to confirm
the margin is still absurdly comfortable, and it is.

## Verdict

Margin stays at 400 µs. Symmetry measurement joins the quarterly drift audit
as a five-minute item. Loop-back box lives in the cage A cabinet, labeled.
