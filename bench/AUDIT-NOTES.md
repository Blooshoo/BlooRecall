# Label audit — bench/queries.jsonl (96 queries)

Auditor: independent label audit, 2026-10-03. Every graded doc was read; sibling/twin docs named in
`corpus/MANIFEST.json` were checked as sweep candidates. No ranking system was run; the only tooling
was a python script that reads the already-labeled docs and counts content-word overlap (definition
below). 32 of 96 queries were changed.

## Per-query verdicts

| id | verdict | what changed and why |
|---|---|---|
| q-001 | ok | cold-start g2 verified (lazy-admission p95 tail explains launch hitch); zero overlap. |
| q-002 | ok | fox-sprite-cache g2 verified (oldest-first eviction stalls); overlap 1 ("fox", the feature name). |
| q-003 | ok | milky-brine g2 correct; kimchi-triage g1 kept — it has a "White dust / milky liquid" section pointing at the guide. |
| q-004 | ok | kombucha-no-tingle g2 correct; kombucha-year g1 kept (links the still-bottle forensics). |
| q-005 | both | label: +alert-thresholds-v2 g1 (defines the 80/90 pool line that "turned the board red"). query: rewritten — "board went red" mirrored the doc verbatim. |
| q-006 | ok | wireless-clients-roaming g2 verified (19:00 disassociations, vocab-gap intact). |
| q-007 | ok | ingest-horizon g2 verified (floor 2025-10-06 = "last October"). |
| q-008 | ok | snapshot-pipeline g2 verified (PNG / paginated A4). |
| q-009 | fixed-query | rewritten — "shift … encoders … speed" all appear in exp-029; now only "encoders" (the subject) is shared. |
| q-010 | fixed-label | +occlusion-handling-v2 g1 (current protocol for hidden stretches; complements hold-and-relink g2 and tracker-tuning g1). |
| q-011 | fixed-query | rewritten — the retention spec's principle line is near-verbatim ("how long … before it is unrecoverable"). |
| q-012 | fixed-query | rewritten (twice) — "land", "clock", "region" all appear in reminders-travel; final wording shares only "reminders" + weak words. |
| q-013 | fixed-query | rewritten (twice) — grip/walls/button/ends all appear in wallride.md; final wording shares none of them. |
| q-014 | ok | delivery-surfaces g2 verified (suppressed-alert behavior); notification-channels g1 kept (quiet hours, adjacent). |
| q-015 | ok | ERR_TILE_5042 sole home verified. |
| q-016 | ok | rollup.max_series sole home verified. |
| q-017 | ok | ERR_RIDGE_209 in error-codes g2; cold-start g1 confirmed (cites the watchdog and its 400 ms trigger). |
| q-018 | ok | input_buffer_depth sole home verified. |
| q-019 | ok | .dlcap/DLCAP1 sole home verified. |
| q-020 | ok | ERR_SNAP_SEQ_118 sole home verified. |
| q-021 | ok | cache.serve_stale_ttl sole home verified ("on dill" is answerable context). |
| q-022 | ok | ERR_BRIDGE_LOOP_77 sole home verified. |
| q-023 | ok | dataset id sole home verified. |
| q-024 | ok | ERR_ENCODER_STALL_118 sole home verified. |
| q-025 | ok | ERR_LUT_MISMATCH_31 sole home verified. |
| q-026 | ok | ERR_HERD_512 sole home verified. |
| q-027 | ok | migrateHerdSchema sole home verified. |
| q-028 | ok | macros.md sole home of MACRO-24; query is a description, not the id — acceptable for the category. |
| q-029 | fixed-label | +momentum-tuning-v2 g1 — the current air-steer number (30%) lives there; momentum-model (g2) explicitly defers numbers to the tuning passes. |
| q-030 | ok | perf-push "Memory ceiling > Resident budget" (1.8 GB, cut order) verified. |
| q-031 | ok | checkpoint-audit g2 (measured 840 ms p95 to control-return); policy-v2 g1 kept. |
| q-032 | ok | starter-rescue g2 ("The dark layer of water on top"); smell-triage g1 kept (same root cause, companion triage). |
| q-033 | ok | kimchi-triage headings carry the topic by design (heading-context case). |
| q-034 | fixed-label | +plans/network-segmentation-2026 g1 (cyan alias rules + "from cyan: nothing internal reachable except the board" verification). |
| q-035 | ok | humidity-damp-rack g2 (warn 60 / red 70, March peak 66). |
| q-036 | ok | ups-maintenance g2 (90-second shutdown order); deep-dive g1 kept (same 90-second chain). |
| q-037 | ok | sync meeting g2 (41 mutes); watcher-notification-policy g1 kept (collapse rule born from that mute audit). |
| q-038 | ok | glossary "Rollups" g2; adr 0009-v2 g1 kept. |
| q-039 | ok | dashboard-interactions g2 (cross-filtering narrowing). |
| q-040 | ok | topology + operations g2 (83 °C refuse-new-work ceiling); postmortem g1 (action item). |
| q-041 | ok | framehose g2 (0.90 pinch, GOP shedding). |
| q-042 | ok | glyph-colormap g2 (red-green safety section). |
| q-043 | ok | rendering-pipeline g2 ("Frame budget, measured" ~3050 words deep); perf-push g1. |
| q-044 | fixed-label | +quick-capture-v2 g1 (the 20-second window decision feeding the sizing table; g2 holds the byte numbers). |
| q-045 | ok | kombucha-year "The numbers I brew to" verified (3 L / 150 g / 5 bags / 300 ml / 8 days). |
| q-046 | ok | complete guide g2 (cold-hold + bake-from-cold schedule); country loaf g1 (has the timings too). |
| q-047 | ok | deep dive g2 (storage segment has no default route); vlan-table g1. |
| q-048 | ok | backup-pipeline g2 (fs.flush_aggr_window_ms=450 on bramble, variance win). |
| q-049 | ok | adr 0018 "The cost model" verified. |
| q-050 | ok | ingestion-pipeline 9.2 + backpressure/watermarks verified. |
| q-051 | ok | operations 6.4 "Pinned environment values" verified. |
| q-052 | ok | tracker-architecture 5.2.1 pinned values; tuning notes g1 kept. |
| q-053 | ok | rollback plan section 7 (ladder + drain limits); storm runbook g1 (its own ladder). |
| q-054 | fixed-label | +reminders-review meeting g1 (quota debate; final numbers explicitly deferred to spec §5). |
| q-055 | ok | rollback plan 5.1 automatic triggers verified. |
| q-056 | fixed-label | +driftline reference/glossary g1 (canonical definition plus the explicit "in this codebase it is always the replay thing" disambiguation line). taskherd side correctly excluded. |
| q-057 | ok | gesture spec g2; review meeting g1. driftline side correctly excluded. |
| q-058 | ok | sparkline-component g2; visual-notes g1. driftline shader notes correctly excluded. |
| q-059 | ok | sparkline-trails g2. lumen side correctly excluded. |
| q-060 | ok | both g2 verified: max_attempts=4 / backoff 15 present in offsite-rotation-v2 and backup-pipeline-architecture. |
| q-061 | ok | both g2 verified: render scope, 2 attempts, immediate requeue. render-review meeting (hose numbers) correctly excluded. |
| q-062 | fixed-label | +checkpoint-audit g1 (measured 60–75 s spacing conformance; v2 plan stays g2, v1 stays g1). |
| q-063 | ok | 2026 grid g2; 2025 g1. |
| q-064 | ok | golden-kraut g2 (pantry/ground turmeric, 2%); twin g1 (cross-referenced near-twin). |
| q-065 | ok | mirror of q-064 (fresh rhizome, cheese boards, 2.1%). |
| q-066 | ok | funnel v2 g2 (2 steps); v1 g1; decision meeting g1. |
| q-067 | ok | sync-rate-limits g2 (token bucket); throttle policy g1 (superseded, points forward). |
| q-068 | ok | 2026 plan g2; 2025 plan g1 (superseded banner). |
| q-069 | fixed-label | +pipeline-config-reference g1 (occlusion_bridge.window_frames=45, "matches protocol v2") and +tracker-architecture g1 (ORBITAL_BRIDGE_MAX_GAP=45). v2 g2 / v1 g1 / hold-and-relink g1 confirmed. |
| q-070 | fixed-label | +coyote-time.md g1 (superseded 120 ms answer) — recency grading made consistent with q-078/080/081/082. changelog g1 verified (0.13.0 entry). |
| q-071 | fixed-label | +ginger-bug.md g1 (superseded banner; old every-other-day schedule). |
| q-072 | fixed-label | +kimchi-baechu-v1.md g1 (superseded wet-brine method). |
| q-073 | fixed-label | +alert-thresholds-v1.md g1 ("kept as baseline" banner). pool-capacity g1 verified. |
| q-074 | fixed-label | +offsite-rotation-v1.md g1 (superseded banner; Tuesday vs Wednesday is the recency discriminator). |
| q-075 | fixed-label | +render-farm-qc-v1.md g1 (SUPERSEDED banner; hand-sampling era). |
| q-076 | both | query rewritten — "nightly zip job" was verbatim from both ADRs. grades verified: 0011 g2, 0004 g1 (retired banner), changelog g1. |
| q-077 | both | query rewritten — "edit wins/offline" mirrored v2's resolution rule. +offline-conflicts-v1 g1 (superseded server-wins rule, points to v2). |
| q-078 | ok | tuning v2 g2 (current numbers); v1 g1. |
| q-079 | ok | tumbleweed plan g2; known-issues + rework spec g1s verified. |
| q-080 | ok | alerting v2 g2 (15 s); v1 g1 (60 s). |
| q-081 | fixed-query | query rewritten to avoid the ADRs' own terms ("base grain of the pre-agg store"); grades verified (10 s vs 60 s base tier). |
| q-082 | ok | quick-capture-v2 g2; v1 / replay-format / playtest meeting / architecture g1s all verified. |
| q-083 | ok | fox-sprite-cache g2; changelog g1 (0.12.0 pinning entry). |
| q-084 | both | query rewritten — "hill crests" was verbatim from toboggan-hack.md. glossary + momentum-model g1s kept. |
| q-085 | both | label: CHANGELOG upgraded 1→2 — the 0.16.1 "capture star freeze" entry names the release the query asks for (equally right with the architecture doc); input-latency g1 kept (cites the star freeze). query rewritten ("saving a replay froze" mirrored the docs). |
| q-086 | both | query rewritten (counter/floor/night verbatim); koji-flood log g2 verified. |
| q-087 | both | query rewritten (bottle/sink phrasing mirrored the log); kombucha-year g1 kept (tub-rule origin story). |
| q-088 | both | query rewritten (dense/grey/kitchen verbatim); guide + slow-starter-winter g1s kept (both tell the S-014 story). |
| q-089 | fixed-label | theme-tokens g1 REMOVED — it never mentions the incident, palette, or accent (pure CSS-variable definitions). changelog + sparkline-visual-notes g1s verified (violet accent regression). |
| q-090 | fixed-query | query rewritten — chart/drew/flat/line/zero all appear in the incident report; changelog g1 verified (v3.9.4 entry). |
| q-091 | both | query rewritten (clocks sagged verbatim); postmortem + operations g1s verified. |
| q-092 | both | query rewritten (cron/frames/reel/closed verbatim); framehose + operations g1s verified (digest + lock mentions). |
| q-093 | fixed-query | query rewritten — composer/hop/typing verbatim from the kangaroo plan; known-issues g1 verified. |
| q-094 | ok | sync postmortem g2; storm runbook + rollback plan g1s verified. |
| q-095 | both | query rewritten — 7 words (evaporative/pad/rack/tied/wet/zip/fan) verbatim from the hack note; humidity g1 kept (cross-references it). |
| q-096 | ok | cookie-sheet g2; "attic/rafter" overlap accepted as minimal locating context (see concerns). |

## Leakage check

Definition: content words = lowercased alphabetic tokens, length >= 3, minus a fixed stopword list
(~180 words: pronouns, auxiliaries, question words, prepositions, and high-frequency filler such as
get/got/also/back/still/one/two/new/old/like/use). Overlap = |query content words ∩ grade-2 doc
content words|, maximised over the doc's grade-2 docs. A query is flagged at 3+ shared words that are
distinctive, i.e. not the queried concept/identifier itself (e.g. "ginger bug", "coyote time",
"baechu kimchi", "alert thresholds", "cookie sheet", "koji", "purple", "capture", "replay") and not
unavoidable symptom/dimension glue. 21 queries in the three leak-sensitive categories were flagged;
17 were rewritten (one of them twice), 4 were accepted as irreducible (see concerns).

| category | n | mean overlap BEFORE | mean overlap AFTER |
|---|---|---|---|
| paraphrase | 14 | 2.29 | 1.71 |
| vague-recall | 14 | 4.00 | 2.07 |
| recency | 13 | 3.15 | 2.46 |

Top-5 leakiest queries AFTER fixes (all remaining overlap is queried-concept or symptom vocabulary,
not leaked phrasing):

| id | category | shared words with grade-2 doc | why accepted |
|---|---|---|---|
| q-003 | paraphrase | day, fine, kraut, white | kraut = subject, white = the symptom asked about; day/fine are glue |
| q-072 | recency | baechu, days, kimchi, salt | dish name + the requested quantities (salt, days) |
| q-073 | recency | alert, days, storage, thresholds | "storage alert thresholds" is the queried concept itself |
| q-074 | recency | day, offsite, rotation, run | "offsite rotation" is the queried concept; day/run are the dimension asked |
| q-081 | recency | base, grain, pre, store | the queried concept; both v1/v2 share these terms equally, so version discrimination (the point of the category) is unaffected |

## Tally

- Queries modified: 32 of 96 (17 query rewrites, one of them q-085 which also got a label change; plus second-round refinements to q-012, q-013, q-088, q-091).
- Labels added: 17 (all grade 1): q-005, q-010, q-029, q-034, q-044, q-054, q-056, q-062, q-069 (x2), q-070, q-071, q-072, q-073, q-074, q-075, q-077.
- Labels changed: 1 upgrade (q-085 CHANGELOG 1→2).
- Labels removed: 1 (q-089 theme-tokens g1).
- Grade-2 downgrades: 0 — every grade-2 doc survived reading.
- Ids, order, categories and `"split": "pending"` unchanged; `relevant` mirrors the graded keys as before.

## Remaining concerns

1. Irreducible overlap: q-003, q-072, q-073, q-074, q-081, q-085 ("capture" = the feature's name), q-096
   ("attic/rafter" locating context) still sit at raw overlap 3-4. Nothing distinctive is leaked; removing
   the rest would make the queries unanswerable. Flagged so nobody "fixes" them blindly later.
2. q-029 subtlety: momentum-model's Air control section says 35% (0.9.0 baseline) while momentum-tuning-v2
   owns the current 30%. The heading-context grade-2 is still the right primary (the spec defers numbers to
   plans), but scorers should know the truly current number is in the added g1.
3. Corpus inconsistency (not a label bug): humidity-damp-rack points at alert-thresholds-v2 for the humidity
   gauge thresholds, but alert-thresholds-v2 contains no humidity row. q-035 is unaffected; a sharp retriever
   may dangle on the pointer.
4. Recency grading is now uniform: every superseded v1 twin is graded 1 (previously 7 recency queries graded
   the twin and 6 did not). Consumers should expect deliberate partial credit for stale docs on recency queries.
5. driftline/plans/quick-capture-v1 carries no in-file superseded banner (unlike most v1 twins); systems
   relying on in-doc banners will only disambiguate it via the v2 plan or the architecture doc.
6. cron-schedule.md constrains when the offsite rotation may run but never states the day; deliberately NOT
   graded on q-074 (the day lives only in offsite-rotation-v2/v1).
7. q-028 is categorised exact-identifier but the query text contains no identifier ("which macro do I use for
   a sync backlog complaint"). It is answerable and MACRO-24 is unique to macros.md, but the category label is
   loose; left as-is since rewriting categories was out of scope.
