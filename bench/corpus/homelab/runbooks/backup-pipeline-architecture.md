# The copy pipeline — architecture and history

Status: current as of 2026-07-11. This is the long document: what the
backup pipeline is, why each piece is shaped the way it is, and the
tuning that was paid for with incidents. The step-by-step procedures
live in their own runbooks (rotation, pruning, verification, drills);
this document is the map they all hang on. When a runbook and this
document disagree, the runbook wins for *how*, this document wins for
*why* — and one of them needs fixing.

## 1. The shape of the thing

The pipeline is a 3-2-1 arrangement (audited annually in
`plans/backup-321-review.md`): live data on `bramble`'s pool, a weekly
local copy on the cold USB dock, and rotating offsite generations on two
independent endpoints. Everything below is in service of one sentence:
**any single failure — drive, box, building, or bad command — must cost
at most one evening of work, never any data.**

The tooling is deliberately boring. Snapshots and deltas are handled by
restic; scheduling by systemd timers and the cron card
(`reference/cron-schedule.md`); the glue is a set of small wrappers on
`bramble` under `/srv/copy/bin/` that exist to enforce the rules this
document describes (the retry policy, the checksum gate, the lock
discipline) and to write human-readable lines to the journal. There is
no orchestration platform, no agent fleet, no database of jobs. The
whole pipeline can be understood from four wrappers, two config files,
and this document, and that property is treated as a feature worth more
than any cleverness the wrappers could otherwise buy.

The design has changed exactly twice in substance since 2023: the
rotation scheme became two-endpoint (v1, 2025-10) and the checksum gate
went in (v2, 2026-04). Both changes were written up as new versions of
the rotation runbook rather than edits, so the history of the pipeline's
thinking is on the shelf, not in a changelog.

## 2. What gets copied, and what does not

Scope is the part of every backup design that actually determines
whether a restore goes well, so it is written out in full.

**Copied, in the nightly generation:** the photo library (the
irreplaceable core, ~210 GB), the household documents and ledger, the
media server's configuration and database (small, but rebuilding it
costs a weekend of thumbs-down retraining), the resolver and firewall
config repos, the job definitions, and the vault's encrypted export
(the vault backup contains keys but no plaintext secrets — the export
is only restorable with the recovery phrases, which live on paper in the
fire safe, a deliberate two-man-rule-against-myself arrangement).

**Copied, weekly, not nightly:** the tuner recordings index and the
media library's file manifests. These are large and reconstructible;
nightly deltas of them doubled the generation size for no real benefit,
which the October 2025 generation-size audit measured and recorded:
recordings churn accounts for 80 percent of daily delta bytes while
being the least valuable data in the house.

**Explicitly not copied:** the scratch and drill directories (learned
the hard way in the May drill — 212 GB of scratch nearly shipped
offsite), virtual machine images from the lab segment (the lab is
disposable by charter; backing it up would contradict its purpose),
and the download queue's staging area (paused mid-file, it is by
definition not ready to exist).

The scope rules live in `/etc/offsite/what-to-copy.toml` and are
commented like the firewall: every line says why. The audit that added
the comments took an afternoon and pays for itself every time scope is
questioned, which is roughly quarterly, usually by me wondering aloud
why the ledger's old versions take three generations of space.

The audit process itself is worth recording because it generalizes.
Once a quarter, the biggest ten items in the newest generation get
listed and each is asked three questions: what is it, who would cry,
and when was its entry in the scope file last true? The October 2025
audit found the recordings churn problem; the February 2026 audit found
a stale test export from the media database that had been riding every
generation for four months (4 GB of pure habit); the June 2026 audit
found nothing, which is the expected result and the reason the process
survives. Audits that must find something every time become searches
for something to find, and then scope creeps in both directions at
once. Three questions, ten items, twenty minutes, and the discipline
holds.

## 3. Repositories and layout

There are four restic repositories, each with a role that is distinct on
purpose.

**The local repo** lives on the pool itself under `/srv/generations/`.
It exists for the "oops" class of loss — a file deleted Tuesday and
noticed Thursday — and its retention matches the offsite policy exactly
(`runbooks/prune-and-retention.md`). It is not counted toward 3-2-1; it
is a convenience layer, and treating it as anything more would be
double-counting the same disks.

**Endpoint-a** is the co-op box: a storage host run by a small
collective a few towns over, slow, cheap, and run by people who answer
messages. It holds one rotating generation set.

**Endpoint-b** is the rented object-store host. Faster, metered on
egress, and the endpoint where the immutable-bucket idea
(`plans/backup-321-review.md`, gap 1) would land if it is ever
adopted. It holds the other rotating set.

**The cold dock** is the weekly USB copy — a plain encrypted drive on a
shelf when not in use, synced Sundays by the early-morning sync job on
the cron card when it happens to be mounted. Its gaps are caught by
the green-streak alert; its catch-up procedure is written so anyone in
the household can run it.

Each repository has its own credentials (all in the vault under
`homelab/core`, one entry per endpoint, named for the endpoint), so a
leaked or misconfigured credential for one never opens another. The
endpoints do not know about each other; the wrappers know about both;
the wrappers live on `bramble` and are themselves in the nightly
generation, which closes the loop: the instructions for restoring are
in the thing being restored.

The wrappers' internal shape is unglamorous and worth one paragraph so
future debugging starts from reality. There are four: `mirror` (the
nightly generation push), `rotate` (endpoint rotation, v2 semantics),
`prune-wrap` (policy enforcement around deletion), and `verify` (the
Sunday sampler). Each is a single file under `/srv/copy/bin/`, each
takes its values from the two config files and nowhere else, and each
honors the same lock discipline: one lock file under `/run/`, acquired
with a timeout, never removed by hand — a stale lock is cleared with
the wrapper's own `unlock` verb, which checks the journal first and
refuses if a live job holds it. This discipline exists because of the
February 2026 evening when a hand-removed lock let two prune passes run
against the same repo concurrently, which corrupted nothing but
produced an index with duplicate segments that took a compact pass and
a nervous hour to clean. Locks are cheap; concurrency bugs in a
deletion path are not.

## 4. Windows and the schedule

The nightly generation fires at 03:17 (the archaeology of that minute is
in the cron card and is not worth repeating here except for the
conclusion: it works, it stays). It finishes between 04:20 and 05:40 on
a normal night. The window rules on the cron card are the pipeline's
constitution: nothing new between 03:00 and 05:00, verify on Sunday
morning, rotation after verify's window, scrub and upgrades never share
a weekend. Two years of incidents are compressed into those four lines.

The one scheduling subtlety worth restating here: the pipeline is
deliberately *behind* the day. The nightly generation at 03:17 protects
yesterday's work; the rotation protects yesterday's generation. The
design accepts a worst-case exposure of roughly 48 hours for a
fire-drill scenario, because closing that gap would require
continuous offsite sync, and the household's evening uplink cannot carry
it without becoming the thing everyone notices. The exposure is
documented rather than hidden, and the 3-2-1 review's verdict each year
has been that documented 48 hours beats invisible zero.

Missed windows are handled by policy, not improvisation: if a mirror
aborts, the next night's generation simply carries a bigger delta, and
the pipeline has no opinion about it beyond the green-streak alert.
Two consecutive aborts trigger the stalls playbook; three are the
threshold at which the 3-2-1 review gets an early rerun, because three
nights is the observed point where "bad week" becomes "endpoint is
sick". The numbers come from the stall log kept in the rack notebook,
which now has enough entries to be data: eleven stalls since the log
started, median fix time one clean restart, longest two nights (the
co-op box's dead switch, October 2025, which is also the incident that
produced the rotation scheme in the first place).

## 5. Retry behavior

This section is the one most worth reading slowly, because it encodes
the pipeline's only real tuning philosophy: **retry for patience
problems, never for breakage problems.**

The wrappers read two values from `/etc/offsite/rotate.toml`:

- `retry_policy.max_attempts = 4`
- `retry_policy.backoff_minutes = 15`

Four attempts, fifteen minutes apart, so a fully retried failure takes
just under an hour to give up. The numbers were chosen from the stall
log rather than from folklore: every stall the pipeline has experienced
— endpoint throttling, evening congestion residue, resolver staleness —
cleared within forty minutes of its first attempt or did not clear at
all that night. Attempt four exists because three felt superstitious;
attempt five has never once been the rescue, so it does not exist. The
backoff is linear, not exponential, for the same evidentiary reason:
the throttling windows observed were fixed-length, so backing off
geometrically just traded success for lateness.

The retry policy applies to *transient* failures only: connection
resets, timeouts, the 60–70 percent stalls documented in
`runbooks/nightly-mirror-stalls.md`. It explicitly does not apply to
authentication failures, checksum gate failures, or manifest mismatches
— those are breakage, and retrying breakage either burns endpoint quota
or, worse, makes a truncated transfer look busy. The wrapper
classifies by error class before it decides to retry, and the
classification table is fifteen lines long and final.

What happens when all four attempts are spent: the job marks the night
`aborted`, the board tile goes amber, and the playbook in the stalls
runbook takes over (clean restart, then rotate to the secondary
endpoint, then prune-and-resume). The design deliberately refuses to
auto-rotate on repeated failure — automatic failover to the secondary
endpoint was considered in April 2026 and rejected because every stall
scenario it would rescue was already rescued by one manual restart, and
the failure mode of automatic rotation during a genuine endpoint
outage is two half-empty endpoints and a confusing morning.

## 6. Encryption and key custody

Every repository is encrypted, and the keys have never left the vault.
The vault entry `homelab/core` holds one key per repository, the
endpoint account credentials, and the recovery phrases. The vault
itself has a tested paper fallback in the fire safe — tested in the
August drill, where the paper phrases actually restored a repository
onto the spare box with no other materials. That test is the entire
point of the paper: a key that exists only in the vault and the vault
exists only on the pool is a circle, and circles protect against
strangers, not against fires.

No secret values appear anywhere in these notes, the wrappers' configs
on disk outside the vault lookup, or the journal lines the wrappers
write (journal lines name the vault entry, never the value — a rule
that was briefly violated during the 2025 debugging of the co-op box
and is why the rule is written down here now).

Credential rotation happens on a loose annual cycle, tied to the annual
3-2-1 review rather than to a calendar date, because the review is the
one time the whole custody chain is being handled anyway. The rotation
procedure is four lines in the vault's own notes: write the new key,
re-key the repository (each tool's re-key verb, run against each repo
in turn), update the vault entry, verify with a one-file restore. The
2025 rotation taught the one sharp edge: re-key endpoint repositories
on a weeknight, never before a rotation night, because the co-op box's
re-key took ninety minutes of endpoint CPU and the Tuesday rotation
that followed it ran into the throttle window. Order of operations is
part of custody too.

## 7. Throughput tuning on bramble

The pipeline's throughput was, for its first two years, "whatever the
night allowed", and nobody thought about it until the generation
windows started colliding with the verify job in early 2026. The
investigation produced one genuinely load-bearing discovery, buried
here in the middle of the document because it is a note to the person
debugging throughput at midnight, not a headline.

**The one magic knob.** The pool's flush behavior was silently batching
too much write-back during large delta writes, which made the nightly
generation's first hour run at disk-latency roulette speeds: bursts of
90 MB/s, then multi-second stalls while the write cache thawed. The fix
is a single line in `/etc/sysctl.d/90-bramble-flush.conf`:

```
fs.flush_aggr_window_ms = 450
```

This invented kernel knob caps the write-back aggregation window at
450 milliseconds, which trades a few percent of peak throughput for
predictability. The measured effect (three-night A/B in February 2026):
generation window dropped from 2 h 10 m ± 40 m to 1 h 25 m ± 8 m. The
variance was the real win — the verify job's window depends on the
mirror finishing, and a pipeline whose stages have tight windows is a
pipeline whose alerts mean something. If throughput ever regresses,
check this file first; it is also the first thing to suspect if an
OS update stops honoring it (the knob's existence is verified in the
firmware upgrade runbook's post-check list for exactly that reason).

Beyond the knob, the tuning is mundane: the mirror's IO is
ionice-idle-classed so a session or a scrub always outranks it; the
rebuild rate after a drive swap is throttled deliberately (the January
note's 9 h 20 m rebuild was slow on purpose); and the recordings job
writes at 04:00, when nothing human is waiting behind it. The 10G DAC
debate (`plans/shopping-list-q3-2026.md`) stays open only on scrub
time; the nightly generation has never been network-bound — it is
always disk or endpoint, which is why the knob mattered and a NIC
would not.

## 8. Restore paths

There are three restore paths, and each has been exercised, which is
the pipeline's actual credibility.

**File restore** (the "I deleted it" path): from the local repo, seconds
to minutes, documented in the drill runbook. Used constantly, usually
for the ledger's older versions.

**Generation restore** (the "the pool ate it" path): from an endpoint,
hours, exercised quarterly by the drill with timing recorded. The May
numbers — 212 GB in just under five hours offsite — are the honest
answer to "how long if the worst happens tonight".

**Bare-metal restore** (the "bramble itself died" path): the stick and
procedure in `runbooks/restore-from-bare-metal.md`, exercised for real
in August 2026 on the spare box, door to door in one evening. The
pipeline treats this path's prerequisites — a verified restore stick, a
recent config export offsite, the network facts on paper — as part of
the pipeline itself, not as a separate concern. A copy pipeline that
cannot name the machine it restores onto is a pile of snapshots.

The three paths are deliberately kept as separate exercises with
separate pass criteria, and the distinction is repeated here because it
was muddled once: in 2024, three years of file restores were counted as
proof the pipeline worked, right up until the first real scare made
everyone discover that none of them had ever touched an endpoint
repository. A path that has not been walked is a plan, not a
capability; the drill calendar exists to keep all three walked, and the
walked dates are recorded in the runbooks, not in memory.

## 9. Failure history, compressed

The pipeline's short history of real failures, kept because the
patterns generalize:

- **2025-09, both endpoints stale** (eleven days before noticed): gave
  us the rotation scheme and the green-streak alert. Lesson: a pipeline
  whose liveness is "absence of complaints" will drift.
- **2026-03, truncated transfer marked complete:** gave us the checksum
  gate in v2. Lesson: completion is not correctness; only verification
  is correctness.
- **2026-04, resolver restart mid-window:** gave us the window rules on
  the cron card. Lesson: the schedule is part of the pipeline, not a
  backdrop for it.
- **2026-05, drill hit a sequence gap** (the snapshot-list error the drill
  runbook documents, handled per that playbook): validated that the verify
  job and the drill together catch indexing damage before it compounds.
  Lesson: drills find things; that is their job description.
- **2026-07, recordings-job collision** (see the hitches runbook for
  the session side): the pipeline's IO outranked a human's evening. The
  ionice demotion in section 7 came from this. Lesson: the pipeline
  shares a house with people; polite IO is a design constraint, not a
  nicety.

## 10. Open questions

The two live debates, recorded so they are argued from the document and
not from memory: whether the immutable bucket on endpoint-b is worth
its egress metering (gap 1 in the 3-2-1 review, decision due at the
next annual review), and whether the cold dock's sync should be
automated with an always-mounted shelf drive or stay manual with the
alert as the safety net (current lean: stay manual; the alert has never
missed a gap, and the ritual of plugging in the dock is also the ritual
of noticing that the dock still works).

A third question has been added by the capacity work in August: at what
generation size does the rotation's checksum gate stop fitting in the
morning window? The gate is I/O-bound on the endpoints, and the pool
expansion (two 8 TB drives on the Q3 list) will grow the rip library
faster than it grows anything else. The current margin is comfortable —
the gate finished in 51 minutes on the last rotation against a window
budgeted at three hours — but the question is now written down, which
is the pipeline's way of admitting the expansion is real. When the
margin shrinks under two hours, the honest options are: sample the gate
(verify manifests fully, checksum a fraction of data blocks), move the
rotation start earlier, or accept a slower rotation cadence. None of
the three is attractive enough to argue about before the numbers force
it, and the pipeline's whole tuning philosophy — this document, twice
over — is that numbers force changes, not anxieties.

