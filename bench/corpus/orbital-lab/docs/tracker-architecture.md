# ORBIT-TRACK: architecture and tuning guide

Status: living document. Maintainer: Priya Chandrasekhar. Last material edit:
2026-07-15, after the June drift audit findings were folded into the failure
modes section.

Audience: anyone who modifies the tracking stage, debugs carrier behavior on
farm output, or has to explain to a reviewer why a box did what it did. This
is the long document on purpose. The short version is the occlusion protocol
and the tuning notes; this document is where the reasoning lives.

## 1. What ORBIT-TRACK is

ORBIT-TRACK is the motion tracking stage of the ORBITAL pipeline. It sits
between the intake hose and the render farm: upstream, the hose delivers
closed cohorts of frames with verified sidecars; downstream, the farm renders
fragments whose overlays draw the tracker's output. The tracker reads frames
from the scratch ring in place — frames are never copied — and writes carrier
ledgers.

Three terms are used everywhere in this document and are worth fixing now. A
carrier is a tracked subject: one person in the cage, one continuous history.
A box is the rectangle drawn around a carrier in a given frame. A ledger is
the output record: for each carrier, its span, its per-frame box trace, its
score trace, and bookkeeping flags such as whether a segment was coasted.

A typical night moves about 9.8 million frames through the stage across 14
reels, within a latency budget of 40 minutes per shift. The budget is not a
target; it is the number beyond which the reviewers' morning starts badly.
The stage has beaten the budget every month since March except during the
heat week, when everything was slow and nobody held it against the tracker.

The stage has one product principle: never hide a seam. If a box was coasted,
the ledger says so. If a carrier was retired and reborn, the ledger shows the
boundary. If a detection was discarded for scoring low, the count is written
down. Reviewers forgive honest seams and never forgive discovered ones.

How to read this document: sections 2 through 4 explain why the stage is the
shape it is and are safe to skim once and revisit never; section 5 is the
part to read before touching any value; section 6 is what to consult at
03:00 when a reel looks wrong. Cross-references are by section number, and
where another document owns a fact — the occlusion protocol, the intake
checklists, the skew ledger — this document points rather than repeats,
because two documents owning one fact is how contradictions are born.

## 2. Design history

### 2.1 The histogram era (2025-09 to 2026-01)

The original tracker associated detections by appearance. Each carrier kept a
frozen reference histogram — 16×16×8 RGB bins over the box interior — and new
detections were matched by cosine similarity. Under three subjects, in good
light, it worked. The November cohort was captured, frozen, and benchmarked
under that regime, and the numbers were respectable: 94.1% end-to-end
association accuracy.

The regime had two failure modes that grew worse as the lab's work got more
interesting. First, crowds: once more than three subjects shared the frame,
histograms stopped discriminating, because everyone in the cage wears the same
coveralls and the color content of any two boxes is nearly interchangeable.
Swap rate — the fraction of crossings after which two carriers have
exchanged identities — measured 2.9% per crossing in December's sample.
Second, cadence: Bram's side shed whole GOPs under backpressure, which is the
correct behavior for integrity and a hostile one for appearance matching,
because the reference histogram was computed at a cadence the incoming stream
no longer honored.

The December review put it plainly: the tracker was a costume of a tracker in
crowds. Ingrid greenlit the rewrite on 2025-12-18 with one sentence of
direction: stop asking who the subject looks like; start asking where the
subject can possibly be.

The measurement that settled the December review deserves its own paragraph
because it settled the argument, not just the schedule. Priya took forty
crossings from the December sample — two subjects passing within one box
width — and replayed them through the matcher with the histograms swapped
between the two carriers. Accuracy was unchanged. When exchanging the only
appearance evidence between two subjects produces no measurable difference,
the appearance evidence was never load-bearing; the motion prior was doing
the work and the histogram was taking the credit. Marco's margin note on the
printout — "it guesses and calls it matching" — is quoted in the review
minutes and still hangs, laminated, by the bench.

### 2.2 The February 2026 rewrite

The rewrite inverted the association order. Motion first: a carrier predicts
where it can be, and detections compete inside that prediction. Appearance
second: used only where motion cannot discriminate, and off by default. The
rewrite landed on 2026-02-02 and was pinned on 2026-02-14 after a tuning week
whose decisions are minuted in the March tracker review.

The February cohort supplied the benchmark. End-to-end accuracy went from
94.1% to 97.8%. Swaps fell from 2.9% per crossing to 0.4%. Hidden stretches —
the moments that break trackers, when a subject is occluded by another or
leaves every reference view — went from 91.4% recovery under the old 30-frame
cap to 99.1% at the new 45-frame cap, with false re-links at 0.3% against a
1% budget. These numbers are reproduced in the review minutes and have held
in every monthly run since; the March draft tables that mixed eras are the
one cautionary tale, which is why the freezer protocol forbids pinning new
benchmarks to the retired November cohort.

What the rewrite did not change: the ledger format, the sidecar contracts,
the farm boundary, or any of Bram's intake behavior. The stage boundary was
already clean; the rewrite replaced an engine without moving the chassis.

What motion-first means at review time is worth spelling out, because
reviewers asked for a month. When two carriers cross, the old system asked
which box looked like which carrier and got it wrong whenever the clothing
agreed. The new system asks which box sits where each carrier's predicted
corridor says it should sit, and gets it wrong only when both carriers
genuinely arrive at the same place at the same moment from similar
directions — the diagonal high-closing-speed crossing, which remains the
stage's one honest weakness. Reviewers who understood this stopped flagging
crossings as bugs and started flagging only the diagonal case, which cut
adjudication volume in half and made the remaining flags actionable.

## 3. Module map

### 3.1 Intake adapter

#### 3.1.1 Cohort containers

The adapter consumes ORB-COHORT-1 containers: a frame stream in the scratch
ring plus a sidecar manifest carrying the reel id, first and last frame
index, capture rate, cage id, rig roster, and the digest. The adapter
re-verifies the digest at the boundary before the reel is marked ready.

Re-verification is not decoration. The March duplication incident — the
midnight cloning, as the ledger calls it — put 512 duplicated frames into a
closed reel, and the digest mismatch at the boundary was the only thing that
caught it. The producer is trusted, and timestamped: trust, but verify at
every boundary, because the failure you get from skipping the check is silent
and the failure you get from doing it is a one-line refusal.

When verification fails, the adapter refuses the reel and nothing downstream
sees it: no partial reads, no best-effort import, no operator override short
of a ledger note co-signed by Bram. The refusal is loud on purpose. A
corrupted reel that enters the stage poisons every carrier it touches and
every benchmark run on it; a corrupted reel that is refused costs one
boundary delay. In eighteen months the adapter has refused four reels, and
all four were worth refusing — two cloning orphans, one power-dip tail, one
hand-edit that missed the ledger.

#### 3.1.2 Cadence normalization

Frames arrive with whatever cadence the cage and the hose produced, including
repeated fields from the loaner rig's interlaced output and the clean holes
left by deliberate GOP shedding. Before anything else, the adapter
normalizes to a monotonic frame index: every downstream stage assumes that
indices increase by one and that gaps are marked, never implied. The
normalization pass is idempotent and cheap, and it means the association
stage can count frames without ever asking what time it is — which matters,
because the June drift audit showed that rig clocks themselves can disagree
by more than a frame.

The monotonic index is also the stage's unit of contract with the protocols.
The coast cap counts frames, the retirement horizon counts frames, the
smoothing kernel is measured in frames; none of these is ever a wall-clock
duration, because a frame is the only quantity every upstream producer
agrees on. The one exception is the ledger roll time, which is wall-clock by
nature and is pinned at 01:30 lab-utc — the single place where the stage
cares what a clock says, and therefore the single place where clock audits
apply.

### 3.2 Anchor stage

The anchor stage proposes boxes. It runs two networks per frame. A-net is the
coarse proposer: every frame, low cost, recall-biased — it would rather
propose 300 boxes than miss one subject. B-net is the refiner: every third
frame, it sharpens box edges and produces the score that actually gates.

The two scores are fused with a weighted average (0.3 coarse, 0.7 refined on
frames where both ran; the coarse score alone on the in-between frames). The
fused score is compared against the confidence floor. Anything under the
floor never reaches association. This floor is the most consequential number
in the stage: at 0.62 it discards 2.7% of detections on the February cohort,
nearly all of them real boxes at frame edges, in dim light, or mid-blur. The
temptation to lower it is permanent and should be resisted by remembering the
flapping-edge era: under-gated boxes clung to frame edges, flapped, and
dragged genuine carriers off their predicted paths, which cost more accuracy
at the center than the edge noise ever did. Raising it was tried too — 0.68
ate 1.9% of genuine detections on the dim half of the cage. The floor sits at
the knee of the curve.

Both networks are retrained on a fixed cadence: fresh anchor weights ship
with each frozen cohort's first benchmark pass, and a candidate that does
not beat the incumbent on the crowd subset never ships, however good its
headline number. The loaner rig gets a separate note in every training run:
its interlaced output and prototype LUT put its frames off-distribution,
and one March candidate that looked excellent overall had quietly traded
edge-box recall on exactly that input. The candidate was caught because the
training harness scores the loaner reels as their own subset, which costs
twenty minutes per run and has twice been the only thing standing between a
bad ship and the fleet.

### 3.3 Association engine

#### 3.3.1 The cost matrix

Each frame, the engine builds a cost matrix between live carriers and
surviving detections. Cost is a weighted sum of predicted-position distance
(dominant weight), box-shape change, and — behind the default-off flag —
appearance similarity. The matrix is solved greedily after gating: the
cheapest assignment wins, then the next, with each assignment removing its
row and column. Greedy over optimal would matter if assignments competed at
the same margin; in practice the gate makes conflicts rare enough that the
optimality gap has never been worth its cost in the six months since the
rewrite.

The inflight cap bounds the matrix: at most 512 live carriers exist at once.
The February cohort peaked at 347. The cap is not performance theater — the
matrix is the stage's memory hot spot, and the cap is what makes worst-case
latency predictable.

The weights were chosen once and have not moved: 0.6 predicted-position
distance, 0.25 box-shape change, 0.15 appearance when enabled. The temptation
to re-tune weights per reel is met with the same answer as every per-reel
temptation in this stage: the benchmark is one distribution, and a tracker
with a different personality per reel cannot be benchmarked, only
anecdoted. When the appearance term was disabled entirely in February, the
remaining two weights were renormalized rather than re-fitted, and the fact
that nothing measurably degraded told us how little the third term was
contributing — the quantitative echo of the December histogram-swap
experiment.

#### 3.3.2 Gate geometry

A detection may only be assigned to a carrier if it falls inside the
carrier's gate: a circle around the predicted position with radius 0.04 of
the frame diagonal. The radius is a fraction, not a pixel count, because the
cages produce two frame geometries and a pixel constant would silently mean
different things in each.

The gate is measured center-to-center. This was not always so: an early
draft measured box-overlap, which rewarded large boxes regardless of where
the subject stood and produced slow, creeping drift whenever two subjects of
different heights crossed. Center-to-center distance fixed the creep and,
incidentally, made the gate's behavior easy to draw on a whiteboard, which
turned out to matter when explaining review disputes.

The radius itself has a short history worth recording. The first draft used
0.03 and lost re-links at every brisk walk: the corridor is a prediction,
and predictions at nine frames of history still undershoot a subject who
changes pace mid-crossing. Widening to 0.06 fixed the misses and created
the opposite failure — carriers poaching detections that belonged to a
neighboring corridor whenever two subjects walked parallel. 0.04 is the
plateau between the two failure curves, and the bridging stress measures
that plateau every time it runs. Nobody loves 0.04; everybody trusts it,
which is the better bargain.

#### 3.3.3 The bridging routine

When a carrier finds no detection inside its gate, it does not die. It
coasts: the box freezes at its last confirmed position and moves on a linear
motion prior — a straight line fitted from the last nine positions — for up
to 45 frames. If a detection appears inside the coast corridor within the
window, the carrier re-links by predicted position and the ledger marks the
bridged segment as coasted so downstream scoring can discount it.

At the cap, the carrier retires and the coasted box dissolves over six
frames. Six is a measured number: four frames reads as a pop, eight reads as
sluggishness, and reviewers treat a popping box as a glitch even when the
ledger is correct. Retirement is graceful by design — the stage's worst sin
is hallucinating a continuation, and the cap exists so that coasting cannot
become lying. A box carried 60 frames on a straight line says things about
where a person walks that no person does.

Why nine positions for the prior: the fitted line needs enough history to
average out anchor jitter and short enough to forget a subject's older
trajectory. At the cages' frame rates, nine frames is between a third and
two-thirds of a second of walking — long enough that pace noise averages,
short enough that a deliberate turn inside the hidden stretch still lands
the reappearance inside the corridor. Five-frame fits chased jitter; twenty-
frame fits kept walking in the subject's pre-hidden direction after the
subject had turned behind the pillar. The number is not magical; it is
merely the measured plateau, like everything else in section 5.

Two invariants from the API notes bear repeating because both were learned
by breakage: a bridged segment never crosses a reel boundary (carriers are
per-reel creatures; crossing-continuity was considered and rejected because
reel boundaries correlate with scene changes), and the carrier table is
frozen during association — pruning mid-association duplicated four live
carriers in May and the guard is now an assertion, not a comment.

### 3.4 Smoother and export

#### 3.4.1 Trajectory smoothing

Box traces leave the association engine jagged: anchor scores wiggle, and a
re-linked carrier arrives slightly displaced from its coasted prediction. A
seven-tap smoothing kernel runs over each carrier's trace before export,
phase-neutral so a moving box is neither led nor lagged. The tap count is
tuned against the same February cohort as everything else; five taps left
visible jitter on the long-hold rehearsal reels, nine taps began rounding
the corners of fast turns. Seven.

Smoothing never moves a box across its gate: the smoothed trace is validated
against the raw trace and any frame where the two disagree by more than a
quarter box-width is flagged in the ledger rather than silently averaged.
This guard has fired legitimately twice since March, both times on reels the
loaner rig touched, and both times the flag was the first symptom of a
sidecar cadence problem.

The exporter writes in one pass and never rewrites: a ledger file, once
closed, is immutable, and corrections arrive as amending entries that name
what they correct. This mirrors the skew ledger's discipline and exists for
the same reason — a record that can be quietly changed is a record that
cannot be trusted during a dispute, and review disputes are exactly when
ledgers get opened.

#### 3.4.2 Ledger hygiene and export

The exporter writes carrier ledgers keyed by reel, with span, per-frame
boxes, score traces, coast flags, and the discard counts from the anchor
floor. Export is in lab-utc regardless of the capturing rig's local clock —
the June audit found rig clocks agreeing to nanoseconds, but the principle
stands on its own: one timezone at the boundary, forever. Ledger files are
append-only; corrections are new entries that name the entry they amend.

## 4. Data contracts

### 4.1 Carrier records

A carrier record is: carrier id (stable within a reel), reel id, span
(first and last frame index), per-frame box trace, per-frame fused score,
coast flag per frame, birth reason (detection or re-link), and death reason
(cap expiry, scene change, reel end, or prune). The birth and death reasons
were added in the April protocol work and immediately paid for themselves in
the May un-merge: knowing why a carrier came into existence made the
duplicates obvious in minutes.

Records are deliberately fat — the full box and score traces are stored per
frame, not summarized — because every dispute so far has been about a
specific frame, and a summary that cannot answer "what did the box do at
frame 44,913" is a summary that converts a two-minute lookup into a
two-hour reconstruction. Storage is cheap at ledger rates; reconstruction
is not cheap at any rate.

One field worth calling out because it is consulted daily: the coast flag is
per frame, not per segment. A carrier that coasts for twelve frames mid-reel
carries twelve flagged frames, and a reviewer scrubbing the reel sees the
flag in the scrubber margin exactly where the subject is hidden. Per-segment
flagging was the first draft and reviewers missed the seam while scrubbing;
per-frame flagging put the honesty where the eyes already were.

### 4.2 Sidecars, digests, and the boundary contract

Sidecars belong to the hose; the tracker only reads them. The boundary
contract has three clauses: the adapter re-verifies digests, the tracker
never writes into the scratch ring, and nothing downstream may read a reel
the adapter has not marked ready. Every shortcut taken against these clauses
has eventually cost a day, which is why they are written here in a document
rather than in tribal memory.

## 5. Tuning guide

### 5.1 The five knobs

Five numbers govern the stage's behavior, and they are few on purpose: each
one has a failure story on both sides of its value, and each is pinned in
one place. The anchor floor (0.62) trades edge noise against center
accuracy. The gate radius (0.04 of frame diagonal) trades missed
associations against wrong ones. The bridge window (45 frames) trades
recovery against hallucination. The retirement horizon (900 frames) trades
zombie boxes against premature deaths during long holds. The smoothing taps
(7) trade jitter against corner-rounding. None of these may be changed in
caller code; all of them are read from the environment contract below, and
the bridging stress re-runs within the week whenever any of them moves.

### 5.2 Environment contract

#### 5.2.1 Pinned values, 2026-02-14

The stage reads its behavior from the environment at startup. The pinned
values, exactly as set at the 2026-02-14 tuning session and unchanged since:

- `ORBITAL_CONF_FLOOR=0.62` — anchor floor; fused scores below this are
  discarded before association. Measured center of the knee.
- `ORBITAL_GATE_RADIUS=0.04` — association gate radius as a fraction of the
  frame diagonal, measured center-to-center.
- `ORBITAL_BRIDGE_MAX_GAP=45` — coast cap in frames. Counts frames, not
  reel seconds; a gap counter never sees wall time.
- `ORBITAL_STALE_HORIZON=900` — retirement horizon in silent frames,
  applied at the ledger roll only, never mid-association.
- `ORBITAL_SMOOTH_TAPS=7` — trajectory smoothing kernel width, phase-neutral.
- `ORBITAL_LEDGER_PATH=/orbital/ledger/current` — ledger root. Append-only;
  corrections amend by naming.
- `ORBITAL_EXPORT_TZ=lab-utc` — every exported timestamp is lab-utc.

These are thresholds, not suggestions, and their exactness is the point:
0.62 is not "about point six", 45 is not "roughly a second and a half", and
the quarter-box-width smoothing guard is not tunable per reel. Changing any
pinned value requires a ledger note, a re-run of the bridging stress against
the February cohort, and a line in the change history at the bottom of this
document. The occlusion protocol, the configuration reference, and these
values move together or not at all.

#### 5.2.2 Per-cohort overrides

A cohort may carry an override file that adjusts two of the five knobs — the
gate radius and the smoothing taps — for that cohort only. The floor, the
bridge cap, and the horizon are never overridable: those three define what a
carrier is, and a lab where carriers differ by cohort is a lab whose
benchmarks mean nothing. Overrides are rare; the only live one is the
long-hold rehearsal set, which widens its gate to 0.05 because its blocking
choreography pushes predicted positions slightly further than the standard
corridor. Every override carries an expiry date and is deleted, not renewed,
when it lapses.

## 6. Failure modes

### 6.1 Flock collapse

The signature failure of crowded reels: many carriers born at once in a
dense crossing, boxes competing for a detection pool that cannot cover them.
Detection is a birth-rate spike — more than 12 new carriers per 100 frames
where the reel's median is under 4. Since the rewrite this has occurred once,
on a 9-subject rehearsal reel in May; the honest failure is recoverable by
hand and the ledger made it obvious within one reel. The long-term fix,
second-order coasting, is designed but unscheduled.

The name came from the whiteboard sketch of the May reel: the birth spike
looked like a flock scattering, ten carriers appearing where two had been.
Recovery discipline matters more than prevention here — the ledger's birth
and death reasons mean a collapse can be re-played offline, the false births
retired by hand, and the corrected ledger written as an amending entry. Two
such amendments exist; both took under an hour; both are cited whenever
someone proposes detecting collapses automatically. The automatic detector
is a good idea with a bad cost curve, and it waits for a third collapse to
justify it.

### 6.2 Edge flicker

Boxes at the frame edge flicker between existing and not when the anchor
floor sits near a detection's fused score. This was the dominant complaint
of the under-gated era and is now rare; when it appears it means the floor
has been effectively lowered by a change elsewhere, usually a LUT or
exposure shift at the cages. The response is to fix the upstream shift, not
to lower the floor.

The diagnostic that separates edge flicker from a genuine floor problem is
the discard histogram: the anchor stage writes, per reel, the distribution
of fused scores it discarded. Flicker shows a bimodal shape with mass
pressed against the floor from below — boxes fighting to exist — while a
healthy reel's discards fall off smoothly. That histogram is the first
thing to look at when reviewers report flickery edges, and it has correctly
assigned blame every time: twice to exposure changes, once to the loaner
rig's prototype LUT, never to the floor itself.

### 6.3 Downstream starvation

When the farm stalls or compaction collides with a shift, the tracker's
export queue backs up and the wall board shows ledger depth climbing. This
is never a tracker fault and always resolves within the shift; the response
procedure lives in the operations handbook. The tracker's only obligation is
to keep ledgers append-only during the backup, which it does.

### 6.4 Reference-view lies

A rig whose clock has wandered turns in evidence that is subtly wrong: boxes
 land a half frame early or late, crossings resolve a frame too soon, and
nothing about any single reel looks broken. The June audit's rig 3 finding
(1.9 ms of coasting, half a frame at 240 fps) is the canonical case. The
defense is procedural rather than algorithmic: no reel is graded against a
rig with an open skew code, and the quarterly audit exists precisely because
this failure is invisible to every single-reel check. The stage itself takes
no clock from the capture side — it counts frames — but the humans grading
its output read clocks, and that is where the lie enters.

## 7. Benchmarks

All benchmarks run against the February cohort on the two bench boxes,
kestrel and mastiff, which are deliberately not renderlets — benchmarks that
share hardware with production drift when production changes. Nightly
production averages 9.8 million frames across 14 reels at a stage latency of
26 minutes per shift against the 40-minute budget. The full benchmark
procedure, including the crowd and long-hold subsets, takes 3.1 hours on
kestrel and is run on every pin change and every quarterly audit. Since the
2026-02-14 pinning, no benchmark run has regressed more than 0.3 points of
end-to-end accuracy.

Two benchmark disciplines keep the numbers meaningful. First, whole-cohort
runs only: the March draft tables mixed subsets across eras and produced a
week of confusion, so partial runs are now labeled as smoke tests and carry
no decision weight. Second, the bench boxes run no production data: they
replay frozen reels, which means a benchmark can be re-run months later
against bit-identical input, which is the entire basis for comparing a pin
change against its predecessor.

## 8. Appendix

### 8.1 Glossary

Carrier: a tracked subject and its continuous history. Box: the per-frame
rectangle. Ledger: the output record. Coasting: carrying a box through a
hidden stretch on the fitted straight line. Gate: the acceptance circle
around a predicted position. The floor: the anchor score threshold under
which detections are discarded. The roll: the nightly ledger event at 01:30
lab-utc that also retires stale carriers and re-heats the farm's encoder
pool.

### 8.2 Change history

- 2026-02-02 — rewrite landed; motion-first association.
- 2026-02-14 — values pinned; stress test adopted as standing regression.
- 2026-04-22 — occlusion protocol v2 ratified; this document aligned.
- 2026-05-21 — prune-during-association guard became an assertion.
- 2026-06-18 — drift audit folded into failure modes; no values changed.
- 2026-07-15 — document restructured into its current form.
