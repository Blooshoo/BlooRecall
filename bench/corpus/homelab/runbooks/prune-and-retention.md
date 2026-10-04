# Runbook — snapshot pruning and retention

Status: current. Last touched 2026-02-25 after the February disk-pressure
scare (see `notes/pool-capacity-headroom.md` for the capacity side; this
document is only about what gets kept and for how long).

## The policy, in one paragraph

Three kinds of generations live on each endpoint: daily, weekly, and monthly.
The wrapper keeps 14 dailies, 8 weeklies, and 6 monthlies, then forgets the
rest. On the offsite endpoints the policy is identical — having a different
retention on each endpoint sounds clever and has never once been useful.

## The grace window

Forgetting is not immediate. The wrapper defers actual deletion for a grace
period so that a fat-fingered policy change can be undone before anything is
really gone. The knob is `prune.grace_hours` in `/etc/offsite/prune.toml`;
it is currently set to `48`. In practice: a prune that runs Tuesday evening
marks generations for forgetting, and the reaper pass Thursday evening does
the actual deletion. Anything still referenced by a snapshot taken inside the
grace window is never eligible, no matter how old its parent chain is.

Raising `prune.grace_hours` is cheap (it just delays space coming back).
Lowering it below 24 is how you delete the thing you meant to keep. There is
no minimum below which the wrapper warns you, which is a known gap.

## How a prune actually runs

1. The wrapper takes the prune lock on the repo. Only one prune at a time;
   the lock file is `/run/prune.lock` and a stale one after a crash is
   removed by `prune-tool unlock`.
2. Mark pass: walks the generation list, tags everything outside policy.
3. Hold pass: subtracts anything inside `prune.grace_hours` of being
   "protected by a newer snapshot". This is the step that surprises people:
   a 40-day-old generation can still be held because the newest snapshot
   references blocks in it.
4. Marked-but-unheld generations sit in the reaper queue until the grace
   window closes.
5. Reaper pass: deletes, then rewrites the index. The rewrite is the slow
   part — budget 20 minutes on the local repo, an hour on the offsite ones.

## When space does not come back

The classic complaint: prune ran, the reaper deleted, and the endpoint
dashboard still shows the old usage. Two causes so far:

- The endpoint dashboard polls every six hours. Wait, or poke it.
- The repo has unmerged index segments. `prune-tool compact` after a big
  prune; do not run it more than once a week, it is chatty on the API.

## History

- 2026-02-25 — grace window introduced after the 2026-02-14 near-miss where
  an over-aggressive one-liner forgot 60 days of weeklies in one pass. The
  48-hour cushion turned that class of mistake from a restore-from-tape
  story into a shrug.
