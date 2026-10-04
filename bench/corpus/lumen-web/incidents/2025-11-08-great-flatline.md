# Incident 2025-11-08 — the Great Flatline

Severity: SEV-2. Author: Rafa Lindqvist. Postmortem finalized 2025-11-10.

## What we call it

"The Great Flatline": for 90 minutes every chart on every board drew a flat line at zero, which looked exactly like total data loss and was actually nothing of the kind. Teammates still say "flatter than November" when a fixture breaks.

## Timeline (UTC)

- 14:05 — sampler deploy v3.9.3 lands.
- 14:07 — the coalescer begins emitting a single zero sample whenever an upstream poll returns empty, instead of skipping.
- 14:28 — first human notice: a design partner's uptime board reads 0%. Dot catches it mid-demo call.
- 14:51 — root cause found in the coalescer's empty-poll branch.
- 15:20 — rollback complete; boards self-heal on their next refresh.
- 15:35 — full recovery confirmed on all boards.

## Impact

Ninety minutes of flat charts. Zero actual data loss — empty polls are genuinely empty; the zeros were display-only. Detection took 23 minutes because zero is a "valid" value and nothing alarmed on it.

## Root cause

Deploy v3.9.3 changed the coalescer's empty-poll branch from `skip` to `emit(0)`. The change was written for the synthetic heartbeat sampler and rode along in the same pull request aimed at the metric sampler.

## Actions

1. Skip-and-mark instead of emit(0) — hotfix v3.9.4, shipped 2025-11-10.
2. Coverage-ratio alarm: boards compute the share of expected series actually reporting; below 90% pages the data tier. Landed 2025-11-14.
3. One pull request, one sampler — process rule, still in force.
