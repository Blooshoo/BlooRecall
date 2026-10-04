# The driftline rendering pipeline

Author: Marisol Vega. Date: 2026-06-18. Status: current as of 0.15.0, with the June budget pass folded in. This is the document the war room asked for: the whole renderer in one place, with the measured numbers and the failure modes that shaped it. It is long on purpose. New hires start here; wiki pages rot, this file has an owner.

---

## Purpose and scope

This document describes everything that happens between "the simulation has produced a tick" and "the frame is on screen" in driftline, on Ridgeline 0.10.x. It covers the atlas system, sprite batching, the particle pass, the fake-lighting model, the post stack, the frame budget, and how all of it scales across the three hardware tiers we ship to. It does not cover gameplay simulation (specs/momentum-model.md owns that), the capture feature (specs/quick-capture-architecture.md), or level-content concerns (levels/ owns those).

Two things make this renderer unusual, and both come from the pillars agreed at kickoff: the game must never stop the player (so the pipeline is built to *degrade visibly but continuously* rather than stall), and speed must be readable (so the pipeline spends its budget on motion clarity — trails, glows, distortion — before it spends anything on static beauty). When you are unsure why a stage exists, the answer is almost always one of those two.

A third influence is the team size. Four developers means the renderer must be boring to operate: few knobs, loud failures, and a budget document (this one) that tells you what everything costs. Every stage below ends in a number, and the numbers were all measured on the reference box with the rig described in the tooling section. If you change the renderer, you re-measure and you update this file in the same change. That rule has kept this document trustworthy for three internal releases.

---

## Hardware tiers and constraints

driftline ships to three tiers, and every design decision in this document was tested against the worst of them, not the best. The tiers are deliberately named after their role rather than any product, because the machines will be replaced and the roles will not.

### The reference box

The reference box is the lab's 4-core x86 mini-PC with an integrated GPU and 16 GB of shared memory. It is the gate machine: every performance gate in plans/demo-build-plan.md closes on this box or not at all. Its integrated GPU shares a memory pool with the CPU, which matters enormously for us — an atlas upload is not a transfer, it is a cache-coherency event, and that fact shaped the admission rules in the atlas section. The box lives on shelf 2 of the lab and is not to be borrowed for demos; it has a tag, and the tag has Priya's name on it.

Measured baseline on the reference box, current build: a quiet scene (quarry, no emitters, one sparkline idle) delivers in 9.8 ms p95. The heaviest sanctioned scene (kiln descent, vent storms, two full sparklines) delivers in 16.2 ms p95 against the 16.6 ms gate. The margin is 0.4 ms and nobody is allowed to spend it without a war-room decision — this is written here and in the ship checklist because "there's a little left" is how margins die.

### The laptop tier

The laptop tier is the oldest machine that can still finish the route: 2 cores, 8 GB, and an integrated GPU one generation behind the reference box. It gets no gates — it gets an *existence check*: the route must be completable, and nothing may visually break. The tier drops detail aggressively and deliberately (see the scaling section), but it drops along preset seams so that what remains is coherent. A game that looks broken on the low tier reads as unfinished; a game that looks *simpler* reads as styled. All our tier seams were chosen to keep the laptop tier in the second category.

### The show-floor box

The show-floor box is a hardened mini-PC in a padded flight case, imaged per candidate, and it is functionally a reference box with better cooling. It exists because venues are warm, loud, and dusty, and because a machine that throttles mid-demo is the single most expensive kind of failure we can buy. It gets its build a full week before travel and the case closes. There are no other tiers, and there is a standing rule that no fourth tier gets invented for a single partner machine; the last project that did that maintained a secret fifth renderer path for two years and nobody wants that story repeated.

---

## The frame at a glance

The pipeline is a fixed sequence of stages. The order has been stable since 0.13 and changing it requires re-running the latency rig (specs/input-latency.md), the p95 gate, and this document.

### Stage order

One delivered frame, in order:

1. **Tick consume** — the simulation's latest fixed tick (60 Hz) becomes the frame's input state. The frame is *always* built from a complete tick; there is no partial-tick path.
2. **Pose solve** — Ember's and the ghosts' animation poses are solved from the tick state. This is CPU work over the pose sets in the sprite cache.
3. **Atlas service window** — a bounded window (see the admission rules) in which page-ins, the defrag sweep, and prewarm admissions may run. Everything here is budgeted; the window closes whether or not the work is done.
4. **Batch build** — the world is walked front-to-back and quads are pushed into per-layer batch buffers.
5. **Particle simulation** — emitters and cells advance one frame's worth. Ribbons (including the sparkline) rebuild their segment chains here.
6. **Particle draw** — cells and ribbons are drawn, additive-heavy, after the world batches.
7. **Light pass** — gradient volumes and occluder blobs are composited into the light buffer. No shadow computation of any kind exists in this engine.
8. **Post stack** — distortion, glow, grade, letterbox, vignette, in a fixed order.
9. **UI batch** — the UI is drawn last, unbudgeted but practically tiny (under 60 quads on the busiest screen).
10. **Present** — submission to the presentation queue, which is allowed up to `max_inflight_frames` (3) delivered frames of runway.

### Threading shape

Two threads matter: the sim thread and the render thread. The render thread owns stages 2 through 10; the sim thread owns ticks and never renders. They communicate through the tick handoff (stage 1) and nowhere else. There is deliberately no job system: with 2 to 4 cores across the tiers, a third thread would cost more in scheduling and contention than it recovered, and every attempt to prove otherwise during the 0.12 spike produced worse p95 tails, not better. The atlas service runs *on* the render thread inside its bounded window — moving it to its own thread was tried in February and the synchronization cost exactly the stalls it was meant to remove.

---

## The atlas system

Everything drawn by stages 4 through 8 comes from a small set of texture atlas pages. The atlas system is the renderer's most load-bearing subsystem and the source of most of our historical failures, so it gets the longest section.

### Page geometry

Pages are **2048×2048**, with **16 px gutters** between sprites. The gutter is not optional: the glow pass samples outside sprite bounds, and without gutters every lit sprite bleeds its neighbors into the halo. Sprites are packed by a shelf packer per page, largest-first within a shelf. We tried a guillotine packer early on; it fragmented 12% worse on real content and was replaced within a month. Maximum resident pages is **24** on every tier — the tier differences are handled by *tier* (see below), not by page count, because page-count differences would change what needs pinning per tier and that complexity bought nothing.

The pose art for Ember and the ghost lines lives in dedicated pages managed by the fox sprite cache (specs/fox-sprite-cache.md); that cache sets policy (budget, pinning, oldest-first eviction) and the system in this section provides the mechanism. Keep the two docs' roles straight: this section says *how* pages move, that one says *which* pages may move.

### Tiers and format decisions

Each page exists in up to three tiers: full (2048²), half, and quarter. Tier selection happens at admission time from the sprite's screen-size history — a sprite that has never been drawn larger than 200 px never needs its full tier admitted. This is why the memory ceiling policy in plans/perf-push.md can "drop the smallest atlas tier first" as a pressure response: the quarter tier is by construction the least-missed.

Formats: full and half tiers are 32-bit RGBA; the quarter tier is 16-bit with a 1-bit stencil channel we do not use and have stopped pretending we might. Compression was evaluated twice (a block scheme in October, a palette scheme in January) and rejected both times: decode cost at page-in was the entire stall we were trying to remove, and the memory savings were smaller than the pin list's waste. The lesson, written down: *on shared-memory hardware, compressed textures trade a cache-coherency event for a decompression stall, and that is a bad trade at page-in rates of two per frame.*

### Admission and eviction as a contract

The service admits at most **2 pages per delivered frame**, enforced *at the service*, not the caller — this closed the loop the May war room found, where well-meaning callers batched their own admissions and lied about the cap. Admission order within a frame: prewarm list first, then demand paged in oldest-request-first. A demand that arrives mid-route for a page that is not on the route's prewarm list prints a warning; the goal is zero warnings on the demo route, and the current count is zero for eleven consecutive nightlies.

Eviction is oldest-first under pressure, skipping pinned pages, exactly as the fox sprite cache specifies for its pages and as the world atlas mirrors for its own. The pressure trigger is `atlas_pressure_ceiling` (0.85 of budget) from reference/config-keys.md. What the contract *forbids* is worth stating plainly: no mid-frame eviction, ever. Eviction happens in the service window or not at all; a draw that hits an evicted page raises `ERR_RIDGE_037`, skips the draw, and is by definition a contract violation to investigate, not a condition to tolerate.

### Fragmentation and the defrag sweep

Shelf packing fragments when sprites retire and their spaces are smaller than any waiting sprite. The service tracks waste per page; when a page's waste crosses **20%**, the page joins the defrag queue. The defrag sweep runs inside service windows, one page per window maximum, moving live sprites into a scratch page and swapping. A full sweep of a worst-case page costs 3.1 ms, which is why it is capped at one page per window and why the sweep pauses entirely during the route's first 40 frames (the pose system's busiest period). The scratch page is resident always; it is the only page allocation that is never evicted, and it is 8 MB of the budget we consider well spent.

---

## Sprite batching

Stage 4 exists because the integrated GPUs we ship to want few, large draw submissions. The batching rules are few and strict.

### Sort keys and bands

Every quad carries a two-tier sort key: **layer band** (0–7 world, 8–9 effects, 10 UI) and a within-band key. The bands are load-bearing for the post stack: the glow pass reads bands 0–7 and the distortion pass reads band 8, so a quad in the wrong band is not a sorting bug, it is a *visual* bug. Within a band, the key packs texture page first, then material, then depth — texture-first sorting is what keeps batch breaks rare, and it survives because artists stopped asking for arbitrary per-sprite material ordering after seeing the batch statistics.

The third key tier that existed before May (a per-sprite stable index) sorted nothing on any recorded route and was removed in the perf push. Its removal is documented here because someone will eventually re-add "just one more key tier" for a legitimate-seeming reason; the record shows the third tier cost 0.9 ms of tail for zero observable benefit.

### Buffer shapes and the 8k cap

Batch buffers hold up to **8,192 quads** each, pre-allocated, one per layer band. Overflow raises `ERR_RIDGE_112` and splits the batch automatically; the split is logged and *frequent fires mean a layer needs re-banding*, not a bigger buffer — a bigger buffer just moves the cliff. On the reference box, a full 8k batch draws in 0.7 ms, so a route that needs two batches in band 0 has already spent more than the whole budget on one band; this has happened once (the flats' eastern rim, pre-tuning) and the fix was content-side.

---

## The particle pass

Particles are where the renderer spends its discretionary budget, by pillar: motion clarity is worth more here than anywhere else.

### Emitters and cells

An emitter is a policy object (rate, lifetime, velocity field, palette); a cell is one live particle. The pool is fixed at **8,192 cells** on every tier. Emitters are unbounded in count but bounded in *cost* by the retirement policy below. The vent columns in the kiln are the pathological case: each vent is an emitter with a 120-cell steady state and a storm state at 400 cells, and a screen with six storming vents is 2,400 cells, which is 29% of the pool and 1.6 ms of simulation on the reference box. The numbers are why vent placement is a level-design conversation and not just an art one (Dev has the emitter budget printed above his desk, his claim, and we let him keep it).

### Ribbons

Ribbons — the sparkline trails chief among them — are built per frame from emission points, 180 segments at full detail, geometry described in specs/sparkline-trails.md and shader details in reference/particle-shader-notes.md. The renderer's only jobs are to rebuild the chain within the particle simulate stage and to never let a ribbon degrade mid-draw: the retirement policy protects the newest two emitters *always*, and a ribbon counts as newest while any of it is on screen. A sparkline that collapses mid-jump reads as a bug to players who have never heard the word "emitter", and the first time it shipped that way (0.12.0, for four days) we got three reports in one playtest night.

### Retirement under pressure

When pool allocation fails, the newest two emitters are protected and the oldest shed detail first: rate halves, then lifetime halves, then the emitter is refused new cells (raising the guard, `ERR_SPK_OVERFLOW_118`, in the sparkline's case). The order was chosen so that the *visual signature* of pressure is "the world gets calmer" rather than "the player's own effects break down". Player-owned effects are the last thing pressure is allowed to touch, and the only thing allowed to touch them is the pool hard-cap, which by construction only fires in the attract stress scene.

---

## Lighting without shadows

There are no real-time shadows in driftline and there never will be on this engine generation. The look is built from two cheap ingredients composited into a light buffer.

### Gradient volumes

A gradient volume is a screen-space or world-space box with a directional color ramp. Every outdoor scene has a sun band (a huge screen-space volume) plus at most a few local volumes; the flats cap at two per screen by design (plans/tileset-refresh.md) and the kiln historically used five. The per-scene cap is **six volumes**; the compositor batches all six in one pass over the light buffer at a measured 0.9 ms on the reference box at full resolution. Volumes do not overlap arbitrarily — overlapping volumes composite in placement order, which is a documented limitation and occasionally a *feature*, since it gives the level designer deterministic control over who wins.

### Occluder blobs

Occluder blobs are soft ellipses that darken the light buffer behind foreground props — the cheap illusion that the kiln's tile columns cast shadow. They are drawn as unlit dark geometry into the buffer at 0.4 ms per screen for a typical load of 20 blobs. The blobs are *the* reason the kiln reads as deep: testers consistently described the shaft as "shadowy" in reviews of a scene that contains, mathematically, no shadows. Nobody tell them.

---

## The post stack

Stage 8 is a fixed chain; the order was settled in February after one bad week of experimenting and it is written here so it stays settled.

### Order and why

1. **Distortion** (band-8 input): heat haze in the kiln, the speed ripple past 560 u/s. Runs first because it reads depth, and everything after it should respect the warp.
2. **Glow**: a two-pass blur over the bright pass of bands 0–9, at quarter resolution. The glow pass is why gutters exist (see atlas).
3. **Grade**: the color LUT, currently the warm festival grade by default with the cool grade behind a debug toggle (ship checklist decision, 2026-08).
4. **Letterbox**: the 2.35:1 bars during signature descents, animated in and out over 400 ms. Bars are drawn, not resolved, so the grade never touches them.
5. **Vignette**: last, always, because the vignette is the frame's voice saying "this much, no more".

The stack costs 2.3 ms p95 on the reference box in total. The tempting cuts (glow to eighth-resolution, vignette off) were both tested and both rejected: glow at eighth-resolution halos, and the vignette-off build tested as "somehow tiring" in the only A/B word the testers could produce. The stack stays whole.

### The grades

Grades are 32×32×32 LUTs, baked at build time from a neutral reference scene. There are exactly three: warm (festival default), cool (debug), and frost (a world we have not shipped yet). The bake is deterministic and checked into the toolpack so a re-bake is diffable. The one rule: *no runtime grade blending*. Cross-fading LUTs costs a second sampler in every post pass and was measured at 0.4 ms for a transition players described as "the same but worse".

---

## Budgets

Everything above exists to make this section small and trustworthy. The budget is measured, not allocated; it is re-measured after every renderer change on the reference box over the heaviest sanctioned scene (kiln descent, vents storming, two full sparklines).

#### Frame budget, measured

The load-bearing numbers, p95 on the reference box, current build, heaviest sanctioned scene. Total **16.2 ms against the 16.6 ms gate**:

| Stage | p95 (ms) |
|---|---|
| Sim consume + handoff | 0.4 |
| Pose solve | 0.8 |
| Atlas service window | 0.4 |
| Batch build | 1.2 |
| Particle simulate | 1.9 |
| Particle draw | 1.4 |
| Light pass | 1.6 |
| Post stack | 2.3 |
| UI batch | 0.7 |
| Present + queue overhead | 0.9 |
| Simulation tick (amortized share) | 3.1 |
| **Slack to the gate** | **1.5** (0.4 of which is committed reserve, see below) |

Read the slack carefully: 1.5 ms of headroom sounds comfortable and is not. **0.4 ms is committed reserve** — reserved for the capture feature's save path (the star freeze must stay hidden behind the hold animation, per specs/quick-capture-architecture.md), and touching it is a cross-feature decision, not a renderer one. That leaves 1.1 ms of true slack, which is the answer to "can we add X": only if X costs less than 1.1 ms p95 on the box *and* a war-room sign-off exists.

#### What breaks the budget

Recorded, named, and ranked, so the next tail incident starts from history instead of archaeology:

1. **Vent storms with retirement disabled** (the pre-May build): +2.1 ms of tail. Fixed by the retirement policy; un-fixable by hardware tier — the laptop tier drops vent *count*, never vent cost, so this class of regression cannot hide on a fast machine.
2. **Atlas service over-admission**: +1.4 ms when callers bypassed the cap. Fixed by service-side enforcement. The failure mode to watch for is a *new caller* that means well.
3. **Third sort-key tier**: +0.9 ms for nothing. Removed. The general lesson is written in the batching section.
4. **Mid-frame defrag**: +3.1 ms, once, in February, when the one-page-per-window cap was accidentally unbuilt in a merge. The cap is now asserted, not assumed.

#### Guardrails for future work

- No stage may exceed its budget line for three consecutive nightlies without a war-room item. Three nights is enough to distinguish noise from trend on this rig.
- New pipeline stages require a new `ridge_frame_stats_t` field in the same change (reference/engine-api-notes.md); an unmeasured stage is an unbounded stage.
- Anything that costs "nothing on the reference box" must still be measured on the laptop tier, where "nothing" historically means "0.3 ms you did not have".

---

## Scaling across tiers

Scaling is by preset seams, decided once, per stage. This section is short because the design intent is that it can be: if scaling requires judgment calls at runtime, the tiers have already failed.

### What the laptop tier drops

In order of when pressure appears: quarter-tier pages are not admitted (half-tier serves), glow drops to a single pass at half resolution, vent emitters cap at half count, occluder blobs cap at 12 per screen, and the distortion pass narrows to the screen center. The last one is the only seam that changes a *feel*: the speed ripple past 560 u/s reads at the edges on the reference box and at the center on the laptop tier. It was tested with six testers on the laptop tier and all six described the speed as "fast" with no qualifier about the ripple; the seam kept its job.

### What nothing drops

Three things are tier-invariant by pillar: the sparkline's existence (it may shorten via its own LOD, never vanish below the charge gate), the input latency path (specs/input-latency.md's numbers are contract), and the post stack's *order* (a tier may skip a pass it cannot afford, never reorder). The invariant list is short on purpose: every exception added to it is an exception someone will eventually test against, and the pyramid of "it holds everywhere except" is how a renderer becomes unmaintainable.

---

## Tooling and overlays

The renderer is operable because the tools to see it are one keypress away, and because what they show is trustworthy.

### The frame graph

F8 opens the frame graph (see reference/debug-overlay-keys.md): stage bars from `ridge_frame_stats_t`, the atlas service's page-in queue, pool occupancy for particles, and the last 120 frames of p95 history. Every bar is fed from the same struct the budget table above was measured from, so the overlay cannot disagree with the document unless someone broke the discipline — and if someone broke the discipline, that is the bug to fix first.

### Capture discipline

Performance investigation captures (the overlay's recording, not the game's Quick Capture feature — different thing entirely) run at most 20 seconds and always on the reference box, always at the heaviest sanctioned scene. The war-room decomposition that produced the May action list came from exactly four such captures; the discipline that mattered was that all four were taken with identical scene state, which the overlay's scene-freeze key enforces. Unfreezed captures compare nothing.

### The rig, and why the numbers are believable

Every number in this document was produced the same way: the fixed route, the heaviest sanctioned scene state, 30 seconds of play after a 60-second warmup (so cold-path admissions never contaminate a measurement), p95 over the delivered frames, on the reference box, with the machine unplugged from the network and the overlay off except when it is the subject. The warmup rule was added in April after we noticed that the first run of any session carried prewarm admissions and read 1.8 ms heavier than every run after it — an entire war room nearly got scheduled over what was, in the end, the renderer doing its job. The rig is a script in the toolpack; it is not a suggestion. If a number in this file disagrees with the rig, run the rig three times, and if it still disagrees, the file is wrong and gets fixed the same day — an outdated number in a trusted document is worse than no number, because it wears the costume of authority.

---

## Known failure modes

The renderer's history in four incidents, kept here because each one encodes a rule that is easy to delete if nobody remembers the body it came from.

### The beaded ribbon incident

The first ribbon shader drew independent quads and additive blending exposed one-pixel gaps at every joint; at speed, the sparkline looked like a string of pearls. Fixed with the 1 px overlap at 50% alpha (reference/particle-shader-notes.md). The rule it left behind: *additive-blended adjacent geometry must overlap deliberately*, because the blend sums whatever the rasterizer leaves between primitives, and what it leaves is seams.

### The seam at the world border

Twice in 0.9.0 the NaN guard (`ERR_MOM_NAN_401`) fired at the world border seam where a vent and a pad applied impulses in the same tick. It was a simulation bug that *presented* as a rendering bug — Ember snapped to the last good node, which players read as "the camera broke". The rule: when a player-visible glitch could have two causes, fix the reporting first, or you will tune the wrong subsystem for a week, which is exactly what happened.

### The March atlas miss

One shipped build raised `ERR_RIDGE_037` during a world transition because a hand-edited pin list referenced a page key that did not exist, and the eviction loop, finding its skip target missing, skipped nothing. The validator that now checks pin lists at load exists because of that night. The rule: every hand-edited input to the renderer gets validated at load with a loud, specific error. Loud and specific is cheap; silent and weird is the most expensive thing this team ships.

### The grade that could not blend

The runtime grade-blending experiment (see the post stack section) is listed as a failure mode because the *reason* it failed is reusable: a per-pass cost that is individually defensible ("0.4 ms for a nicer transition") but that composes against a budget with 1.1 ms of true slack. Any feature whose cost is described in "only" is a budget conversation before it is a rendering one.

---

## Open questions

Carried forward, with owners, so they do not fossilize:

1. **Half-tier glow on the reference box.** If the reference box ever needs the laptop tier's single-pass glow, the halo artifacts need a real answer, not the dither hack. Owner: Marisol. Trigger: any budget regression past 0.6 ms of the current slack.
2. **Light buffer at half resolution.** Compositing the six volumes at half resolution and upsampling measured 0.5 ms cheaper with a visible softening that testers *liked* in the kiln and *hated* in the flats. It is a per-world toggle today; whether it becomes a per-scene art parameter or dies entirely is an art-direction call deferred until Marrow Flats' refresh lands (plans/tileset-refresh.md). Owner: Dev, with Marisol measuring.
3. **The committed reserve.** Whether the capture save's 0.4 ms reserve should formalize into the budget table as its own line after the festival. Owner: Priya, after the demo, deliberately not before.

---

## Appendix: where things live

- Gameplay movement rules: specs/momentum-model.md (this document never modifies them, only presents their consequences).
- Capture ring and save path: specs/quick-capture-architecture.md; format: specs/replay-format.md.
- Sprite cache policy: specs/fox-sprite-cache.md.
- Trail and emitter feature rules: specs/sparkline-trails.md; shader details: reference/particle-shader-notes.md.
- Config keys quoted here: reference/config-keys.md; error codes: reference/error-codes.md.
- The gate this document is measured against: plans/demo-build-plan.md, and the war-room history: meetings/2026-05-18-perf-war-room.md.

If you read only one section before touching the renderer, read the budget. If you touch the renderer without reading the budget, the budget will read you.
