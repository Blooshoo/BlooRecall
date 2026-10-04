# Runbook — offsite copy rotation (v2)

Status: **current**. Replaces `runbooks/offsite-rotation-v1.md` (2025-10-12).
What changed from v1: rotation day moves Tuesday → Wednesday, a checksum
stage gates the "success" declaration, the retry block is formalized, and the
duty-phone paging step is gone (there is no duty phone, there never really
was, it was me in bed with a pager app).

## When this runs

The offsite copy turns over every **Wednesday**, starting after the nightly
mirror window (mirror job fires at 03:17; rotation kicks off on the green
board event, typically 05:30–07:00). Budget 30 minutes of attention and two
to three hours of unattended transfer.

## Why rotate at all

Unchanged from v1: two endpoints, so the newest offsite generation is never
more than one cycle old on the current endpoint, and the other endpoint holds
an older generation as a hedge against the endpoint itself being the problem.

## Steps

1. Check the nightly mirror went green on `weathervane` (board: *copy ·
   bramble · nightly*). If not, stop and fix that first.
2. Note which endpoint is current — pointer file `/srv/copy/endpoint.current`
   on `bramble`, values `endpoint-a` (the co-op box) or `endpoint-b` (the
   rented storage host). (Naming changed from `A`/`B` in v1 so grepping logs
   is less miserable.)
3. Flip the pointer to the other endpoint.
4. Kick it by hand once to watch it: `systemctl start offsite-rotate.service`.
   Watch the first ten minutes. Early failures are still DNS-through-`dill`
   and token expiry (vault: `homelab/core`; endpoint-a's token is the repeat
   offender).
5. **New in v2 — checksum gate.** When the transfer reports done, the wrapper
   verifies the manifest checksums before anything prunes. If the gate fails,
   the job marks the run `suspect` and stops; do not prune, do not flip the
   whiteboard magnet.
6. **Retry block, formalized.** The wrapper reads `retry_policy.max_attempts`
   and `retry_policy.backoff_minutes` from `/etc/offsite/rotate.toml`.
   Current values: `retry_policy.max_attempts = 4`,
   `retry_policy.backoff_minutes = 15`. Four tries with a fifteen-minute
   backoff was chosen because the stalls we have actually seen clear
   themselves in five to forty minutes; more attempts than that just burns
   quota on a dead endpoint. Do not raise these without a stall log that
   justifies it.
7. After the checksum gate passes, prune: snapshots older than the retention
   window (30 days) go. Same rule as v1 — never prune on the endpoint you
   just rotated away from until the next cycle has succeeded once.
8. Update the rack whiteboard magnet (endpoint name and date) and drop a line
   in the notebook page. Paper stays.

## Verification

- `offsite-rotate status`: new endpoint `current`, previous `last-good`, and
  the run marked `verified`, not merely `complete`. In v2 those are different
  states; only `verified` counts.

## Rollback

Same as v1: flip the pointer back, re-run. The checksum gate means a bad
transfer cannot masquerade as a good one, which is the entire point of v2.

## History

- 2026-04-06 — v2 written after the March stall where the job reported
  success on a truncated transfer. See also `notes/incident-review-2026-03-09-vlan-flap.md`
  for the unrelated network mess the same month.
