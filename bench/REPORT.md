# BlooRecall retrieval benchmark

Honest answer to "is BlooRecall actually better than what a coding agent does by
default, and where?" — with the places it loses included.

**One-sentence result:** Dense-only beats the shipped hybrid on MRR@10 (paired -0.086, 95% CI [-0.166, -0.013]); at Recall@5 the point estimate also favors dense (0.952 vs 0.873) but the paired CI grazes zero. Hybrid clearly beats the frozen one-pass grep baseline on this corpus (paired +0.14 Recall@5, +0.19 MRR@10), while grep is higher on heading-context in this sample — the per-category table and paired deltas say where.

## Setup

- **Corpus:** 251 synthetic Markdown files across 6 fictional
  projects (a game, a home-lab, a web analytics app, a research lab, a
  fermentation wiki, a mobile app). Written to feel like real dev notes:
  specs, runbooks, ADRs, meeting notes, changelogs; 3-line stickies up to
  ~4700-word deep-heading docs. Deliberately planted: vocabulary-gap docs
  (query words absent from the doc), doc-unique identifiers, answers whose
  topic words live only in section headings, v1/v2 near-duplicate plans,
  superseded decisions (older file times applied from `MANIFEST.json`),
  long docs with the answer buried 2000+ words deep, and three cross-project
  name collisions ("Quick Capture", "sparkline", `retry_policy.max_attempts`).
  No real people, companies, or credentials.
- **Queries:** 63 test / 33 dev (96 total),
  7 categories, labeled with graded relevance (2 = clear answer, 1 =
  partial). Written by an agent that read only the corpus and never ran a
  search system; a separate auditor agent then re-verified every label,
  added equally-right docs, and rewrote queries that leaked doc wording
  (see `AUDIT-NOTES.md` for before/after leakage numbers).
- **Split discipline:** dev/test ≈ 30/70 assigned deterministically from
  `sha256(query id)`. All design decisions were made on dev or on the corpus
  itself before any test run; the test split ran once per system, frozen, at
  commit `84a7c22c5058`.
- **Model/hardware:** qwen3-embedding:0.6b (Ollama, 1024-dim); Intel(R) Core(TM) i7-14700K, Linux-7.0.0-30-generic-x86_64-with-glibc2.39.
  Index build: main (heading-aware) 30.266s, plain-chunker ablation 22.064s
  for 251 files. Query latency is single-process, warm
  Ollama (`keep_alive`), one warmup query excluded.
- **Metric definitions:** recall@k = a relevant doc (grade ≥ 1) in the top k;
  MRR@10 = 1/rank of the first relevant doc; nDCG@10 uses graded gains
  2^rel−1. CIs are percentile bootstrap over queries (1000 resamples,
  seeded). Latency for BlooRecall variants is embed + rank; `bm25` never
  embeds. Grep latency is our Python implementation, not the `rg` binary.
- **Reproduce:**
  ```bash
  git checkout bench-study
  python3 -m bench.manifest apply                      # set file times from MANIFEST.json
  python3 -m unittest discover -s tests                # 65 tests, no network needed
  python3 -m bench.run --system all --split dev --fresh
  python3 -m bench.run --system all --split test --fresh
  python3 -m bench.report                              # regenerate this file from results/
  python3 -m venv var/bench/chart-venv                 # one-time, for the charts:
  var/bench/chart-venv/bin/pip install matplotlib
  var/bench/chart-venv/bin/python bench/chart.py       # regenerate docs/*.svg
  ```
  (needs a local Ollama with `qwen3-embedding:0.6b` pulled; the corpus lives in
  `bench/corpus/` — the harness mirrors it to a fixed temp dir because
  BlooRecall refuses to index its own project directory.)

## Headline (test split)

| system | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | 95% CI on Recall@5 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| grep | 0.460 | 0.730 | 0.841 | 0.583 | 0.540 | [0.619, 0.841] | 8 | 12 |
| filename | 0.397 | 0.651 | 0.698 | 0.505 | 0.459 | [0.540, 0.778] | 0 | 0 |
| bm25 | 0.603 | 0.825 | 0.921 | 0.692 | 0.651 | [0.730, 0.905] | 1 | 1 |
| dense | 0.794 | 0.952 | 0.952 | 0.858 | 0.790 | [0.889, 1.000] | 126 | 148 |
| hybrid | 0.698 | 0.873 | 0.968 | 0.771 | 0.729 | [0.794, 0.952] | 126 | 139 |
| hybrid-noheadings | 0.603 | 0.905 | 0.936 | 0.714 | 0.687 | [0.825, 0.968] | 124 | 139 |
| hybrid-norerank | 0.714 | 0.889 | 0.952 | 0.784 | 0.740 | [0.809, 0.952] | 125 | 142 |
| hybrid-norecency | 0.698 | 0.905 | 0.952 | 0.770 | 0.729 | [0.825, 0.968] | 128 | 141 |

Read with the paired deltas — overlapping CIs are easy to misread:


### Paired deltas (same queries, per-query differences)

- **hybrid − grep, recall@5: +0.143** (95% CI [+0.032, +0.254]; hybrid better on 12 queries, grep better on 3, 48 ties)
- **hybrid − bm25, recall@5: +0.048** (95% CI [-0.016, +0.127]; hybrid better on 4 queries, bm25 better on 1, 58 ties)
- **hybrid − dense, recall@5: -0.079** (95% CI [-0.159, +0.000]; hybrid better on 1 queries, dense better on 6, 56 ties)
- **hybrid − hybrid-noheadings, recall@5: -0.032** (95% CI [-0.095, +0.032]; hybrid better on 1 queries, hybrid-noheadings better on 3, 59 ties)
- **hybrid − grep, mrr@10: +0.189** (95% CI [+0.104, +0.277]; hybrid better on 27 queries, grep better on 6, 30 ties)
- **hybrid − bm25, mrr@10: +0.079** (95% CI [+0.035, +0.133]; hybrid better on 17 queries, bm25 better on 1, 45 ties)
- **hybrid − dense, mrr@10: -0.086** (95% CI [-0.166, -0.013]; hybrid better on 3 queries, dense better on 17, 43 ties)
- **hybrid − hybrid-noheadings, mrr@10: +0.057** (95% CI [+0.003, +0.121]; hybrid better on 14 queries, hybrid-noheadings better on 8, 41 ties)
- **hybrid − grep, ndcg@10: +0.188** (95% CI [+0.119, +0.260]; hybrid better on 35 queries, grep better on 10, 18 ties)
- **hybrid − bm25, ndcg@10: +0.077** (95% CI [+0.045, +0.114]; hybrid better on 27 queries, bm25 better on 0, 36 ties)
- **hybrid − dense, ndcg@10: -0.062** (95% CI [-0.118, -0.003]; hybrid better on 12 queries, dense better on 24, 27 ties)
- **hybrid − hybrid-noheadings, ndcg@10: +0.041** (95% CI [+0.001, +0.091]; hybrid better on 20 queries, hybrid-noheadings better on 16, 27 ties)

## Per-category (test split, Recall@5)

Recall@5 per category (test split):

| category | grep | filename | bm25 | dense | hybrid | hybrid-noheadings | hybrid-norerank | hybrid-norecency |
|---|---|---|---|---|---|---|---|---|
| deep-in-long-doc (one fact buried 2000+ words into a 3000+ word doc) | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| disambiguation (similarly named things across projects or versions, query carries the discriminator) | 0.889 | 0.889 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| exact-identifier (query names an error code / config key / function that is unique to one doc) | 0.889 | 0.222 | 1.000 | 0.889 | 1.000 | 1.000 | 1.000 | 1.000 |
| heading-context (answer paragraph's topic words live only in its section headings) | 0.800 | 0.600 | 0.800 | 0.900 | 0.700 | 0.800 | 0.700 | 0.700 |
| paraphrase (query avoids the doc's wording (vocabulary gaps)) | 0.125 | 0.500 | 0.500 | 0.875 | 0.750 | 0.750 | 0.875 | 0.750 |
| recency (asked for the CURRENT decision; an older doc was superseded (backdated mtime)) | 0.778 | 0.889 | 0.889 | 1.000 | 0.889 | 0.889 | 1.000 | 1.000 |
| vague-recall (asked from memory, by nickname or episode) | 0.600 | 0.700 | 0.600 | 1.000 | 0.800 | 0.900 | 0.700 | 0.900 |

## Where hybrid does NOT win

See the per-category table above: the categories where `grep` matches or
beats `hybrid` get named here with example queries (filled from the actual
run below), and the paired-delta lines above quantify how often each system
wins per query.

Categories where **grep ≥ hybrid** on Recall@5 (point estimates; small n per cell):
- `deep-in-long-doc`: grep 1.000 vs hybrid 1.000. Example queries:
    - (q-043) "what's the measured per-stage frame budget on the heaviest scene and how much headroom remains"
    - (q-045) "exact numbers for a three-litre kombucha batch: water, sugar, tea bags, starter, days"
    - (q-047) "which network segment has no route to the internet and why"
- `heading-context`: grep 0.800 vs hybrid 0.700. Example queries:
    - (q-030) "what's the resident RAM budget for the demo route and what gets cut first"
    - (q-031) "how long until you get control back after dying at a kiln checkpoint"
    - (q-032) "dark liquid pooled on top of my starter — is the jar done for"

Categories where **dense-only > shipped hybrid** on Recall@5 (the blend gives back embeddings' gains):
- `heading-context`: dense 0.900 vs hybrid 0.700. Example queries:
    - (q-030) "what's the resident RAM budget for the demo route and what gets cut first"
    - (q-031) "how long until you get control back after dying at a kiln checkpoint"
- `paraphrase`: dense 0.875 vs hybrid 0.750. Example queries:
    - (q-001) "why does the game seize up for a few seconds right when you launch it"
    - (q-003) "kraut brine went opaque white by day three, is that fine"
- `recency`: dense 1.000 vs hybrid 0.889. Example queries:
    - (q-070) "how long is coyote time these days"
    - (q-071) "what's the ginger bug feeding routine we settled on"
- `vague-recall`: dense 1.000 vs hybrid 0.800. Example queries:
    - (q-083) "whatever came of that fox sprite cache thing"
    - (q-084) "what was that sled workaround for the steep downhill sections?"

Hybrid's clearest win: `paraphrase` (hybrid 0.750 vs grep 0.125).

## Ablations (what each piece buys)

- **no headings** (`hybrid-noheadings` vs `hybrid`): the value of heading
  breadcrumbs, isolated. Chunk geometry also changes (plain chunks are
  larger), so this is the chunker as a whole, not just the breadcrumb line.
- **no re-rank** (`hybrid-norerank`): the term-coverage bonus over the top 20.
- **no recency** (`hybrid-norecency`): how much the mtime feature contributes
  (it should be small; the corpus times are engineered, so this ablation is
  the honesty check on the `recency` category).
- **dense vs bm25 vs hybrid**: the blend against its own ingredients.

Ablation wording discipline: with ~9-10 queries per category and Recall@5
moving in steps of ~0.1, the ablations support "higher observed Recall@5"
claims, not causal "this component costs X". The paired MRR@10 deltas are
the sharper instrument (e.g. heading breadcrumbs **help** MRR@10: hybrid −
noheadings +0.057, CI [+0.003, +0.121], while noheadings shows higher
observed Recall@5).

## Dev split (reported separately, not the headline)

| system | Recall@1 | Recall@5 | MRR@10 | nDCG@10 |
|---|---|---|---|---|
| grep | 0.364 | 0.576 | 0.447 | 0.438 |
| filename | 0.182 | 0.364 | 0.266 | 0.273 |
| bm25 | 0.515 | 0.667 | 0.599 | 0.577 |
| dense | 0.727 | 0.818 | 0.770 | 0.751 |
| hybrid | 0.576 | 0.727 | 0.655 | 0.635 |
| hybrid-noheadings | 0.576 | 0.758 | 0.645 | 0.620 |
| hybrid-norerank | 0.576 | 0.788 | 0.667 | 0.650 |
| hybrid-norecency | 0.606 | 0.758 | 0.676 | 0.648 |

## Threats to validity

1. **Everything synthetic and LLM-written.** Corpus, queries, and labels come
   from the same model family (not the same instance or prompt, and the
   query writer never saw a ranking). Real notes are messier; identifiers
   here are cleaner than real ones. The auditor's word-overlap audit
   (`AUDIT-NOTES.md`) quantifies but cannot eliminate template leakage.
2. **One embedding model, one language, one machine.** qwen3-embedding:0.6b
   at 1024 dims; a stronger embedder could shift dense/hybrid numbers.
3. **Small test set.** 63 test queries; per-category cells are ~8-10
   queries, so per-category CIs are wide (shown in the results JSON). The
   paired deltas are the sharper instrument.
4. **The grep baseline is a fixed, declared spec** (distinct terms matched,
   then line hits) — the study prompt froze it before any run. It does not
   do morphology, quoted phrases, multi-pass refinement, or reading hits
   before judging relevance, which a real agent might do. Treat it as "one
   rg pass", not "the best possible agent effort". The `filename` variant
   brackets one trivial refinement. The red-team check (`REDTEAM.md`) also
   ran a strengthened grep (per-term `rg -c`-style occurrence counting /
   occurrence tie-break): its Recall@5 rises 0.730 → ~0.762, which narrows
   the hybrid−grep Recall@5 margin to ~+0.11 with the paired CI grazing
   zero. **The durable comparison is the paired MRR@10 / nDCG@10 delta
   (+0.19 / +0.19), which the strengthened variants do not threaten.**
5. **Corpus-engineered mtimes** make the `recency` category solvable from
   timestamps alone; `hybrid-norecency` quantifies how much that feature
   actually contributes (small), and grep ignores mtimes entirely.
6. **Chunk-level index, file-level evaluation** on both sides: BlooRecall
   ranks its best chunk per file (shipped behavior); grep ranks files.
7. **No tuning at all** — shipped weights are used as-is. That is the honest
   "as shipped" question, but it means no one optimized BlooRecall for this
   corpus, and the dev split was used only for sanity checks, not weight
   search.

## Proposed README section (NOT applied — for the owner to review)

```markdown
## Benchmark

Against a frozen one-pass grep baseline (what an agent gets from one `rg`
pass) on a 251-file synthetic corpus, shipped BlooRecall reaches Recall@5
0.87 vs grep's 0.73 (MRR@10 0.77 vs 0.58); dense-only retrieval scores
0.95/0.86, and grep is higher on heading-only queries (0.80 vs 0.70).
Synthetic corpus and queries, single 0.6b embedding model, 63 test
queries — treat the deltas, not the absolutes.
![Recall@5 by system](docs/benchmark.svg)
```

## Reproduction artifacts

- `bench/results/<system>.<split>.json` — one file per system per split
  (headline metrics, per-category, per-query rows, latency, environment).
- `bench/queries.jsonl` + `bench/QUERIES-NOTES.md` + `bench/AUDIT-NOTES.md`.
- `bench/REDTEAM.md` — the independent red-team review (8 checks, all pass;
  includes the strengthened-grep probe).
- `bench/corpus/MANIFEST.json` — per-file project, intended mtime, planted
  cases; `python3 -m bench.manifest apply` restores the engineered times.
