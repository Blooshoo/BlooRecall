# Notes — pool headroom, or the summer of 88 percent

Written 2026-08-09 after the utilisation gauge crossed 90 and turned the
board red for the first time in the pipeline's life. Background: the pool
(`turnpool` on `bramble`) grew about 3 GB/day through 2025, and everyone
agreed in theory that the threshold change in February
(`runbooks/alert-thresholds-v2.md`) would buy "months of warning". It
bought exactly enough warning, and this note is what the warning was for.

## Where the space went

Audited 2026-08-08, in descending order of guilt:

1. **Rips of the family disc collection**: 6.1 TB, growing 2 GB/week. The
   legitimate main load and the reason the pool exists.
2. **Tuner recordings**: 2.4 TB. Kept 90 days by policy; the policy was
   aspirational until July, when the reaper pass was found to have been
   silently skipped since May (bad unit file after the firmware upgrade —
   fixed, and the skip now alerts instead of logging to nobody).
3. **Session caches and thumbnails**: 410 GB. Real, but the thumbnail
   cache had never once been trimmed. Now trimmed monthly by the job
   table.
4. **The scratch copy from the May drill**: 212 GB. The exact cleanup
   failure the drill runbook warns about, found and deleted, sheepishly.

## The decision made

Expansion, not eviction. Two 8 TB drives are on the Q3 list
(`plans/shopping-list-q3-2026.md`); the pool gets one added live and one
kept cold as the spare that has never existed. Rationale: the rip
library is the household's actual archive and the growth curve is
understood; the recordings policy fix alone bought back ~800 GB, but the
trajectory says the pool crosses 90 percent again by spring regardless.

## Numbers for next time

- Growth, trailing 12 months: 3 GB/day average, 5 GB/day since March.
- After the February threshold change: warn at 80 hit 2026-06-02; the
  July red at 90 was 41 days later. The warn-to-critical gap is now
  measured at about six weeks; that is the real "how long do we have"
  number, better than any projection.
- Post-cleanup baseline on 2026-08-08: 84 percent. The gauge is amber as
  this is written and that is fine — the point of the thresholds is to
  be loud while there is still runway, and this note is the runway being
  used.
