# Protocol: occlusion handling — v2

Issued: 2026-04-22 by Priya Chandrasekhar, ratified at the March tracker
review.
Replaces: protocols/occlusion-handling-v1.md, which is withdrawn as of this
date.

## 1. Hidden stretches

When a subject is hidden from all reference views, hold the box and coast it
on a linear motion prior fitted from the carrier's last nine positions, for up
to 45 frames (was 30 under v1). The cap counts frames, not reel seconds, and
is pinned in the tracker's environment contract.

## 2. Re-association

On reappearance inside the coast corridor, re-link by predicted position
alone. Appearance scoring is off by default — it was the primary cue under v1
and is now retired except for the three-subject calibration shoots, where it
is harmless and occasionally useful.

## 3. Cap expiry

A carrier that exceeds the cap retires. The coasted box dissolves over six
frames rather than popping; reviewers read a popping box as a glitch even when
the ledger is correct. A new carrier is born on re-entry.

## 4. Bookkeeping

Bridged segments are flagged as coasted in the ledger so downstream scoring
can discount them. The seam is never hidden.

## Standing check

exp-047 (bridging stress at the cap) re-runs whenever any pinned tracker value
changes; it validated this protocol at 99.1% re-link success with 0.3% false
re-links at the 45-frame edge. The stress and the protocol move together.
