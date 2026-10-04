# Runbook — offsite copy rotation (v1)

Status: **superseded by `runbooks/offsite-rotation-v2.md`** (2026-04-06).
Kept in place so the two versions can be diffed; do not follow this one.

## When this runs

The offsite copy turns over every **Tuesday evening**, after the nightly
mirror has finished and before the weekly verify window. Budget 30 minutes of
attention and about two hours of unattended transfer.

## Why rotate at all

There are two endpoints. Rotating means the newest offsite copy is never more
than one cycle old on the current endpoint, while the other endpoint keeps a
slightly older generation as a hedge against the endpoint itself being the
problem (expired cert, quota, the co-op box rebooting into a bad state, etc.).

## Steps

1. Check the nightly mirror went green on `weathervane` (board: *copy ·
   bramble · nightly*). If it did not, stop here and fix that first; rotating
   onto a stale generation wastes the night.
2. Note which endpoint is current. As of this version the pointer file lives
   at `/srv/copy/endpoint.current` on `bramble` and contains either `A`
   (the co-op box) or `B` (the rented storage host).
3. Flip the pointer: `echo B > /srv/copy/endpoint.current` (or `A`, whichever
   is not current).
4. Kick the rotation by hand once to watch it: `systemctl start
   offsite-rotate.service`. Watch the first ten minutes. The two classic
   early failures are DNS (the endpoint names resolve through `dill`, which
   occasionally holds a stale record after the resolver restart) and an
   expired access token — tokens live in the vault under `homelab/core`, and
   the endpoint-A token is the one that has expired twice so far.
5. Once the first snapshot block lands, leave it alone. On this version the
   job retries three times with a fixed ten-minute gap before giving up.
6. After it finishes, prune: snapshots older than the retention window
   (30 days) go, but never prune on the endpoint you just rotated *away*
   from until the next cycle has succeeded once.
7. Update the whiteboard magnet on the rack: endpoint letter and date.
8. Log the rotation in the notebook page taped to the rack door. Yes, on
   paper. It has already paid for itself twice.

## Verification

- `offsite-rotate status` should show the new endpoint current and the
  previous one marked `last-good`.
- Spot-check one file from the newest snapshot block by restoring it to
  `/tmp/rotate-check/` and eyeballing it.

## Rollback

If the new endpoint misbehaves mid-run, flip the pointer back and re-run.
Nothing is lost by rotating twice in one evening except sleep.

## History

- 2025-10-12 — first written, after the September incident where both
  endpoints silently held the same stale generation for eleven days.
