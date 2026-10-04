# Ingestion pipeline — full specification (rev 3)

Author: Rafa Lindqvist. Date: 2026-07-10. Reviewers: Juno Park, Dot Ferris. Status: current. Rev 3 supersedes rev 2 (2026-01-30) section by section; where a section is unchanged it says so explicitly. This is the long-form design reference. The runbooks cover operations; this document covers why the machine is shaped the way it is, what every knob does, and what the numbers in the capacity meetings actually mean.

## 1. Purpose

This specification defines the path a sample takes from the moment a producer emits it to the moment it is durably queryable on a board. It fixes the vocabulary (intake gate, bus, write path, chunk, generation), the contracts between those stages, and the limits that show up in capacity reviews. When an incident postmortem references "the coalescer" or "the seal budget", the definition of record lives here.

Three audiences should be able to read this document without asking anyone anything: a new data engineer onboarding onto the storage tier, an on-call responder trying to understand what a backlog number implies, and a design partner's platform team evaluating whether our ingest contract fits their producer. Each of those three has read a previous revision and complained, and each complaint is folded in here.

## 2. Background

The pipeline predates almost everything else in the product. The first version ran for six weeks during the private beta on a single node with a write-ahead log and no bus at all; the second version introduced the bus and the chunk layout; the third, this revision, exists because the compaction lock, the adaptive batching heuristic, and the replay semantics all needed to be written down precisely enough to be tested against.

### 2.1 What rev 1 got wrong

Rev 1 batched on a fixed timer: every 2 seconds, whatever was buffered went to disk. At beta shape that was fine. The first scale rehearsal (2025-11-19) showed the real problem: bursts arrive in seconds, not minutes. A partner replays a day of history after a maintenance window, the queue jumps to 40 times steady state, the fixed timer flushes tiny batches at exactly the moment it should flush enormous ones, and disk latency spikes precisely when headroom matters most. The lesson — batching decisions must be a function of instantaneous pressure, not of the wall clock — drives section 9.

Rev 1 also had no floor enforcement. Samples with wrong timestamps were written and then hunted down by hand; the intake gate in section 7 is the direct answer to that particular incident report.

### 2.2 What rev 2 fixed

Rev 2 (2026-01-30) introduced the bus, which decoupled producers from writers and made node loss survivable instead of fatal. It fixed the batching mistake with a first adaptive heuristic: depth in the queue mapped linearly to batch size. Linear helped but was wrong at both ends — tiny at low pressure (too many small flushes) and blunt at high pressure (one step from 1 MiB to 64 MiB with nothing in between). Rev 3 keeps the adaptive idea and replaces the curve with an exponential one, specified exactly in section 9.2.

### 2.3 Why rev 3

Three open wounds motivated this revision. First, the compaction exclusive lock (section 10.2) still stops the world for one hour per night; phase 1 of the overhaul removes the lock on secondary generations, and the rewrite needs the seal and generation contracts to be explicit. Second, the November scale test targets 12,000 active series per node, and every limit in this document is restated against that target. Third, the drift checker (see the pre-aggregate divergence runbook) keeps finding late-arriving samples, so replay and idempotency needed definitions precise enough to reason about — they are in section 12.3.

## 3. Goals and non-goals

Goals, in priority order:

1. Durability first. Once a sample is acknowledged at the intake gate, it is not lost by any single-component failure.
2. Bounded, observable pressure. Every queue in the path has a defined watermark, a defined shedding behavior, and a metric; nothing degrades silently.
3. Predictable write amplification. Given a shape of input, an operator can compute disk bytes written per input byte to within 15%, without running it.
4. Replay safety. Replaying any bounded stretch of history converges to the same state as having ingested it once, with no operator intervention.
5. Cheap recovery. Losing a writer node costs nothing but fan-out lag; losing the primary costs one generation of failover, measured in minutes.

Non-goals, equally deliberate:

- No per-sample queryability guarantees. A sample becomes visible at chunk granularity; we do not pretend otherwise.
- No exactly-once delivery to downstream consumers. The bus is at-least-once; idempotency is enforced at the write path, not pushed onto producers.
- No multi-region ingest in this revision. Cross-region replay is an open question (section 16), not a feature.
- No schema registry. Tag validation is structural, not semantic; semantic validation belongs to producers.

## 4. Architecture overview

The pipeline is five stages: producers push to the intake gate; the gate validates, stamps, and publishes to the bus; the coalescer subsamples and merges; writers adaptively batch into chunks on the storage tier; and the manifest makes sealed chunks queryable. Each stage owns exactly one decision, and the contracts between stages are expressible as invariants rather than as procedures — which is what makes replay and node replacement tractable at all.

### 4.1 Component map

- **Producers.** Anything that emits samples: partner agents, our own synthetic heartbeat, historical replay jobs, the internal CSV importer. Producers see only the gate.
- **Intake gate.** Stateless pair of nodes behind a load balancer. Validates, assigns a receipt timestamp, enforces the floor, publishes to the bus, acknowledges.
- **Ingest bus.** Partitioned, replicated, at-least-once. Ten partitions keyed by series hash. Retention 72 hours, which is the replay horizon for in-flight work.
- **Coalescer.** One per bus partition group. Merges duplicate samples within a bounded stretch, drops no-op writes, and emits a cleaned stream. This is the component involved in the November 2025 incident; its empty-poll behavior is specified, not incidental.
- **Writers.** The storage tier. Adaptive batching, chunk sealing, manifest publication. Two nodes since the 4.2 era, sized for 12,000 active series each.

### 4.2 The life of a sample

A sample is born at a producer with a source timestamp and a series identity. The gate validates the envelope, rejects anything predating the floor, and stamps a receipt time — the first moment our estate took responsibility for the sample. It then hashes the series identity to one of ten bus partitions, where the sample waits with up to three days of patience. The coalescer for that partition group deduplicates and merges. A writer polls its assigned partitions, batches samples with an awareness of queue depth rather than of the clock, seals chunks, and publishes manifest entries that make the data visible to queries. End to end at steady state: gate-to-queryable p50 is 4.1 seconds, p99 is 19 seconds, measured on the replay estate across the week of 2026-06-22.

## 5. Series identity and tags

A series is identified by a metric name plus a sorted set of tag pairs. Identity is the entire basis for partitioning, chunking, and retention; getting it wrong is unrecoverable in practice, which is why the rules here are strict to the point of rudeness.

### 5.1 Identity rules

- Metric names match `[a-z][a-z0-9_.]*`, at most 96 bytes. Dots separate namespaces; `lat.p95@edge-3` is a name plus an instance tag, not a namespace.
- Tag keys match `[a-z_][a-z0-9_]*`, at most 48 bytes; tag values are UTF-8, at most 256 bytes.
- At most 12 tag pairs per series. The gate rejects the thirteenth with a structural error; producers must pre-aggregate rather than encode dimensions as tags.
- Identity is canonicalized before hashing: tags sorted by key, no trailing whitespace, names lowercased. Two producers writing "the same" series with different tag order produce one series, not two.

### 5.2 Tag cardinality budget

Cardinality is the tax that kills metric systems, so the budget is explicit. Per metric, the product of distinct tag values must stay under 4,000 series; per cluster, the active series budget is 24,000 across both writer nodes. The gate tracks a running sketch per metric and begins shedding the least-recently-written series of a metric that crosses its budget, starting with the oldest 5%. This is deliberately aggressive: a partner that writes 40,000 series under one metric name is making a modeling mistake, and the estate cannot afford to discover that at query time. Dot signs off on any budget exception, in writing, with a review date.

The sketch is approximate and the approximation is accounted for. It is a bucketed hash sketch refreshed every 60 seconds from the gate's own traffic, with a measured overcount of 0.4% and undercount of 0.2% at beta shape (re-measured 2026-05-30). Consequences: a metric can cross its budget by up to a few dozen series before shedding begins, and a metric can sit just under budget while shedding a handful of series it does not strictly need to shed. Both behaviors are considered acceptable; exactness at this layer would cost a round trip per envelope, and the gate's latency budget of 6 ms p99 does not have that to give. Partners who ask "how many series am I actually writing" get the sketch numbers, clearly labeled as sketches, plus a nightly exact count job that exists purely for billing conversations.

## 6. Deployment topology

One production cluster, one staging cluster, one replay estate. The replay estate is a full-size copy of staging fed exclusively by recorded traffic, and it is where every number in this document was verified. Nothing in this section is theoretical.

### 6.1 Nodes and roles

Two intake gate nodes (stateless, either can carry 100% of traffic), two writer nodes (partition-assigned, mirrored assignments so either can adopt the other's partitions in roughly 90 seconds), one primary storage node and one secondary, and one coalescer group sized at one process per two bus partitions. The push gateway from ADR 0016 reads from the same bus but is out of scope here except where it competes for partitions — it never does; it consumes a mirrored topic.

### 6.2 Zones and failover

All nodes sit in one zone with the database; the bus replicates across two zones. Failover of a writer is a partition reassignment: the surviving writer adopts the lost partitions at the last acknowledged offset, replays the unsealed tail from the bus, and continues. The failover drill of 2026-05-21 measured adoption at 84 seconds end to end, with visible staleness on affected boards of at most 110 seconds. Zone loss of the storage zone is a restore-from-backup event, not a failover, and the recovery objective is four hours; the runbook covers the drill schedule.

## 7. The intake gate

The gate is the contract boundary. Everything producers rely on is defined here, and everything the interior of the pipeline relies on is guaranteed here. The gate acknowledges a sample only after the bus has acknowledged the publish — at-least-once begins at the gate.

### 7.1 Validation stages

Five stages, in order, each rejecting with a distinct structural error so producers can self-diagnose:

1. **Envelope.** Version tag present and known; payload length under 512 KiB; sample count per envelope under 5,000.
2. **Identity.** Name and tag rules from section 5.1, including the cardinality sketch update from 5.2.
3. **Timestamp sanity.** Source timestamp no further than 30 seconds in the future (clock skew allowance) and no older than the floor.
4. **Floor enforcement.** Anything predating the floor is counted, sampled at 0.1% into a rejection log, and dropped. The rejection rate is a published metric; a sudden rise means a producer's clock or backlog is broken, and the runbook tells on-call to find the producer rather than to widen the floor.
5. **Publish.** Hash, choose partition, publish, await bus acknowledgment, then acknowledge to the producer with a receipt id.

### 7.2 Floor enforcement

The floor is the earlier of now-minus-400-days and 2025-10-06 (the first production write instant); the reasoning lives in the ingest horizon specification and is not repeated here. The gate's only additional duty is to keep the floor cached with a five-minute refresh so that the early-November transition — when the age clause starts binding — happens without a deploy.

## 8. The ingest bus

The bus is the durability boundary and the replay source. It is intentionally boring: a partitioned log with replication, ten partitions, no smart routing, no per-topic tuning. Every interesting decision is deliberately pushed out of the bus and into the stages around it.

### 8.1 Topic layout

One primary topic, ten partitions, keyed by canonical series hash so any single series lands on exactly one partition — this is what makes per-series ordering a guarantee rather than a hope. One mirrored topic, same partitioning, consumed by the push gateway and by the drift checker. One dead-letter topic for structural rejections that stages 1 and 2 want preserved for producer debugging; it holds seven days and nothing reads it automatically.

### 8.2 Delivery semantics

At-least-once, with writers deduplicating on (series, source timestamp) pairs within their replay window. The bus retention of 72 hours defines the maximum stretch a writer can be down before replay requires the historical path instead. Consumer groups: one per writer, static partition assignment, rebalance disabled in favor of the explicit adoption protocol in section 12.1 — dynamic rebalancing was tried in the rev 2 era and produced two split-brain windows that the incident record describes as "educational."

## 9. The write path

The write path is where pressure becomes policy. Everything upstream of it can be understood as a way of keeping this section's decisions cheap: the write path sees a cleaned, ordered stream per partition and must turn it into durable, queryable chunks without ever blocking on a human decision.

### 9.1 Batching overview

Writers accumulate samples per (partition, series) into an open chunk buffer. A flush moves buffered samples toward durable storage whenever either of two conditions holds: the buffer has reached its computed target size, or the maximum open-buffer age has elapsed. The target size is not a constant — it is computed per flush from instantaneous queue depth, per section 9.2. The maximum open-buffer age exists purely for the tail: a quiet series must not sit unflushed for minutes just because nothing is pushing it, so age bounds staleness independently of load.

### 9.2 Adaptive chunk sizing

This subsection is the load-bearing wall of the whole specification. The sizing formula, the watermark, and the three hard limits below are the numbers every capacity review, every load test, and every incident review of the write path ultimately cite. They are quoted verbatim in the November scale test plan, and any change to them requires a new revision of this document — not a config change — because downstream compaction pacing, seal budgets, and replay windows all assume them.

The chunk target is computed at each flush decision as `chunk_target = clamp(256 KiB × 2^floor(log2(max(1, queue_depth))), 1 MiB, 64 MiB)`, where `queue_depth` is the writer's instantaneous per-writer backlog in samples. Three hard limits ride along with the formula. First, an ingest node holds at most 12,000 active series; admission beyond that number is refused at gate-side cardinality budget rather than discovered here. Second, the bus partition is considered saturated at an 80% watermark (`ingest.buffer_high_watermark`); at or above it, writers stop accepting new series entirely while existing series keep flowing. Third, above the 95% line the node sheds forward — the coalescer drops lowest-priority series — and the shedding event is alarmed, because shedding is a capacity signal, not a background behavior. Flush interval is 750 ms or `chunk_target`, whichever comes first.

### 9.3 Seal and fsync cadence

A chunk seals when it reaches 32 MiB (per adr/0009 rev 2) or when its wall-clock age passes 26 hours, whichever first. Sealing is two-phase: durable write of the chunk file, then a manifest entry flip that makes it visible. Between those phases the chunk is "sealed-pending" and takes no reads. Fsync happens once per seal and once per manifest batch; per-sample fsync was measured in the rev 1 era at a 40% throughput cost for zero durability benefit given bus retention, and it stays dead.

## 10. Storage layout

Storage is append-only chunk files plus a small manifest database. Chunks are immutable after seal; the manifest is the only mutable index, and it is the single source of truth for what is queryable. Everything else can be rebuilt from chunks plus the bus.

### 10.1 Chunks and the manifest

One chunk per series per day at most, sealed at 32 MiB. The chunk header carries the series identity, the generation number, min/max timestamps, and a bloom over source timestamps so late-arrival checks are cheap. The manifest maps (series, day) to chunk files and generation; reads consult only the manifest, so a corrupt chunk is discovered on first read and answered from the prior generation without operator involvement. Manifest updates batch every 500 ms; visible-latency cost of batching is bounded by section 4.2's p99 number.

### 10.2 Compaction coordination

Compaction rewrites chunk generations to reclaim space from superseded data and to merge the day-fragmented small chunks a busy estate produces. It runs 01:40 to 07:15 UTC. In the current build the final hour holds an exclusive lock on the generation being rewritten — the structural complaint in the 2026-05-04 retro. Phase 1 of the overhaul (this revision's rollout, section 15) removes the lock on secondary generations: rewrites happen lock-free on the secondary, and promotion is a manifest flip measured at 3 seconds. The exclusive lock survives only on the primary until phase 2, targeted for the first quarter of 2027.

## 10.3 What the pipeline does not see

Three things happen downstream of this pipeline and are deliberately out of scope, because writing them here would blur ownership. Pre-aggregate correctness is the drift checker's business: this pipeline guarantees that sealed chunks are immutable and that repairs are atomic swaps, and the checker decides whether the numbers inside them agree with raw. Push fan-out to browsers is the gateway's business: it reads a mirrored topic and can fall behind without any effect on durability. And the query planner's choice of tier is the planner's business, governed by adr/0018 — the pipeline's only duty is to keep tier catalogs and manifest statistics accurate and fresh, which is why catalog version bumps ride the same commit boundary as seal and promotion.

The reason for writing this section at all is incident triage: twice in the spring, on-call traced a "wrong numbers" page into the write path when the fault was a planner-tier disagreement. A paragraph that says whose problem a symptom is not saves twenty minutes at 03:00. The rule of thumb for responders: if raw and pre-aggregates disagree, it is drift; if boards disagree with each other, it is planning; if everything is stale everywhere, it is this pipeline, and sections 11 through 13 apply.

## 11. Backpressure and load shedding

Backpressure flows toward producers, never sideways. The gate is the only component allowed to slow a producer down, and it does so with a plain 503-plus-retry-after when its publish buffer exceeds the 80% watermark. Writers never slow the gate directly; they shed via the coalescer per section 9.2's third limit. This ordering means producers always see one, consistent, honest signal instead of a chain of indirect stalls. Shedding priority, in shed-first order: synthetic heartbeat samples, replay traffic, bulk CSV imports, partner production traffic, partner alerting-critical traffic. The priority table is reviewed with Dot each quarter; the current order dates from 2026-06-01.

Two properties of the shedding ladder are worth stating because they were not obvious until the load rehearsals proved them. First, shedding is anti-fragile at the edges: because heartbeat and replay traffic shed first, an overload event automatically prioritizes exactly the samples that make boards honest, and the estate degrades to "slightly stale" rather than to "silently wrong". Second, the ladder must never invert under retry pressure. A naive retrying producer amplifies its own 503s into more load; the gate therefore includes a jittered, per-producer backoff hint in every rejection, and producers that ignore the hint are rate-limited harder per the enforcement note in the producer guide. During the 2026-06-11 rehearsal, a deliberately misbehaving producer without backoff was contained to 3% of gate capacity; the same producer with the hint honored cost 0.2%.

## 12. Failure modes and recovery

Every failure mode below has a drill in the operations calendar and a measured number from the most recent drill. A failure mode without a drill date is treated as a design gap, not as an operational unknown.

### 12.1 Node loss

Losing a writer node triggers partition adoption: the survivor takes over the lost partitions at last-acknowledged offset, replays the unsealed tail, and continues. Measured 84 seconds in the 2026-05-21 drill, with board-visible staleness of at most 110 seconds and zero acknowledged-sample loss. Losing an intake gate node is invisible beyond a load-balancer blip. Losing the primary storage node promotes the secondary; the promotion drill of 2026-04-16 measured 6 minutes 40 seconds to full queryability, within the four-hour objective by a factor of thirty-six.

### 12.2 Bus backlog growth

Backlog growth means producers outpace writers. The dashboard to watch is per-partition lag age, not lag depth: depth is a function of sample rate, but age is a function of time-to-durability. At 10 minutes of lag age, the data tier pages itself; at 30 minutes, producers are asked (via the gate) to slow to 50%; at 60 minutes, replay-critical and heartbeat traffic shed automatically. The 72-hour retention is the wall behind all of this — past it, un-replayed samples are gone, which is why the alarm ladder starts at 10 minutes and not at a number that feels comfortable.

### 12.3 Replay and idempotency

Replay is a first-class operation, not an emergency measure: the drift checker's repair job, the historical importer, and post-incident backfills all use the same path. A replayed stretch of history converges to the identical state as first-ingest because writers deduplicate on (series, source timestamp) within the chunk bloom and the manifest, and because sealed chunks are immutable — a replayed sample either lands in an open chunk or triggers a chunk rewrite through the normal repair machinery. Replay throughput is deliberately capped at 2x steady-state write throughput so a replay can never become the next incident; the cap is visible in the admin queue and the remaining replay time is shown on the requesting board.

## 13. Observability

The pipeline's own metrics are exposed on the same boards as customer metrics, in a dedicated ops board that on-call keeps open during rotations. If a pipeline number is not on that board, it does not exist; the rule has killed every attempt to add private diagnostics.

### 13.1 Pipeline-internal metrics

Gate publish latency (p50/p99), per-partition lag age, writer open-buffer depth, flush size histogram, seal duration, compaction generation age, floor rejection rate, cardinality sketch per top-20 metrics, and replay queue depth. Each metric has a stated owner (Rafa for all of them, currently) and a stated alarm threshold tied to the sections above rather than to round numbers.

### 13.2 What pages and what does not

Paging: lag age past 10 minutes, shedding engaged at all, seal failure of any kind, floor rejection rate tripling hour-over-hour. Not paging: single-chunk read errors (manifest fallback handles them), generation age under the nightly compaction window, cardinality sketches approaching but not crossing budget. The distinction is written down because the 2026-02 alarm audit found three thresholds that paged on interesting-but-handled conditions, training on-call to ignore the channel — the exact failure mode the collapse rule fixed for customers.

## 14. Capacity model

Capacity is computed, not felt. The model below reproduces every number quoted in the planning meetings from four inputs, and it has matched measured reality within 8% across the last three rehearsals.

### 14.1 Constants

Steady-state input at beta-plus shape: 2,400 samples per second, mean 180 bytes on the wire. Bus expansion factor 1.35x. Write amplification 2.6x raw (columnar, rev 2 grain plan). Compaction reclaims 11% per night at current churn. Active series per node cap: 12,000. Replay cap: 2x steady state. All constants are re-measured each rehearsal; the last full re-measure is 2026-06-22.

### 14.2 Worked example

The November scale test plans 8,000 samples per second sustained with a 30-minute burst at 40,000. Sustained: bus load 8,000 × 1.35 = 10,800 messages-equivalent, comfortably inside partition headroom; write path 8,000 × 180 bytes × 2.6 ≈ 3.7 MB/s durable, under a third of the measured seal ceiling. Burst: queue depth at 40x steady state drives `chunk_target` to its 64 MiB ceiling within two flush cycles, open-buffer age never breaches 750 ms, and the 80% watermark is touched but not crossed on two of ten partitions. Conclusion recorded 2026-06-24: the test passes on current hardware with one node of margin; the second writer node approved on 2026-08-19 converts that margin into two.

## 15. Rollout plan for rev 3

Phase 1 (this quarter): lock-free compaction on secondary generations, live behind a flag, with the replay estate running mirrored traffic for two weeks before promotion. Phase 2 (next quarter): primary lock removal, gated on phase 1 holding for a full lunar month of compaction cycles. Phase 3: floor cache refresh decoupled from deploys. Each phase lands with its own drill slot in the operations calendar; no phase ships inside the two weeks before a scheduled design-partner review, per an agreement made after the March accent regression taught everyone what a Monday-morning surprise costs.

## 16. Open questions

Cross-region ingest: the bus is single-region by design; a second region needs either a bus topology change or a store-and-forward gate, and neither is designed. Series renames: identity is immutable, so a renamed metric is a new series, and lifetime tooling for that migration does not exist yet. Compaction phase 2 scheduling interacts with the horizon floor's first move in early November; the interaction is believed benign and is unproven. A fourth question was added at Rafa's request on 2026-07-08: whether the coalescer should merge across receipt-time boundaries during replay bursts, which would cut duplicate writes by an estimated 9% at the cost of weakening the receipt-timestamp guarantee that the drift checker's repair job currently relies on. No position yet; the early-November scale test will say whether the 9% matters.

## 17. Appendix — term index

Active series: a series with at least one sample in the last 24 hours. Chunk: the unit of durable storage, per series per day, sealed at 32 MiB. Generation: a rewrite epoch of the chunk set, the unit of compaction and of manifest fallback. Floor: the earliest instant the intake gate accepts. Receipt id: the acknowledgment handed to producers at the gate. Seal: the two-phase act of making a chunk durable and then visible. Watermark: a fraction of a buffer at which defined behavior changes; the two that matter are 80% and 95%.
