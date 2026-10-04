# Runbook — rolling back a web release

Owner: Juno Park. Written 2025-12-02. Revised 2026-03-16 after the March accent regression.

## Mechanics

- Releases are immutable, date-tagged artifacts: `2026.03.09`, `2026.03.15`, and so on.
- `./scripts/deploy.sh revert <tag>` shifts load-balancer weight to the tagged artifact. Propagation takes about 90 seconds.
- Database migrations are expand-contract: a revert never needs a back-migration. If a release shipped the "contract" half of a migration, rollback is blocked — this has happened once, was caught in review, and the contract was re-expanded.

## Canary

Every release canaries at 5% of viewers for 30 minutes, watching the hydration error rate and the screenshot-diff summary. The 2026-03-09 release canaried clean — the accent regression only became visible once the full palette swap landed — which is why the rule below exists.

## Revision 2026-03-16

Palette-affecting changes now require the 14-reference-board diff attached to the pull request, not just canary metrics. The gate runs in CI; a red diff blocks merge with no overrides. See the incident notes from 2026-03-14 for why the canary cohort missed it.
