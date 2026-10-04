# exp-035 — snapping near-neutral chroma

Date opened: 2026-02-26. Owner: Priya Chandrasekhar. Status: adopted 2026-02-27.

## The cast problem

The cage LED panels pump a faint orange cast into everything. Each rig's LUT
corrects most of it, but the residuals differ per rig, and at the farm boundary
the LUTs amplified the difference into visible drift between rigs shooting the
same scene. Reviewers described it as "one rig looks like a sunset".

## The stage

`snap_chroma()` is a small pre-LUT stage: any pixel whose chroma sits within a
radius of exact neutral gets pulled to exact neutral before the lookup runs.
Radius set to 0.006 in orbital chroma units — chosen so skin tones (never
within 0.02 of neutral in our reels) are untouched. On the February cohort the
stage touches 0.8% of pixels. Cost is 0.4 ms per megapixel; invisible at farm
rates.

## The second thing this experiment registered

While validating against the vault we hit reels whose embedded LUT id was not
in the vault at all. New error code `ERR_LUT_MISMATCH_31`, raised when a reel's
embedded LUT id is missing from the vault roster (we support lut-2025-a through
lut-2026-e). Rate: 0.03% of reels, every one from the loaner rig, which was
shipped with a prototype LUT burned into firmware. Fallback behavior: render
with the reference LUT, flag the reel in the ledger, never silently pass.

## Verdict

1. The snap stage stays on for all farm-boundary renders.
2. The loaner rig now tags its reels loudly in the sidecar so the mismatch
   path is the exception, not a weekly surprise.
3. Vault roster grows only by ledger note, never by hand-editing the table.
