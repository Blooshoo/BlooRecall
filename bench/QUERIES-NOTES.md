# Queries notes

bench/queries.jsonl — 96 queries (q-001 … q-096), `split` left as `pending`.
Validated with python3: every line parses, ids unique and zero-padded
sequential, every relevant path exists on disk, `relevant` equals the
`graded` keys with grade >= 1, grades are only 1 or 2, query length 5–15
words (mean 10.4).

## Per-category counts (target ~14, ±2)

| category | count |
| --- | --- |
| paraphrase | 14 |
| exact-identifier | 14 |
| heading-context | 14 |
| deep-in-long-doc | 13 |
| disambiguation | 14 |
| recency | 13 |
| vague-recall | 14 |

## Per-project counts

Counting each relevant entry (mentions, including grade-1 helpers), and
separately the queries' grade-2 primary answers:

| project | mentions | grade-2 primary answers |
| --- | --- | --- |
| driftline | 37 | 20 |
| ferment | 22 | 13 |
| homelab | 24 | 17 |
| lumen-web | 28 | 16 |
| orbital-lab | 26 | 17 |
| taskherd | 27 | 16 |

Grade distribution: 99 grade-2, 65 grade-1; 50 queries have more than one
relevant doc.

## Notes and doubts

- **q-040** — orbital `render-farm-operations.md` is graded 2 alongside
  `render-farm-topology.md` (the planted heading-context target): both
  fully answer the 83 °C refusal rule, so the heading-context signal is
  diluted for this query.
- **q-060 / q-061** — both docs on the homelab side (and both on the
  orbital side) of the `retry_policy.max_attempts` collision are grade 2;
  each states the values with equal authority. The discriminator in the
  query ("backup rotation" vs "render farm") is what has to do the work.
- **q-082** — five docs state the current 20-second capture window
  (v2 plan grade 2; v1 plan, replay-format, playtest minutes, and the
  architecture doc all grade 1). Deliberately generous.
- **Recency queries omit superseded docs where the old answer is now
  wrong** (coyote v1, ginger-bug v1, kimchi v1, alert-thresholds v1,
  offsite-rotation v1, render-farm-qc v1, offline-conflicts v1): per the
  rules they only keep a grade 1 if they still mostly answer, and none
  do. q-076 keeps adr/0004 at grade 1 because its retirement banner does
  help answer "is the nightly job gone".
- **q-017** — `cold-start.md` at grade 1 mentions ERR_RIDGE_209 and its
  400 ms threshold (partial). **q-014** — `notification-channels.md` at
  grade 1 covers the scheduled quiet-hours window, adjacent to but not
  the same as do-not-disturb. **q-032** — `starter-smell-triage.md` at
  grade 1 mentions layer separation but not the dark-liquid rule.
- **q-083/q-085/q-089/q-090/q-094** — changelogs and adjacent docs carry
  brief corroborating mentions of the named incidents/fixes; graded 1.
- **Collision found but not queried:** `max_inflight_frames` exists in
  both driftline (`reference/config-keys.md`, default 3, pipeline frames)
  and orbital-lab (`docs/pipeline-config-reference.md`, default 512,
  tracker matrix cap) — a third cross-project key collision beyond the
  three documented ones. I avoided it in exact-identifier (q-018 uses
  `input_buffer_depth` instead); it would make a good extra
  disambiguation query later.
- Uniqueness of every exact-identifier target was verified by reading the
  owning doc; `ERR_BRIDGE_LOOP_77` was additionally cross-checked against
  the March incident review (which describes the loop but never names the
  code).
