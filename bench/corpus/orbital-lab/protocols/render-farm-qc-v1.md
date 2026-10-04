# Protocol: render farm QC — v1

Issued: 2025-12-08 by Marco Deluca.
Status: SUPERSEDED — see protocols/render-farm-qc-v2.md. Do not follow this
version; it is kept for the record.

## 1. Sampling

After each farm shift, the operator pulls three finished clips by hand — one
per row in rotation — and plays them against the cage master on the review
console.

## 2. Reference comparison

Each pulled clip is scored as PSNR against the cage master. Threshold: 38 dB
per fragment. A clip under threshold fails the shift.

## 3. Log

The operator appends a line to the paper QC binder: date, shift, three clips,
three scores, initials. The binder lives on the shelf by the review console.

## 4. Escalation

Two consecutive failing shifts pages Marco. One failing shift gets a re-pull
of two more clips before it counts.

## Rationale, as written at the time

The farm finishes fewer than 40 clips a night, so hand sampling is cheap and
the operator's eyes catch the failures that scores miss. Revisit when the farm
outgrows this.

## History note

That revisit came in March 2026: the farm doubled its nightly output, hand
sampling stopped covering the roster, and v2 automated the lane and revised
the gates. v1 remains withdrawn; the binder is in the archive box labeled
"QC paper 2025-12 to 2026-03".
