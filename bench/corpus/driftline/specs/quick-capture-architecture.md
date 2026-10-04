# Quick Capture — architecture

Author: Tomás Iriarte. Date: 2026-03-02. Status: current as of 0.13.0, updated for the v2 plan's decisions. This is the deep document behind plans/quick-capture-v1.md and plans/quick-capture-v2.md. The on-disk format is pinned separately in specs/replay-format.md and is not re-derived here.

---

## Purpose and history

Quick Capture is driftline's always-running replay capture: the game continuously records the last 20 seconds of play, and holding the capture button for 300 ms saves that window into the player's profile. Starred captures are permanent; unstarred ones age out on the nightly sweep. Auto-triggers save deaths and signature jumps without a button press. An editor slice lets players scrub, trim, slow down, and export the result.

The feature exists because of a kickoff-meeting demo: Tomás played a 90-second quarry run, hit a damper crate near-miss at 480 u/s, and nobody could reproduce it afterward. Screenshots and verbal retellings lost to actual footage every single time we tried. The pillar-level justification is written in the kickoff notes; the practical one is that a game about *speed you can read* needs a way to show someone what "reading speed" looks like, and the best evidence is the run itself.

The v1 plan (December) shipped the ring, the button, and star-to-keep, internal-only, 12-second window. The February playtest moved the window to 20 seconds, added auto-triggers, and pulled the editor forward; that is the v2 plan, and the numbers justifying each change live in meetings/2026-02-09-replay-playtest.md. This document describes what ships in v2 and what it costs.

## Product rules (fixed for v2)

These are the rules the architecture is not allowed to violate:

1. **Always recording.** The ring runs from boot to shutdown with no user-visible switch. A capture feature you have to remember to arm has already failed at its only job.
2. **Saving is cheap and invisible.** The save path costs at most 40 ms of withheld work, hidden behind the 3-frame hold animation. Testers read an uncovered pause as a crash — this shipped wrong once (0.16.0) and the fix is pinned in the ship checklist.
3. **Star-to-keep, with a floor.** Newest 40 captures per profile, or 200 MB, whichever binds first; never fewer than 25 surviving even if the byte cap argues otherwise. Starred captures are exempt from pruning and from the byte cap's interpretation.
4. **The player's own effects never break to save memory or CPU.** The retirement order in the renderer protects player-owned effects last; the capture path abides by the same principle — the ring degrades before gameplay does, never after.
5. **A capture is a replay, not a video.** Files are small, seeks are instant, and the ghost-line feature on Marrow Flats can consume the same data. This rule shapes everything below.

## Requirements trace

For every product rule, the architectural commitment that delivers it:

- Rule 1 is delivered by the ring living inside the simulation loop, not beside it: snapshots are produced by the tick itself, so there is no capture process that can be forgotten, crashed, or OOM-killed independently of the game.
- Rule 2 is delivered by the two-phase save: the button press copies the ring window (cheap, bounded) and defers encoding to a background task with a hard withholding budget measured against the presentation path.
- Rule 3 is delivered by the retention sweep running at the nightly build cut, never during a session.
- Rule 4 is delivered by the capture path's fixed 0.35 ms per-frame cost being paid from the *slack* the renderer's budget reserves, never from another stage's line.
- Rule 5 is delivered by the deterministic-replay design: the authoritative payload is the recorded input timeline, and snapshots exist for seeking and resyncing. Everything else is derived.

## The capture pipeline

### What the ring records

Three channels, produced by the simulation tick at its native 60 Hz:

1. **Player channel** — Ember's full gameplay state each tick: pose index, position, velocity, charge, cling state, grounded flag, the coyote window's remaining time, and the RNG stream position. Serialized this is roughly 96 bytes per tick.
2. **World-delta channel** — only entities whose state differs from the world's entry defaults, delta-encoded each tick. On the quarry this is nearly empty; during a kiln vent storm it carries the vent columns and the breakable tiles, and runs 400–900 bytes per tick.
3. **Effects channel** — markers, not data: which emitters started, stopped, or changed policy this tick, plus the charge gate transitions. Tens of bytes per tick on a busy frame. Effects are *rebuilt* at playback, never stored (see the determinism section for why this is load-bearing).

Downsampling to 30 Hz happens at save time, not record time: the ring stores all 60 Hz ticks (they are cheap; see the sizing section), and the saved file carries every other tick as snapshots with the full-rate input echo alongside, per the format spec. Recording at full rate costs nothing extra and keeps the door open for a future slow-motion-accurate export without changing the ring.

### The input echo

Alongside all three channels, every press and stick sample is appended to an echo track with its poll timestamp. The echo is the *authoritative* payload: playback re-simulates from the echoes, exactly as the game itself would have consumed them, and the snapshots serve two narrower purposes — instant seek (start playback at any saved snapshot instead of from zero) and resync (after N ticks of playback, compare simulated state to the nearest snapshot and correct any drift; see the determinism section).

This split — inputs authoritative, snapshots for seek and repair — is the most important decision in the document. It is why a 20-second capture file averages 1.9 MB instead of the 60-plus MB a naive video capture would weigh, why seeks are instant, and why the ghost lines can consume captures as input data without a separate recording format.

### The save path

Pressing and holding the capture button starts a 300 ms hold; on completion, the save runs in two phases:

- **Phase 1 (the copy, budgeted at under 4 ms):** the ring window [now − 20 s, now] is copied out of the ring buffers into a staging buffer. This is a straight copy of ~4.3 MB (see sizing) and runs inside the frame; the 3-frame hold animation covers it completely.
- **Phase 2 (the encode, budgeted at 40 ms of withheld work):** delta encoding, downsampling, checksums, and the file write happen on a background task that is allowed to withhold at most 40 ms of work from the presentation path per frame, stretched across as many frames as it needs. The withholding budget is the entire trick: the encode of a full 20-second window is ~180 ms of total work, delivered across frames that never feel it.

The 90 ms → 40 ms change from v1 was not a faster encoder; it was moving the checksum pass into the withheld budget's stretch and letting the nightly sweep verify any checksums the encoder had not reached when the player kept playing. The correctness argument (a torn file is detected at load either way) is in the format spec.

### Auto-triggers

Two triggers save without a press, per the v2 plan: death (any state transition into the defeat state) and a "signature jump" (velocity delta above 520 u/s inside 200 ms). Both write a capture identical to a manual one except for a cause marker and a "prunes first" retention class. Auto-saves are unstarred by definition — a human always decides what is worth keeping, which is the same principle that keeps auto-saves from auto-exporting.

The triggers are evaluated by gameplay code and emit an event; the capture module listens and calls the same save path. There is deliberately no special-cased fast path: the thing that makes manual saves cheap makes triggered saves free.

## Determinism hazards

Playback re-simulates recorded inputs through the live simulation. That is only possible because the simulation is deterministic given (starting state, input timeline, time). Keeping it so is an ongoing discipline, and this section is the checklist that discipline hangs on.

### Fixed-step simulation

The simulation is a fixed 60 Hz step, semi-implicit Euler, forces accumulated before integration (specs/momentum-model.md). No gameplay system reads render-frame time; anything that did would make playback diverge the moment the recording machine's frame pacing differed from the playback machine's. The discipline is enforced by review and by the replay harness, which plays a capture on two machines and asserts bit-identical positions at every snapshot boundary.

### RNG and iteration order

Every gameplay RNG draw comes from a seeded stream whose position is part of the player channel's state; a capture seeds playback from the recorded position. There are exactly two streams (world ambience and gameplay), because a single stream made ambience hangs sensitive to gameplay changes — a 2016-vintage lesson Tomás refuses to relearn. Entity iteration is by stable id, never by container order; the container-order version passed every test on every machine we owned and diverged on the one machine we didn't. Stable ids cost nothing and are checked by the harness.

### Effects are rebuilt, not replayed

The effects channel carries markers, and playback reconstructs the sparklines, vent haze, and pad flashes from the simulated state — the same code path live play uses. This is why effects data is not stored (the format would triple in size for no fidelity gain) and also why the particle shader must be deterministic given (state, inputs, time), which is written into reference/particle-shader-notes.md as a shader-side requirement with its own failure history. During a seek, the effects are rebuilt from the nearest snapshot's markers; a seek lands within one emitter lifetime of visual correctness, which for a 90 Hz emitter is under 200 ms of catch-up the player never notices because seeks end on a paused frame.

### What playback does with the world

Playback runs in a sandbox: the world is reset to the capture's starting snapshot, then driven by the echo. Live gameplay state is untouched — a player can watch a capture from the defeat screen while their checkpoint (a trusted node, per plans/checkpoint-policy-v2.md) waits for them untouched. The one deliberate exception is Marrow Flats' ghost lines, which consume the echo *while the player races*, running the recorded inputs through a shadow simulation advanced in lockstep with the player's. The shadow sim is the same code with a different state root; it costs 0.6 ms per frame on the reference box, measured, and it is in the renderer's budget as part of the flats' scene cost.

## Storage and lifecycle

Saved captures are single files per the format spec, written to the profile folder. The retention sweep runs at the nightly build cut: newest-40 by modification time, exempting starred, floor of 25 survivors, byte cap at 200 MB applying to unstarred captures first and starred only if the profile would otherwise exceed 400 MB total (a floor that has never bound in practice; it exists so a corrupted pruning loop cannot eat someone's starred history). The sweep never touches a live session because it never runs when a session is live — the build cut and play sessions are separated by the same scheduling that makes the nightly the safe hour for everything else in this project.

## The editor

The v2 editor slice is deliberately small: scrub bar, trim handles with 0.5 s snapping, 0.25× slow-mo, and silent webm export at the source frame rate. All four operate on the same principle: **the editor never re-simulates unless the trim changed the input timeline.** Scrubbing and slow-mo drive playback over the existing capture; trimming produces a derived capture whose echo is the trimmed range and whose start snapshot is the nearest recorded snapshot — no encode of any kind happens for a trim, which is why it is instant. Export is the only operation that renders, and it renders by playing the capture in the sandbox at export speed and writing frames out; a 20-second export takes 20 seconds plus overhead, and we have decided, twice, to be honest about that rather than add a second fast-path renderer.

Trim snapping is slightly wrong on captures shorter than 3 seconds (clamps to 1 s instead of 0.5 s); filed, low priority, slated for toolpack 3.5.1 per the handoff doc.

## Performance interactions

The ring's steady-state cost is **0.35 ms per delivered frame** on the reference box: the three channels serialize in under 0.2 ms (they are small and the serializers are table-driven), and the echo append is allocation-free. The cost is paid from the renderer's slack, on the render thread's schedule, and it is a line in specs/rendering-pipeline.md's budget table like any other stage. The save path adds nothing steady-state; phase 1 copies inside its own 4 ms and phase 2 stretches its 180 ms across frames under the 40 ms withholding cap. The star freeze incident (0.16.0 shipped a 90 ms pause that testers read as a crash; 0.16.1 cut it to 40 ms by deferring checksums) is the cautionary tale that keeps the withholding budget honest: the budget is measured against the presentation path, not against "the average frame", because the pause a player feels is a *worst* frame, and averages are how it shipped wrong in the first place.

Interaction with the prewarm system (specs/cold-start.md): capture files are written, not read, during play, so the admission path never contends with the ring. The one historical exception — the editor loading a capture on a cold machine admitted pages mid-route — is why the editor's read path uses the low-admission-priority flag, and why that flag exists at all.

---

## Ring buffer sizing

The numbers in this section are the load-bearing ones; the rest of the document explains them. The ring is three fixed allocations, sized for the 20-second window at full tick rate:

| Channel | Per tick | Ticks retained (20 s × 60 Hz) | Ring size |
|---|---|---|---|
| Player | 96 B | 1,200 | 115 KB |
| World deltas | 460 B avg (worst traced: 900 B) | 1,200 | 552 KB avg / 1.05 MB worst |
| Effects markers | 60 B avg | 1,200 | 72 KB avg |
| Input echo | 12 B per sample, ~4 samples/tick avg | ~4,800 samples | 58 KB |

Steady-state total: **~800 KB average, 1.3 MB worst traced**, comfortably inside the 2 MB budgeted at the v2 decision. The 20-second window's *copy* (save phase 1) is therefore ~4.3 MB of staging per save, which is why phase 1 is a straight memcpy and why the staging buffer is a single fixed allocation made at boot — an allocation at save time would put a malloc on the input path, and the input path does not malloc, ever, as a rule older than this feature.

The saved file is smaller than the window copy because save-time downsampling halves the snapshot ticks and delta encoding compresses the world-delta channel by a measured **62%** on kiln captures (the vents are extremely repetitive); the median 20-second file lands at **1.9 MB**. At that size, the 200 MB byte cap is roughly 100 unstarred captures — the newest-40 count binds first in every profile we have inspected, and both rules coexist because the count is what the sweep enforces and the cap is what protects a hoarder's drive.

The numbers were validated against the February playtest corpus (214 captures, including the three torn tails) and re-validated against the June playtests after the 20-second window shipped. If the window length ever changes again, this section is the arithmetic to redo first — every derivative number (file size, copy cost, encode stretch, cap ratios) hangs off the window length, and the 40 ms withholding budget was tuned against *these* sizes specifically.

---

## Failure modes and guards

- **Torn tails** — a hard exit (crash, power loss) leaves the ring mid-flush. Detection is per-chunk checksums at load; the loader drops the incomplete chunk and reports the format's truncation code, and the editor shows the capture minus its last intact second. Rate: 1.4% in the February corpus, zero data-loss complaints. The guard exists because of the 0.11.0 build, where a torn file failed to load *at all* and took its 11 perfectly good seconds with it.
- **Ring overrun** — the ring is fixed-size and circular; overruns are impossible by construction, which is the point of fixed-size. The historical failure was the *staging* buffer overflowing on a save during a vent storm (worst-case world deltas); the staging buffer is now sized from the worst traced tick, not the average, and the difference is 500 KB of RAM we consider cheap insurance.
- **Desync in playback** — the resync rule (compare against the nearest snapshot every 120 ticks, correct if drifted) has fired once in shipped builds, from a float-summation ordering difference between compiler versions on two machines. The harness now builds playback with the same compiler settings as the game; the resync rule stays as the safety net underneath the discipline rather than a substitute for it.
- **The editor opening a capture from a newer format** — version digit check, clean rejection with the format code, no partial reads. A partial read of an unknown format is how tools corrupt profiles; the cutter learned this in June with a 0.15-format file and had to be taught the check the hard way.

## Rollout and open questions

Shipped: v1 ring and manual save (0.11.0), auto-triggers and 20 s window (0.14.0 line), editor slice and export (0.15.0). The attract-mode cutter consumes starred captures nightly (Rosa). Ghost lines consume echoes on Marrow Flats (full game).

Open, with owners:

1. **Slow-motion-accurate export** (every tick, not every other) — the ring already records full rate; only the saved file downsamples. Owner: Tomás, blocked on a real request rather than a hypothetical one.
2. **Ghost races on the kiln** — needs a vertical ghost-line renderer and a policy for races in cling sections. Owner: Dev, after the festival.
3. **The 25-capture floor vs. tiny drives** — the floor protects history; a profile on a full 8 GB drive with a 400 MB starred profile is a corner nobody has hit. Owner: Rosa, revisit if the festival telemetry (opt-in) ever shows it.
4. **Whether auto-saves should ever auto-star** — the February data says deaths are the content; auto-starring deaths would tilt the loop further toward the blooper reel. Deliberately unanswered; we star by hand and watch the numbers.
