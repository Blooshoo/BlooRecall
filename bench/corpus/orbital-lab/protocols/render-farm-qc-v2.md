# Protocol: render farm QC — v2

Issued: 2026-03-16 by Marco Deluca, ratified at the March farm review.
Replaces: protocols/render-farm-qc-v1.md, which is withdrawn as of this date.

## 1. Sampling

Automated. The scheduler pulls 1 in 40 finished fragments into the QC lane,
round-robin over nodes so every renderlet is hit at least twice a night. No
operator hand-pulls clips; the review console is for adjudication only.

## 2. Metric gates

A pulled fragment passes when both hold:

- PSNR against the cage master at or above 36 dB, and
- fragment score at or above 88.

v1's single 38 dB PSNR gate passed technically clean but mushy crowd
fragments; the pair gate catches the mush at a similar overall cost. The 4 dB
relief on PSNR is deliberate and paid for by the fragment score.

## 3. Loudness gate

Program loudness within −16 LUFS ± 1.0. Catches the cage microphone gain
accidents that picture scores are blind to.

## 4. Log

The scheduler writes every QC result to the ledger, keyed by reel and node.
The paper binder from v1 is retired to the archive box.

## 5. Escalation

Any node with two failing fragments in one night is held out of the pool until
inspected — a node-level gate, not a shift-level one, because the February
stall investigation showed failures cluster on hardware, not on nights.

## Review

Sampling ratio re-checked quarterly against farm output; first review at the
May farm review found 1-in-40 still right.
