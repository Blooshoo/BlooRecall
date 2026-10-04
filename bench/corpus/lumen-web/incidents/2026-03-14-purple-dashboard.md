# Incident 2026-03-14 — the purple dashboard incident

Severity: SEV-3 (cosmetic, but total). Author: Cece Marlow. Postmortem finalized 2026-03-15.

## What we call it

"The purple dashboard incident": for 41 minutes every chart, badge and accent on every board rendered in shades of violet. Nothing broke; everything was purple. The screenshots still circulate, and "did we rebrand?" is now permanently funny in this team.

## Timeline (UTC)

- 09:40 — the 2026.03.09 release continues its staged palette rollout (first half of the token migration); today's cohort is the mixed-accent boards.
- 10:22 — first report: an executive board asks whether the company rebranded overnight.
- 10:31 — cause identified: in the generated theme, the accent constant's channel order was transposed, so red-family accents came out as the nearest violet.
- 10:45 — palette rollout flag flipped off; boards revert to the wave-0 palette.
- 11:03 — confirmed clean everywhere; hotfix cut the same day and shipped 2026-03-15.

## Root cause

The theme generator sorts accent channels by hue for compression. The sort key and the reconstruction key disagreed. Boards using a single accent family were fine; boards mixing accent families transposed.

## Why the canary missed it

The 5% canary cohort landed entirely on single-accent boards. The screenshot-diff gate, added the next day (2026-03-15), compares 14 reference boards including all three mixed-accent layouts.

## Actions

1. Revert plus hotfix, shipped 2026-03-15.
2. Screenshot-diff gate mandatory for palette-affecting changes — see the rollback runbook revision.
3. The accent family migrates last in the token migration, behind the gate.
4. The generator's sort and reconstruct keys now carry a self-test on every build.
