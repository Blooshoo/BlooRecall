# Protocol: the freezer

Issued 2026-02-09 by Ingrid Halvorsen. "The freezer" is the read-only shelf of
frozen benchmark cohorts. It is a shelf, not a machine; the name came from
Bram and, like most of Bram's names, it stuck within the hour.

## What may be frozen

A cohort becomes frozen when: (1) its reels all pass boundary reconciliation,
(2) its digests verify, and (3) someone with a benchmark need signs the freeze
note. Freezing adds a tag and a manifest of digests. A frozen cohort never
changes; if it is wrong, it is retired, not patched.

## Thawing

Thawing means copying to scratch with the freeze tag in the path — the tag
rides along so nobody confuses thawed scratch with live capture. Copying back
is forbidden: anything written during an experiment lands in scratch under a
different name and never carries the tag.

## Current contents

- The February cohort is the benchmark reference for all tracker work; see the
  dataset page under `docs/` for its roster and counts.
- The November cohort was retired to the cold shelf on 2026-03-01 after the
  rewrite benchmarks concluded. It is still readable, but no new benchmark may
  be pinned to it — the histogram-era numbers all live there and mixing eras
  is how we got the confusing March draft tables.

## Discipline

The freezer list is short on purpose. Every frozen cohort costs vigilance:
digests re-verified at every quarterly audit, space reserved, retirement
decisions eventually due. When in doubt, freeze later rather than now.
