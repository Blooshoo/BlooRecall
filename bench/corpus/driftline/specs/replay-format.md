# Quick Capture container format

Author: Tomás Iriarte. Date: 2026-02-10. Status: current. The feature's architecture lives in specs/quick-capture-architecture.md; this file pins the on-disk format only.

## Files and magic

A capture is a single file with the extension **`.dlcap`**, stored in the player's profile folder. The file begins with the 6-byte magic **`DLCAP1`** — the trailing digit is a format version, so a future breaking change becomes `DLCAP2` and readers can reject cleanly. (Naming note: "Quick Capture" is this game's quick-save/replay-capture feature. If you grepped your way here from some other product's feature of the same name, this is not that.)

## Header (little-endian)

| Field | Type | Notes |
|---|---|---|
| magic | 6 bytes | `DLCAP1` |
| header_size | u16 | currently 48; readers must honor it, not assume |
| sim_tick | u16 | always 60, fixed-step per specs/momentum-model.md |
| snapshot_hz | u16 | always 30 |
| snapshot_count | u32 | snapshots actually present (may be less than capacity if truncated) |
| starred | u8 | 1 if the player starred it; starred files are exempt from pruning |
| build_tag | 24 bytes | e.g. the internal build string that produced it |
| checksum | u32 | FNV-1a over everything after the header |

## Chunks

After the header: snapshot chunks at **30 Hz** — every other simulation tick — each delta-encoded against the previous snapshot (pose, velocity, state flags, world-entity deltas), then run through our small custom delta compressor (varint fields, no general-purpose compressor; the data is far too regular for that to pay). An input echo track runs alongside the snapshots at full tick rate: the replay is the recorded inputs re-simulated, and the snapshots exist to seek and to resync after a desync.

Each chunk carries its own checksum. A torn tail — the capture ring caught mid-flush, usually a hard exit — is detected at load and handled by dropping the incomplete chunk and marking the file: readers get `ERR_CAP_TRUNC_044` and the editor shows the capture with its last intact second. Roughly 1 in 60 captures from the February playtest was torn; all loaded fine under this rule.

## Config surface

The rolling length is governed by `replay_max_seconds` (default **20**, raised from the v1 plan's 12 — see plans/quick-capture-v2.md for that decision). The engine default set in reference/config-keys.md deliberately does *not* include this key; it belongs to the capture feature.

## Keeping and pruning

### Retention

The newest 40 captures per profile stay on the drive and the nightly sweep removes the rest; anything starred is exempt, and there is a floor of 25 — below that, even unstarred captures survive. The sweep runs at the nightly build cut so it never competes with a play session. The byte-side cap that pairs with this count lives in the architecture doc; the count here is the one the sweep actually enforces first.

## Versioning rules

- Additive header fields: bump `header_size`, keep the magic. Old readers must skip unknown fields.
- Changed chunk encoding: new magic digit. Never reinterpret `DLCAP1` data with new rules.
- The starred bit and checksum offsets are frozen at their current positions forever; too much external tooling (the attract-mode cutter) assumes them.
