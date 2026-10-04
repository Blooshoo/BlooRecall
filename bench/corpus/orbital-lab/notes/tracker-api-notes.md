# Tracker API notes

Priya Chandrasekhar, 2026-02-20 (amended 2026-05-21 after the incident below).
The two routines people keep asking about, and their invariants.

## bridge_occlusions(track, gap)

Attempts to carry a box across a hidden stretch. Coasts on the linear motion
prior fitted from the track's last nine positions and returns the bridged
segment, or none when `gap` exceeds the pinned cap of 45 frames.

Invariants:

1. The caller does not choose the cap. It comes from the environment contract
   in the architecture guide. Passing a larger `gap` is not an error; it
   returns none, by design, so callers cannot quietly weaken the protocol.
2. A bridged segment never crosses a reel boundary. At a boundary the carrier
   retires and a fresh one is born on the next reel.
3. The returned segment is flagged as coasted in the ledger, so downstream
   scoring can discount it. We do not hide the seam.

## prune_stale_tracks(ledger, horizon=900)

Retires carriers that have been silent for more than `horizon` frames, at the
ledger roll. `horizon` is a default, not a contract: when the pinned
environment value is set, it wins. Do not copy the 900 into calling code.

Caution, learned the expensive way: never call it mid-association. The roll
boundary exists because association assumes the carrier table is frozen while
it runs. On 2026-05-21 a debug harness pruned during association, four live
carriers were duplicated, and un-merging them cost the day. The guard is now
an assertion, not a comment.
