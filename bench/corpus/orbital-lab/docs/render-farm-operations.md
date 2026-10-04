# Render farm operations handbook

Status: living document. Maintainer: Marco Deluca. First issued 2026-05-28,
consolidating the scattered farm notes after the May review. Audience: whoever
holds the operator handset on a given night, plus anyone changing farm policy.

## 1. Scope and shape

The render farm is 24 nodes in five rows, fed by two capture cages through
the intake hose. It turns closed reels into rendered fragments: overlays draw
the tracker's carriers, the bitrate ladder decides what each fragment costs,
and the QC lane samples the output before anything is called finished. The
farm is cage-agnostic — it neither knows nor cares which cage a reel came
from until the QC reference comparison needs a master.

The farm's product promise is the tail-latency guarantee: a fragment that
enters the queue on a normal night is finished, QC-sampled, and ledgered
within the shift. Every policy in this handbook exists in service of that
promise or in service of honesty when the promise cannot be kept. The farm
never hides a stall, a retry, or a quarantine; the ledger records all three.

The operator's creed, in one line, is: margins are visible, actions are
logged, and nothing is special-cased. A special case is a policy that
applies on Tuesdays or to node renderlet-09 or when Marco is asleep; the
handbook has no such policies, and any attempt to add one must survive the
question "does this hold at 03:00 with nobody in the room?" Most do not,
which is why the farm runs on numbers — watermarks, ceilings, depths —
rather than on judgment calls that cannot be audited the next morning.

Structural facts — rows, node kinds, disk layout, the heat history that
shaped them — live in the topology note. This handbook assumes those facts
and covers operations: the scheduler, the spools, the QC gates, the night
cycle, and what to do at 03:00 when something is wrong.

## 2. The scheduler

The scheduler is a queue with opinions. Fragments enter in priority order:
re-encodes and retries first, then new work oldest-reel-first, then QC
re-renders, which are deliberately last so that a slow night degrades QC
sampling depth rather than delivery. Within a priority class, work lands on
the shallowest eligible node — eligibility being set by node kind, spool
watermarks, and the thermal ceiling described in section 6.

The queue depth is a first-class number: it is on the wall board next to the
spool watermarks, and the nightly health line reports its peak. A healthy
night peaks under 400 fragments; the ceiling of 96 fragments per node in
flight exists so that a queue spike degrades gracefully instead of
overrunning every node's spool at once.

Attempts and requeues are scheduler policy, not node behavior. When a node
reports a stall-class or spool-class failure, the fragment returns to the
front of the queue immediately — no delay, no backoff — and a second failure
sends it to the quarantine bin rather than around again. The ceiling of two
attempts is a ratified decision with its own record; this handbook deliberately
describes the behavior without restating the number, so that the decision and
the procedure cannot drift apart. If this paragraph and the decision record
ever disagree, the decision record wins and this handbook gets patched.

QC gate failures are not retries and never touch the attempt counter. A
fragment that fails its gates routes through the QC protocol's adjudication
lane: the scheduler holds the fragment, the reviewer sees both the fragment
and its master, and the outcome is a ledger entry, not a re-render. This
separation was settled at the March review after a week in which QC failures
silently consumed attempt budget and made the retry numbers lie.

A worked example, since priorities are easier with one: at 02:20 a re-encode
of a twice-failed fragment (priority 1), a fresh fragment from the night's
oldest unfinished reel (priority 2), and a QC re-render ordered by an
adjudication (priority 3) are all waiting. The shallowest eligible node
takes the re-encode; the next node takes the fresh fragment; the QC re-render
waits, and keeps waiting if the night stays busy — by design, because a late
QC sample delays one ledger entry while a late delivery delays a reviewer's
morning. The wall board shows all three classes, so the waiting is visible
rather than mysterious.

## 3. Spool lifecycle

Each node owns two spool disks. Reads and writes are striped so a reel's
read stream never competes with its own write stream; in practice this means
fragments being assembled read from one disk while finished fragments drain
from the other, and the stripes flip at the ledger roll.

Watermarks are the spool's entire public interface: 0.90 means plan (the
operator schedules compaction at the next roll), 0.95 means now (the
operator can force compaction between rolls, and the kindled pool suspends
re-heating to free read pressure). These thresholds were set after the
February stall census, in which 12 of 17 stall events began within 90
seconds of compaction starting on a spool above 0.95 with no alarm
whatsoever. The alarms are the lesson; the thresholds are the calibration.

Compaction runs immediately after the ledger roll, when the queue is
shallowest, and never inside a shift window. This rule cost one line of
scheduler code and bought the end of the stall storms; it is also the rule
most tempting to relax on a night when the roll runs late, and the answer to
that temptation is the February census numbers, which are quoted in the
topology note and in the experiment record for the stall work.

Spool disks are consumables. Each has an expected write volume; the fleet
report tracks wear against it, and disks retire at 90% of expected volume
rather than at failure. The 10% reserve is not conservatism for its own
sake: a disk that fails in service takes its unwritten fragments with it,
and those fragments re-enter the queue as fresh work at the worst possible
moment. Retiring early converts an unplanned failure into a scheduled swap,
which is the whole philosophy of this handbook in one practice. Retired disks go to the QC lane nodes first, where
write volume is lowest, and leave the fleet entirely a quarter later. The
retirement schedule has outrun every failure since the practice began in
March; before that, spool failures were the second most common farm incident
after heat.

The stripe flip at the roll deserves its own sentence of explanation, because
it looks like superstition until the reason is written down. A reel being
assembled reads its source frames while writing its rendered output; on one
disk, those two streams contend for the same heads and the read stream
starves — which is the stall story again, in miniature, every night. The
flip is scheduled code, not operator action, and it is the reason the
per-node stripe layout is identical on all 24 nodes: sameness is auditable,
cleverness is not.

## 4. QC gates in operation

The QC protocol (v2) defines the gates; this section is what running them
feels like. One fragment in 40 is pulled into the QC lane, round-robin over
nodes, so every node is sampled at least twice a night. Pulled fragments are
scored on PSNR against the cage master, on the fragment score, and on program
loudness. Two failing fragments from the same node in one night pulls the
node from the pool until inspected — a node-level gate, because failures
cluster on hardware.

The reviewer-facing truth about the gates: they are calibrated to be
slightly stricter than the reviewers. A fragment that passes both gates is
never, in six months of operation, been returned by review for picture
quality. A fragment that fails them is worth the reviewer's attention about
80% of the time. That asymmetry is the design: the gates should waste less
of the reviewer's night than hand-sampling did, at the price of occasionally
holding a fragment nobody would have complained about.

The loudness gate is the youngest and has already earned its keep: cage
microphone gain was bumped during a February rig service, the picture gates
passed everything, and the loudness gate failed 30 fragments in one night —
every one traced to the gain change, none of them visible on any picture
metric. Before that gate existed, the same class of fault reached reviewers
as "the cage sounds wrong this week" reports, which took days to correlate.
One gate, bought with a line of scheduler code, retired a whole genre of
mystery.

When a gate fails and the cause is texture loss rather than geometry, the
fragment may be re-rendered one ladder rung up under the deviation rule in
the ladder reference. Deviations are logged, and if more than 2% of a
night's fragments ride the headroom rung, the ladder itself is wrong and the
sweep gets re-run. The current ladder has not moved since the May adoption;
the deviation rate has stayed between 0.4% and 0.9%.

## 5. The night cycle

A farm night has a skeleton, and knowing the skeleton is half of operations:

- 01:30 lab-utc — the ledger roll. Ledgers close, compaction runs, the
  kindled encoder pool re-heats against a black clip, stale carriers retire
  upstream, and the nightly health line is written. Everything on the farm
  is timed relative to the roll; moving the roll is a lab-wide event.
- 02:00–02:40 — the deep window. Bulk re-encodes and the previous day's
  adjudicated fragments. Queue depth bottoms out here.
- 03:00–06:00 — capture continues, rendering tracks it. This is the window
  where the farm actually earns its name.
- 06:00 — shift boundary. Counters reconcile, QC lane drains, the morning
  health line goes up with the peak queue depth, watermark highs, thermal
  highs, and the quarantine bin count.

When the roll runs late — a long ledger close, an upstream hiccup — the
compaction window moves with it, and the operator's only decision is whether
the deep window still fits before 03:00. If it does not, capture continues
and the deep work shifts one hour; what never happens is compaction
squeezing into a live shift, which is the February lesson in operational
form. The roll being late is written on the wall board; a silent late roll
is treated as an incident even when nothing else goes wrong, because silent
schedule drift is how the stall storms started.

The 03:14 tidy cron lives inside the deep window and is locked and
idempotent since the March cloning incident. Any new automated job that
writes to a reel or a spool goes through the same review: idempotent or
locked, ideally both, and scheduled inside the deep window unless there is a
reason strong enough to write down.

## 6. Heat, filters, and maintenance

### 6.1 The thermal picture

Exhaust probes drive the fan curve, keyed to the room rather than the die,
because die-chasing oscillates — the heat week demonstrated this at length.
At a die reading of 83 °C the scheduler refuses new fragments and lets the
pool drain before accepting more. The ceiling is soft and is hit perhaps
twice a quarter since fan curve v3 shipped; when it is hit, the wall board
says so and the night operator's only action is to look at row 2's filters
and at the corridor poster that is no longer there.

### 6.2 Filters and facilities

Row 2's filters rotate quarterly, Bram's calendar, and the rotation is the
single most cost-effective maintenance act in the lab's history: the January
week cost four throughput points for five days and its root causes included
filters that had never been swapped. Facilities' heating loop controller
joined the quarterly audit at the same time. Both items are on the wall
calendar next to the drift audit, and both are the operator's to verify, not
to trust.

### 6.3 Maintenance windows

Planned maintenance happens inside the deep window or at the roll. Node
drains for disk swaps or encoder service are announced on the wall board
with an expected return time, and the scheduler treats a drained node as
simply absent — there is no special mode, because special modes are how
nodes get forgotten. A node that misses its expected return gets flagged on
the morning health line, and the flag has caught three forgotten drains since
the practice started.

Encoder service is the one maintenance act that changes node behavior
rather than node availability, so it carries an extra rule: after any
encoder service, the node renders ten QC-lane fragments before it returns
to the pool. Ten fragments is enough to catch the class of fault where the
hardware works but disagrees subtly with its siblings — one March service
left a node with a marginally different output profile that passed single
renders and failed pair comparison. The ten-fragment soak converts that
discovery from "a week of confused adjudications" into "twenty minutes at
the roll".

### 6.4 Pinned environment values

The farm reads its operating margins from the environment at scheduler
start. These are the pinned values, exactly as set with the handbook's first
issue, and their exactness matters — like the tracker's contract, they are
thresholds, not vibes:

- `RENDERLET_THERMAL_CEIL_C=83` — the soft ceiling; above a die reading of
  83 °C the scheduler refuses new fragments. Rationale: the January week's
  throttle onset sat at 84–87 °C measured, and one degree of margin is the
  difference between a drained pool and a throttled farm.
- `RENDERLET_SPOOL_WATERMARK=0.90` — the plan-now watermark; 0.95 is the
  hard alarm and is deliberately not an environment knob, because the alarm
  that can be tuned away is the alarm that gets tuned away.
- `RENDERLET_QUEUE_DEPTH=96` — per-node in-flight fragment ceiling. Exists
  so a queue spike degrades gracefully; raising it moves the failure from
  the queue to the spools, which is strictly worse.
- `RENDERLET_REQUEUE_DELAY_S=0` — immediate requeue between retry attempts.
  The zero is contractual and mirrors the decision record; a nonzero value
  here would silently repeal the ratified policy.
- `RENDERLET_NIGHTLY_ROLL=01:30` — the roll time the scheduler assumes when
  timing compaction and pool re-heat. Must match the ledger roll hour in the
  configuration reference; the handbook and the config file are checked
  against each other at every quarterly audit.

Changing any pinned value requires: a ledger note, a line in this section's
history, and — for the thermal ceiling and the requeue delay — ratification
at a farm review, because both encode decisions rather than calibrations.
The values have been stable since the handbook's first issue and the
stability is itself the record: nothing here has needed to move.

## 7. Incident index

The farm's named incidents, with pointers; details live in the notes.

- The melting GPU week (2026-01-12 to 2026-01-16). Three-way root cause:
  facilities loop overshoot, packed row 2 filters, one poster. −38%
  throughput for five days; recovered to 97% of baseline by the Friday.
  Produced fan curve v3, the thermal ceiling, the filter rotation, and the
  lab's entire maintenance culture.
- The stall storms (week of 2026-02-02). 17 stall events on one node,
  compaction-collision shaped, mean silence 2.3 seconds. Zero events in 14
  shifts after the fix. Produced the compaction window rule, the watermark
  alarms, the read-cache bump, the stall census, and the retry decision's
  evidentiary base.
- The midnight cloning incident (2026-03-03, caught 2026-03-04). A tidy cron
  ran twice after a clock step and cloned 512 frames into a closed reel.
  Caught by the digest at the boundary; one day of reel delay, no data lost.
  Produced the lock-and-idempotent rule for reel-writing jobs.

The index is deliberately short. Incidents get names when they teach
something structural, and the naming bar is high; near-misses stay in the
ledger without earning a paragraph in a handbook.

## 8. Handover checklist

Between operators, every night, in order:

1. Wall board read and spoken aloud: queue peak, spool highs, thermal high,
   quarantine count.
2. Ledger roll completed and health line present; if the roll is late, say
   so and say why.
3. Quarantine bin walked: every fragment has a disposition or a reason to
   wait for morning.
4. Any drained node has an owner and an expected return.
5. QC adjudication lane empty or explicitly carried over.
6. The bin of unlabeled media near row 3 is, as always, not yours to throw
   away. Ask Marco.

The checklist fits on one page and is taped inside the operator handset's
cover. It has been shortened twice; resist the urge to lengthen it, and
resist harder the urge to skip it on a quiet night, because quiet nights are
when item 4 catches the forgotten drain.

Item 1 is spoken aloud even when the operator is alone, which took some
getting used to and survived because it works: saying "queue peak 340,
spools under 0.8, thermal high 79, bin empty" engages a different kind of
attention than reading the same numbers, and two of the near-miss catches
last quarter came from an operator hearing themselves say a number that was
wrong. The health line automates the collection of these numbers; it cannot
automate noticing them, and the handover exists precisely to manufacture
one guaranteed moment of noticing per night.

## 9. Appendix

### 9.1 Contacts and ownership

Farm policy: Marco Deluca, ratified at farm reviews. Capture and intake:
Bram Oosterhuis. Tracker behavior on rendered overlays: Priya Chandrasekhar.
Decisions and appeals: Ingrid Halvorsen. Facilities loop: the quarterly
audit, and only the audit — operators do not touch valve controllers.

### 9.2 Glossary

Quarantine bin: where twice-failed fragments wait for morning triage. The
roll: the 01:30 nightly ledger event. The deep window: 02:00–02:40, the
farm's quietest hour. Stragglers: row 5, retired from bulk work, kept for QC
renders and pool experiments. The kindled pool: eight pre-heated encoder
processes, the subject of the January experiment that killed the torpid
shift opening.

### 9.3 History

- 2026-05-28 — handbook first issued, consolidating scattered notes.
- 2026-06-25 — environment values cross-checked against the new
  configuration reference; both agree.
- 2026-07-15 — incident index re-ordered chronologically; no policy change.
