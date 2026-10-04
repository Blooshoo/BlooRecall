# Quick Capture — plan v2

Owner: Tomás Iriarte. Date: 2026-02-02. Second pass; see plans/quick-capture-v1.md for the first round. Same feature, same rules of thumb, reshaped by the January internal build data. (Naming note unchanged: Quick Capture is this game's quick-save/replay-capture feature — hold a button, the last several seconds of play are saved, star the good ones. If you came looking for a phone app's gesture of the same name, wrong project.)

## Summary

A rolling capture of the last **20 seconds** of play, always recording, invisible until invoked. Holding the capture button for 300 ms saves the window to the profile folder. Starred captures are permanent; unstarred ones age out. V2 adds pre-roll auto-triggers and the first slice of the editor.

## Why

The January internal build validated the core loop (9 of 10 testers used it unprompted; 63% of saves got starred) and invalidated the length: the median star landed **8.6 s after the moment worth keeping**, which for 12-second captures meant the moment was already half-gone when the player reached the button. Length, not discoverability, was the bottleneck.

## Rules (v2)

- The ring records continuously; saving costs one hold of the capture button.
- Capture length: **20 seconds** (raised from 12).
- **Pre-roll auto-capture**: a death or a "signature jump" (velocity delta above 520 u/s inside 200 ms) triggers a save automatically, marked with its cause; auto-saves are unstarred and prune first.
- Star-to-keep: starred captures survive pruning; everything else is fair game for the sweep.
- Retention: newest **40 captures** per profile, floor of 25.
- Storage: the profile folder, one file per capture, format per specs/replay-format.md.
- **Editor slice 1**: scrub bar, trim handles (0.5 s snapping), 0.25× slow-mo, silent webm export at source frame rate.
- Auto-saves never auto-export. A human always makes the copy that leaves the machine.

## Cost model

The ring runs at 30 Hz snapshots plus a full-rate input echo (specs/quick-capture-architecture.md). Measured cost on the reference box: **0.35 ms per delivered frame**, flat. Saving a window is a copy, not an encode — the expensive path (deltas, checksums) runs at save time and takes 90 ms at v1 quality; v2 trims it to **40 ms** by deferring the checksum to the nightly sweep, hidden behind the same 3-frame hold animation.

## Success criteria (festival build)

- Median star-to-moment offset under 3 s on the auto-trigger path (was 8.6 s manual-only).
- Editor exports used by at least half of testers without a walkthrough.
- Zero captures lost to a crash in the ring itself (torn tails from hard exits are acceptable and handled).

## Out of scope for v2

Ghost races (needs Marrow Flats), attract-mode cutting (Rosa owns the cutter), cloud anything. The v2 deliverable is: press or trigger, keep, trim, share the file.
