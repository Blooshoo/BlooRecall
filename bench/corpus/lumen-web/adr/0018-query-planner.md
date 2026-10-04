# ADR 0018 — Cost-based query planner (planner v2)

Date: 2026-06-30. Owner: Rafa Lindqvist. Reviewers: Juno Park, Dot Ferris. Status: accepted, shipping behind the `PLANNER_V2` flag in the 4.3 line.

## Context

Every tile on every board issues a query: a series set, a time range, a grain, and an aggregation. Until now the service tier has resolved those queries with a fixed cascade of rules written in the beta era — try the freshest tier first, fall back to coarser pre-aggregates when the fan-out is too wide, and special-case the handful of patterns that showed up in the first ten design-partner boards. That cascade was never a planner; it was a staircase. It worked because the estate was small and the queries were similar.

Three things changed at once. The columnar store rev 2 added a second pre-aggregate tier (10-second grain, 45-day retention), which doubled the number of legitimate places a query could be answered. Board-level narrowing means one user gesture rewrites the series set of up to 48 tiles at once, so planning cost is now paid in bursts rather than one tile at a time. And the wildcard-heavy estates — the ones that made the fan-out cap necessary in the query cache specification — turned the staircase's "coarsen until it fits" rule into the single largest source of surprising answers, because coarsening changes the numbers a tile shows, and nobody had written down by how much.

The planner rewrite (planner v2) replaces the staircase with a cost-based choice among candidate plans. This record explains the shape of that planner, the constants inside its cost model, and why those constants have the values they have.

A note on timing, because the date of this record relative to the 4.3 cycle matters: the planner was originally scoped for the spring minor, and Dot pulled it from that cycle after the March regression consumed the team's risk budget. The month of slippage turned out to be a gift. The replay estate gained two weeks of mirrored traffic at the new 10-second tier in the meantime, which is exactly the data the cost model's scan constant was measured against. A planner calibrated on guessed constants would have shipped wrong; this one ships with constants whose provenance is a measurement date, and that discipline — no constant without a measurement behind it — is the part of this record most worth copying elsewhere.

## Problem statement

Given a query (series set, range, grain, aggregation) and the current catalog of storage tiers, choose where and how to execute. The choice must be made in milliseconds, must be explainable after the fact (every tile can show "answered from" today, and people click it), and must be stable: the same query issued twice within a staleness window must take the same path, or the board looks haunted.

The staircase fails each requirement differently. It is slow in the burst case because it retries fallback rules per tile with no shared plan. It is unexplainable because its decisions are emergent from rule ordering rather than computed from anything. And it is unstable under concurrency because two identical tiles can land on different rules depending on which cache entries happen to be warm.

Concretely, three failure classes from the 2026-Q2 query review:

1. **Grain whiplash.** A board mixing 10-second and minute tiles would answer sibling tiles from different tiers after narrowing, producing charts that disagreed by up to 12% on the same metric, same range.
2. **The coarsening cliff.** Wildcard series sets between 3,000 and 6,000 series fell into the cap-driven coarsening path even when the raw tier could have served them at minute grain with a scan cost well under budget.
3. **Burst thundering herd.** A narrowing gesture on a 48-tile board planned 48 queries independently; p95 planning time during the burst was 240 ms, which is longer than the narrowing propagation budget of 150 ms from the board interactions specification.

One more class deserves its own paragraph because it never made the formal review but every design partner hit it: the stale-tier answer. The staircase's first rule is "try the freshest tier first", which sounds harmless until a 30-day-range query is answered from raw at a cost nobody sees, the tile renders in two seconds, and the partner concludes the product is slow — when the minute tier could have answered the same query in 90 milliseconds with numbers indistinguishable at that grain. The staircase never chose to be wrong there; it simply had no notion of cost, so it could not trade a little grain for a lot of speed. Any replacement must be able to say no to the freshest data when fresher-than-necessary is the expensive option, and it must be able to justify that choice after the fact in one sentence a product manager can read.

## Constraints

The planner lives inside the service tier, in the same process as the cache. That placement is fixed and not up for debate in this record: it shares the cache's notion of (series set, range, grain), and moving it would break the "answered from" provenance trail. Additional constraints, agreed with Juno and Dot:

- **Planning budget.** 20 ms per query at p99, measured inside the service tier, excluding execution. The burst case gets a shared-plan discount (section on benching, below) but not a shared-budget exemption.
- **No new storage.** The planner may consult existing statistics only: tier catalogs, the cardinality sketches the intake gate already maintains, chunk header bloom statistics, and the manifest. A statistics collector is a follow-up, not a dependency.
- **Determinism within a window.** Identical queries inside one staleness window take identical paths. This is a product requirement, not a preference; the "answered from" popover is load-bearing for trust.
- **Flagged rollout.** `PLANNER_V2` gates the whole thing. The staircase stays shippable until the flag has carried two full digest-Mondays without a planner-attributed incident.

Two constraints were explicitly discussed and explicitly rejected, and the rejection reasoning belongs in the record. A learning-based ranker (train on observed execution times, predict per query) was rejected because our traffic is too bursty and too seasonal for a model to stay calibrated between Monday digests and quarter-end spikes, and because a ranker that cannot show its work fails our own provenance standard. A per-estate configuration surface (let each design partner pin tiers per board) was rejected because it converts a systems decision into a support burden; Dot's support log from the beta era is full of configuration questions that were really prioritization questions, and this team of four cannot afford to hand customers the keys to a cost model. The planner makes one good default decision; escalation hatches exist where they are cheap (the debug view), not as general configuration.

## Options considered

**Option 1 — Tune the staircase.** Keep the rule cascade, patch the three failure classes with special cases (prefer matching grains across sibling tiles, add a raw-tier cost check before coarsening, batch plan requests per gesture). Pros: smallest diff, no new concepts, shippable in a week. Cons: every fix adds a rule and every rule adds an ordering interaction; the Q2 review already found 14 interacting rules, and three of the failure-class patches conflict with existing ones. Special cases are how the staircase got to 14 rules. Rejected as the long-term answer; two of its patches (sibling grain agreement, raw-tier cost check) survive into v2 as heuristics.

**Option 2 — Full optimizer.** A general plan-space search with dynamic programming over join orders, predicate pushdown, and materialization choices, in the tradition of classic database optimizers. Pros: principled, extensible, the "right" answer. Cons: our query shape has no joins in the relational sense and exactly one aggregation shape per tile; the search space is nearly rectangular. The engineering cost was estimated at three engineer-months, and the generality would be paid for and never used. Dot's constraint of two digest-Mondays without incidents would delay the whole 4.3 line for capacity we do not need. Rejected with prejudice; we wrote down why so the next rewrite proposal does not relitigate it.

**Option 3 — Cost-based selection among a small plan set (chosen).** Enumerate a fixed, small set of candidate plan shapes — raw scan, tier-1 (minute) aggregate scan, tier-2 (10-second) aggregate scan, each optionally with a fan-out split — score each with an explicit cost model, pick the minimum, and cache the decision with the query. Pros: the plan set is auditable (it fits on one page), the cost model is four lines of arithmetic whose constants can be measured and re-measured, determinism is trivial (score functions are pure), and the burst case is handled by planning one representative query per (series set, grain) group per gesture. Cons: new plan shapes require code, not configuration; the cost model must be honest about being a model — its errors are bounded but real. Accepted.

## Decision

Planner v2 is option 3. The planner enumerates candidates, scores them, routes to the minimum, records the decision in the cache alongside the result, and exposes the top three candidates with their scores in the "answered from" popover's debug view. The staircase retires when the flag promotes.

The visible behavioral changes, in order of how often design partners will notice them: sibling tiles stop disagreeing about grain (candidate scoring prefers tier agreement within a gesture group); the coarsening cliff disappears (raw minute scans now win whenever the score says so, cap or no cap); and burst planning drops from 48 independent plans to one plan per distinct (series set, grain) pair, usually three to five per board.

What v2 deliberately does not change is equally binding. It does not change the cache's eviction policy, the staleness window, or the fan-out cap's arithmetic — those are other documents' contracts, and a planner that quietly reinterpreted them would be un-bisectable when something regresses. It does not introduce new aggregation semantics: the five shapes that exist are the five it plans for, and a sixth shape begins as a planning error by default until this record gains a section for it. And it does not touch provenance's user-facing wording; "answered from" stays exactly as Juno shipped it, with v2's additions confined to the debug view until design-partner feedback says otherwise. Scope discipline here is what keeps the rollout reversible: if the flag flips off, the estate returns to the staircase with nothing half-migrated except plan ids riding along in cache entries, which the staircase simply ignores.

## Prior art inside the codebase

Nothing here is novel, and the record should say where each piece came from so reviewers can diff against known machinery. The candidate enumeration is the grain-selection rule from the query cache specification, promoted from a fallback into a first-class candidate set. The fan-out split reuses the wildcard partitioning the intake gate's cardinality sketch already computes. The deterministic window is the cache's staleness window, extended by 15 seconds past eviction so a re-planned query during a refresh holds its path. The provenance popover is Juno's existing "answered from" work from the 4.1 era, which was built — deliberately, it turns out — with a debug extension point that v2 now fills.

The one genuinely new object is the cost model, and it is deliberately small enough to print here and argue about in review.

A word on how the model was calibrated, since "where did 4.0 come from" is the first question every reviewer asks. The procedure was: pick the replay estate's mirrored traffic from a representative week, replay it against each tier in isolation, and regress measured execution time against the two quantities the model would use — rows scanned and groups emitted. Both relationships came out comfortably linear within the ranges our boards actually produce, which is what justifies a linear model at all; the residuals concentrated in cold-cache scans and in the split path, and those two findings became, respectively, the accepted tail-error gap and the split multiplier. The calibration script and its raw numbers are checked into the repository next to the planner, so the next re-measurement reproduces the same procedure rather than a folklore version of it.

## The cost model

Every candidate plan scores as a single number in milliseconds-equivalent work. The model is linear in the two quantities that dominate every measurement we have, with a compounding penalty for the one structural feature our queries have — fan-out splits — and one fixed overhead per candidate so that enumeration cost is honestly priced.

`plan_cost = (rows_scanned / 1000) × 4.0 + (groups_emitted / 1000) × 9.0 + 2.5`, with fan-out splits multiplying the whole score by `1.35^split_depth`.

The constants, and where each number comes from:

- **4.0 per thousand rows scanned** — measured sequential scan cost on the columnar store at rev 2 compression, replay estate, 2026-06-12: 3.7 ms per thousand rows at the chunk sizes the estate actually produces; rounded to 4.0 to keep the margin honest rather than optimistic.
- **9.0 per thousand groups emitted** — aggregation and bucket assembly cost per thousand output groups, measured across the five aggregation shapes that exist (sum, min, max, mean, count). The spread across shapes was 8.1 to 9.4; the model takes the high end so mean-heavy tiles are not systematically underestimated.
- **2.5 fixed** — per-candidate enumeration and provenance overhead, measured, and included so the planner does not enumerate candidates it would not actually be willing to pay for.
- **1.35 per split depth** — a fan-out split (serving one tile from multiple sources and stitching) costs a merge pass and a cache split; the multiplier compounds per depth. Depth beyond 2 is forbidden outright — a three-way stitched tile measured 41% slower than the staircase's worst answer for the same query, and nobody could explain it to a design partner, which is disqualifying under our own rules.
- **The routing threshold: 220 ms.** Any candidate scoring above 220 ms is not executed as scored; the planner re-routes to the best pre-aggregate candidate regardless of score, and the tile shows a "degraded plan" note in provenance. The 220 comes from the board interactions budget: narrowing propagation of 150 ms plus one plan of 220 ms plus execution fits inside a 400 ms gesture-to-paint envelope that Juno measured as the perceptibility line on the reference laptop. Above the line, users see the board "think"; below it, they do not.

The constants live in one file, one table, with the measurement date next to each. Re-measurement is a scheduled follow-up per quarter; a constant may not be edited in the same commit as any other change, ever, per the same discipline that keeps the pipeline specification's limits revision-controlled.

## Grain selection under v2

Grain selection stops being a fallback and becomes a scoring contest. The raw tier scores with its row count; tier-1 and tier-2 score with pre-computed group counts from the manifest. A query at minute grain over a 7-day range has, typically, three plausible winners: tier-1 exactly, tier-2 with downsampling (wins when the series count is low, because 4.0-per-thousand row savings beat the 9.0-per-thousand group cost), or raw at minute roll-up (wins when the range is short). The cap from the query cache specification still applies as a hard post-check — the planner may not propose a plan the cache would refuse — but it is no longer the decision-maker; it is the guardrail.

Sibling agreement is enforced as a gesture-group constraint, not a score term: within one narrowing gesture, tiles whose scored best plans disagree on tier are re-scored with a preference for the majority tier of the group, and only if the majority-tier plan exceeds the 220 ms threshold does a tile keep its own best plan. This reproduces the staircase's one good property (visual consistency) while keeping the escape hatch honest.

## Cache interaction

The planner writes its decision into the cache entry: (series set, range, grain) now maps to (result, plan id, candidate scores). A cache hit serves the result and replays the plan id for provenance without re-scoring. A staleness-window refresh re-scores only if the tier catalog version has changed — catalogs bump on compaction promotion and on seal, roughly every 26 hours per series-day in the worst case — so the common refresh path costs microseconds, not milliseconds. Eviction policy is unchanged; plan records evict with their results and are never retained alone.

## Benchmarks

All numbers from the replay estate, mirrored production traffic, week of 2026-06-22, planner v2 behind the flag versus the staircase on alternating hours:

- Planning p50: 3.1 ms v2 versus 11.8 ms staircase. Planning p99 in the burst case: 14 ms per gesture group (three to five plans) versus 240 ms of independent planning. The 150 ms propagation budget now holds with room to spare.
- Grain whiplash incidents: from 31 observed in the review week to zero — sibling disagreement survives only past the 220 ms threshold, which occurred twice, both wildcard boards over 30-day ranges.
- The coarsening cliff: 412 queries in the review week took the cap-driven coarsening path under the staircase; under v2, 368 of them scored raw minute scans as cheaper and were answered from raw, with p95 tile latency for that class dropping from 1.9 s to 780 ms — inside the 700 ms target from adr/0009 within noise.
- Cost model honesty: predicted versus measured execution, tracked per plan id, mean error 7.4%, p95 error 21%, tail dominated by cold cache scans. The 15% accuracy ambition from the capacity goals is met at p50 and missed at the tail; the tail is a known, accepted gap with a follow-up (statistics collector) attached.

## Risks and mitigations

**The model lies after a storage change.** Mitigation: constants are re-measured quarterly and after every store revision; the routing threshold is a circuit breaker in the meantime. **Plan flapping at score ties.** Two candidates within 3% score identically enough to flip under catalog churn; mitigation: sticky ties — the incumbent plan wins ties, so flapping requires the loser to win by more than 3%. **Explainability debt.** The debug view shows scores but the popover shows only "answered from"; mitigation: the degraded-plan note and the debug view ship together, and Juno holds the line that provenance never becomes debug-only. **Flag stickiness.** The staircase must die on a schedule or it will be maintained forever; mitigation: the flag carries a removal date, the first week of December, written here so that future us has to amend a decision record to keep the old code alive.

## Rollout

Flag on in rc builds from 2026-09-22. The first two digest-Mondays of October on staging with mirrored traffic, then production at 25% of estates for one week, then full. The staircase removal lands with the promotion commit; the flag removal date stands regardless. Rollback is a flag flip and is rehearsed in the rc window — planner v2 and the staircase share the cache, so a rollback never invalidates warm entries, it only changes who plans the next one.

## Follow-ups

Statistics collector feeding the model from actual scan telemetry (kills the tail-error gap). Plan ids surfaced on exported board documents, so a design partner can attach "how this was answered" to the numbers they present. Cost model re-measurement calendar entry, quarterly, owner Rafa, first slot mid-December. The wildcard partitioning sketch is reused but not owned here; its 4,000-series budget from the intake gate remains the authority, and this record defers to it.
