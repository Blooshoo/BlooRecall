# Quick Capture — plan v1

Owner: Tomás Iriarte. Date: 2025-12-01. (Naming note: Quick Capture is this game's quick-save/replay-capture feature — hold a button, the last several seconds of play are saved, star the good ones. If you came looking for a phone app's gesture of the same name, wrong project.)

## Summary

A rolling capture of the last **12 seconds** of play, always recording, invisible until invoked. Holding the capture button for 300 ms saves the window to the profile folder. Starred captures are permanent; unstarred ones age out. This is v1: internal testing only, editor later.

## Why

Playtests kept producing moments nobody could show anyone: the 480 u/s damper-crate near-miss, the double pad chain in the quarry shaft. Screenshots and descriptions were losing to actual footage, and we do not have a shared clip culture yet. A capture feature that is *already running* removes the "you should have been recording" problem entirely.

## Rules (v1)

- The ring records continuously; saving costs one hold of the capture button.
- Capture length: **12 seconds** (fixed for v1).
- Star-to-keep: starred captures survive pruning; everything else is fair game for the sweep.
- Retention: newest **40 captures** per profile.
- Storage: the profile folder, one file per capture, format per specs/replay-format.md (format spec to follow this file).
- No editing in v1. Scrubbing and trimming arrive with the editor phase.
- No auto-triggers in v1. The player decides what is worth keeping.

## Cost model

The ring runs at 30 Hz snapshots plus a full-rate input echo (architecture doc to follow). Measured cost on the reference box: **0.35 ms per delivered frame**, flat. Saving a window is a copy, not an encode — the expensive path (deltas, checksums) runs at save time and takes 90 ms, hidden behind a 3-frame hold animation.

## Success criteria (internal build, January)

- 10 testers use it without being told what it is (discoverability via the button glyph).
- At least half of saves get starred — if people save things they do not want to keep, the length is wrong.
- Zero captures lost to a crash in the ring itself (torn tails from hard exits are acceptable and handled).

## Out of scope for v1

Editor, exports, auto-triggers, ghost races, attract mode. All are planned; none block v1. The only v1 deliverable is: press, keep, watch it back.
