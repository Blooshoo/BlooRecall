# Red-team review of the bench study (2026-10-03)

Adversarial review of `bench/REPORT.md` and its artifacts at commit `409c20a`
(test results committed at `d5009b1`, freeze at `84a7c22`). All numbers below
were recomputed from `bench/results/*.json`, `bench/queries.jsonl`, and
independent re-runs of the grep baseline over `bench/corpus/`; no study file
was modified.

> Process note: HEAD moved from `d5009b1` to `409c20a` **while this review was
> in progress** (commit "sharpen claims per adversarial review"). The diff
> touches only `bench/REPORT.md` and prose in `bench/report.py` (verified line
> by line: no metric computation changed), which the study rules allow. Its
> changes reduce overclaiming; the verdicts below apply to the post-`409c20a`
> state.

## 1. Test-set tuning — PASS

`git diff --name-only 84a7c22 d5009b1` contains only `bench/REPORT.md`,
`bench/report.py`, `bench/chart.py`, `bench/results/*`, and `docs/*.svg` — no
ranking-relevant file (`bloorecall/`, `bench/config.bench.json`,
`bench/systems.py`, `bench/grep_baseline.py`) changed between query freeze and
test run; the last changes to all of those predate the queries themselves
(`3ddc7f6`/`e544a99`). Every results file (dev and test) records
`git_commit = 84a7c22…`, so dev and test ran on identical code, and the bench
hybrid policy equals the shipped `baseline-v0` defaults in
`bloorecall/config.py` (0.55/0.05/0.15, rerank 20). The dev split shows the same
ordering as test (dense 0.818 > ablations > hybrid 0.727 > grep 0.576 at
Recall@5), i.e. the headline replicates out-of-sample; git cannot of course
rule out uncommitted local experiments, but nothing in the record suggests any.

## 2. Numbers match — PASS

Recomputed from the committed JSONs: hybrid test Recall@5 0.873, CI
[0.7937, 0.9524]; grep test MRR@10 0.5827; dense Recall@5 0.9524, CI
[0.8889, 1.0000]; all 28 per-category Recall@5 cells (max abs diff 2e-5);
and all 12 paired deltas including CI, wins/losses/ties (e.g. hybrid−grep
recall@5 +0.1429 [+0.0317, +0.2540], 12/3/48 — matches the report exactly).
Overall metrics in all 16 result files equal mean(per_query) to 4-dp rounding
and the bootstrap CIs regenerate bit-exactly with the committed seed. Stronger
still: an independent re-implementation of the declared grep spec over
`bench/corpus/` reproduces **every** per-query metric in `grep.test.json` and
`filename.test.json` for all 63 test queries (committed values are 4-dp
rounded) — the whole chain labels→corpus→implementation→results is consistent.

## 3. Strawman grep — PASS (with one wording concern)

`bench/grep_baseline.py` implements exactly the declared spec (distinct
non-stopword terms matched, then union matching lines, then path), and its
committed results are reproducible from that spec (check 2). The stopword list
is function words only — no domain term is gutted (`current`, `retry`,
`alert`, `kimchi`, `days` all survive); dropping `now/not/never` is standard
and harmless here. I re-ranked the test split with strengthened variants:
total-occurrence tiebreak Recall@5 0.730→0.762; per-term line counts
(`rg -c` per term, summed) 0.730→0.762; light suffix stemming 0.730→0.762
(MRR 0.571–0.600 vs 0.583). All remain ~0.11 below hybrid at Recall@5 (paired
−0.111, CI [−0.222, 0.000]) and ~0.17 below on MRR@10 (0.771), while pure-TF
ranking (occurrences primary) collapses to 0.587 — the spec's
distinct-terms-first key is the right call, not a handicap. Verdict survives.
**Concern:** the grep-vs-hybrid Recall@5 margin is spec-relative (a mild
strengthening already cuts +0.143 to ~+0.11 and the paired CI grazes zero);
the report's framing "frozen one-pass baseline" (threat 4) discloses this, and
MRR/nDCG carry the claim, but any README quoting should prefer the MRR delta.

## 4. Label leakage — PASS

Recomputed the auditor's overlap statistic under my own stopword
approximation: paraphrase 2.14→1.64, vague-recall 3.93→1.93, recency
3.15→2.46 (auditor: 2.29→1.71, 4.00→2.07, 3.15→2.46) — same direction, similar
magnitude, and my top-5 leakiest-after list is exactly theirs
(q-003/q-072/q-073/q-074/q-081, all shared words being the queried concept or
requested dimension). Reading 10 test paraphrase/vague-recall queries myself
(q-001, q-003, q-005, q-008, q-011, q-083, q-084, q-087, q-088, q-095):
post-rewrite queries share only subject/symptom vocabulary with targets —
e.g. q-087 "fruit brew bottle that blew its top" → `pomegranate-incident.md`
and q-088 "brick-heavy blond doorstop… December cold snap" → `batch-S-014.md`
share zero diagnostic words. No wording gives away the answer beyond the
queried concept.

## 5. Cherry-picking — PASS

Test-split category counts are 8/9/10/8/9/9/10 (paraphrase/exact-identifier/
heading-context/deep-in-long-doc/disambiguation/recency/vague-recall) —
roughly balanced, and assignment is sha256-derived, not hand-picked (check 6).
vague-recall is inherently the embedder-friendly category, and its 13 tagged
targets do carry nickname-bearing filenames (`the-great-koji-flood.md`,
`purple-dashboard.md`, …), which feeds BlooRecall's path-metadata feature; but
grep still scores 0.600 there (vs dense 1.000, hybrid 0.800), so the win is
semantic, not a filename artifact, and the report shows grep winning two other
categories prominently. The recency grading of every superseded twin at
grade 1 flatters all systems equally at Recall@5 and is disclosed (AUDIT-NOTES
concern 4), and the `hybrid-norecency` ablation shows the engineered mtimes
contribute nothing to hybrid (norecency 0.905 ≥ hybrid 0.873).

## 6. Split integrity — PASS

Recomputed `int(sha256(id)) % 10 < 3` for all 96 ids: all 96 `split` values in
`queries.jsonl` match (0 mismatches), 33 dev / 63 test as claimed. Ids are
unique, so dev/test overlap is impossible by construction, and per-split
category counts are sane (dev 4–6 per category, test 8–10).

## 7. Reproducibility — PASS (two nits)

Every reproduce command resolves: `bench/run.py` has exactly the documented
flags (`--system/--split/--fresh/--top-k`), `python3 -m bench.report` and
`python3 -m bench.manifest apply` exist as invoked, `tests/` contains 65 test
functions (15+22+28 — the "65 tests" claim is correct), and `docs/*.svg` are
committed. Nits: (a) `var/bench/chart-venv/bin/python bench/chart.py`
presupposes a machine-local, **gitignored** venv — a stranger must build it;
the line should say "any Python with matplotlib"; (b) the run needs a local
Ollama with the model pulled (disclosed) and `git_commit` in results pins
`84a7c22`, which a fresh clone at branch tip won't reproduce byte-for-byte for
latency (fine) — metrics are deterministic per the runner contract.

## 8. Latency fairness — PASS

Headline p50/p95 match the JSONs (grep 8.28/11.64→8/12 ms, bm25 1.32/1.43→1/1,
dense 125.59/147.76→126/148, hybrid 125.61/139.2→126/139), and the metric
definitions state explicitly that BlooRecall latency is embed+rank, that bm25
never embeds, and that grep latency is the pure-Python stand-in rather than
the `rg` binary. The table draws no conclusion from latency, and no prose
implies grep is "slower"; if anything the two honest asymmetries (grep-in-Python
overstates grep cost; index lookups aren't comparable to raw scans) are both
disclosed. No misleading implication found.

## Non-checked observations (minor)

- `report.py::example_queries()` takes the first N queries of a category
  regardless of split, so the test-split section "Where hybrid does NOT win"
  cites q-044 and q-029, which are **dev** queries, without saying so. The
  numbers are test numbers; only the example ids are mixed-split.
- The "Proposed README section (NOT applied)" block now lives inside the
  *generated* `REPORT.md` template in `report.py`; it will be regenerated on
  every rerun and is easy to mistake for a result. Consider moving it to a
  scratch file.
- A new commit (`409c20a`) landed mid-review (see process note above) —
  re-freeze discipline: nothing ranking-relevant changed, but result-bearing
  branches shouldn't move while under review.

## Must-fix before publish

None blocking. Recommended before merge (all cosmetic/wording):
1. Fix the chart-venv reproduce line (say "any Python with matplotlib", since
   `var/` is gitignored) — check 7a.
2. Filter "Where hybrid does NOT win" examples to test-split queries, or mark
   dev ids as such — mixed-split examples invite exactly this review's question.
3. When quoting the grep-vs-hybrid result anywhere durable (README), lead with
   the paired MRR@10/nDCG deltas (+0.19/+0.19), which are robust to grep
   strengthening, and keep Recall@5 (+0.14) explicitly tied to the frozen spec.

## Acceptable limitations (already acknowledged in the report)

- Synthetic, single-model-family corpus and queries; one embedding model; one
  machine (threats 1–2).
- 63 test queries; per-category cells ~8–10 with wide CIs; paired deltas are
  the sharper instrument (threat 3), and the `409c20a` wording softening makes
  this explicit.
- The grep baseline is one frozen pass, not a best-effort agent (threat 4);
  my strengthened variants quantify that its Recall@5 margin is spec-relative
  while the MRR margin is not.
- Engineered mtimes make recency solvable from timestamps; `hybrid-norecency`
  is the honesty check and shows the recency feature contributes nothing
  (threat 5).
- Chunk-level ranking with file-level evaluation on both sides (threat 6);
  no weight tuning on dev (threat 7).
