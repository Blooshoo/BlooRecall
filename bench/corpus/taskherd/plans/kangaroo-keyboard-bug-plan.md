# Plan: the kangaroo keyboard bug

- Owner: Dmitri Vale
- Date: 2026-06-08
- Status: fixed — shipped in the 2.8 patch line (2.8.3, 2026-06-22)

## The name

Dmitri named it on 2026-05-27 in the client channel: "the composer hops when I start typing, like a kangaroo." The name stuck, and it appears in the support macro library as shorthand, so this document records it formally: **the kangaroo keyboard bug** is the input view jumping — the whole task composer, keyboard and all — bouncing up by its inset height and settling back, typically when the first character is typed into a new task title.

## Symptoms

- The composer view jumps once, 120 to 180 px, then settles within 300 ms.
- It happens on the first keystroke of a fresh title, most often right after the keyboard finishes its open animation.
- Cursor position is preserved; no text is lost. It is motion sickness, not data loss.
- Frequency: about 1 in 6 fresh titles on affected builds; never reproduced on tablets.

## Reproduction

1. Open any board and tap the compose field.
2. Let the keyboard finish its open animation (roughly 250 ms).
3. Type any character immediately.
4. On affected builds, the composer and keyboard hop together.

## Root cause

The inset animation listener was being registered twice during the compose-field focus transition — once by the board fragment and once by the composer overlay that Quick Capture introduced in 2.4.0. Each listener applied the keyboard inset as an animation offset, so the offset was applied twice in the same frame. The timing dependency on the keyboard's open animation explains why it never reproduced on tablets: their inset animation completes before focus lands, so only one listener was ever live.

## Fix

- De-duplicate the inset listener registration: the composer overlay now defers to the board fragment when both are in the foreground tree (PR merged 2026-06-11).
- Guard: the inset offset application is idempotent per frame — a second application in the same frame is a no-op by design now, so this class of double-apply bug cannot recur in the composer.
- Regression test added to the client animation suite on 2026-06-12; it replays the exact focus-then-keystroke timing.

## Ship and verification

Shipped in patch 2.8.3 on 2026-06-22 to 100% of the Android fleet in 5 days. Hop reports from the client diagnostics dropped from 340/day to 4/day within a week; the residual 4/day are all on the two third-party launcher builds noted in `specs/quick-capture-gesture.md` (wide gesture zones), tracked separately and not expected to reach zero.

## Follow-ups

- The Quick Capture overlay's lifecycle hooks get a review pass in 3.1 to make sure no other overlay can double-register (owner: Dmitri, due 2026-10-30).
- Support macros referencing the hop were updated to link here instead of the old channel thread.
