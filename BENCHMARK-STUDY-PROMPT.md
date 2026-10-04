# Task: an honest, reproducible retrieval benchmark for FileBrain

You're working in this repo (FileBrain: local hybrid file search, BM25 + Ollama dense embeddings +
heading-aware Markdown chunks + a coverage re-rank, exposed as a CLI and an MCP tool). Read
`README.md`, `filebrain/search.py`, `filebrain/corpus.py` and `filebrain/indexer.py` first.

**Goal:** answer "is FileBrain actually better than what coding agents do by default, and where?"
with numbers anyone can reproduce, plus one chart for the README. This will be published, so
**honesty beats a flattering result.** If hybrid loses somewhere, the report says so.

Use subagents generously and run independent work in parallel. Suggested roles are below.

## Hard rules

1. **Never touch the owner's live setup.** Don't edit or read `config.json` and don't write to
   `var/index.sqlite3`. All benchmark work uses its own config (`bench/config.bench.json`) and
   index (`var/bench/...`).
2. **Never read the owner's real notes.** The benchmark corpus is synthetic and lives in the
   repo. Nothing from outside `bench/` goes into it.
3. **No tuning on the test set.** Split queries into `dev` and `test` (about 30/70). Any weight or
   setting change is decided on dev only. Freeze the settings, record the commit hash, then run
   test once. Report test numbers as the headline.
4. Don't change default ranking behavior to win the benchmark. New code goes in a benchmark
   module, plus small, opt-in switches where an ablation needs one.
5. Work on a new git branch `bench-study`. Commit as you go. **Don't push or publish anything.**
6. Existing tests (`python3 -m unittest discover -s tests`) must still pass. Add tests for new
   code.

## 1. Corpus (subagents in parallel, one per "project")

Build `bench/corpus/`: about 200–300 Markdown/text files spread across 5–6 made-up projects (for
example a game, a home-lab runbook set, a web app, a research notebook, a recipe/hobby wiki, a
mobile app). They should feel like real dev notes: specs, plans, handoffs, READMEs, meeting notes,
runbooks and changelogs, with mixed lengths (some 3 lines, some 5k+ words with deep headings).
**No real people, companies, credentials or security/exploit content.**

Deliberately plant the cases that separate retrieval methods:
- **Vocabulary gaps**: the doc says "exponential backoff on reconnect", the query will say "how do
  we retry a dropped socket".
- **Exact identifiers**: error codes, config keys, function names, version strings (`ERR_QUOTA_429`,
  `max_inflight_frames`). Keyword search should win these.
- **Answer lives under a heading**: a short paragraph whose topic words appear only in its section
  headings (this tests heading breadcrumbs).
- **Near-duplicate distractors**: v1 and v2 of a plan, or two projects with similarly named
  features.
- **Long docs where the answer is one paragraph deep inside.**
- **Superseded docs**: an older decision that a newer doc overrides (backdate the old one's mtime
  via a manifest that the harness applies with `os.utime`).

Write `bench/corpus/MANIFEST.json` with each file's project, intended mtime, and which planted
cases it carries.

## 2. Queries and labels (blind to the systems)

The subagent that writes queries **must not run any search system.** Write 80–120 queries in
`bench/queries.jsonl`:
`{"id", "query", "relevant": [paths], "graded": {path: 2|1}, "category", "split"}`.

Categories (roughly balanced): `paraphrase`, `exact-identifier`, `heading-context`,
`deep-in-long-doc`, `disambiguation`, `recency/superseded`, `vague-recall` ("that thing about the
fox sprite cache"). Write queries the way a person or agent actually asks. For `paraphrase`, avoid
the doc's distinctive words.

Then a **separate auditor subagent** checks every label: is the relevant doc really the answer,
and is any other doc equally right (add it)? It also computes the query/doc word overlap per
category and flags leakage (paraphrase queries that copy doc wording).

## 3. Systems compared

Implement these behind one interface in `bench/` (or `filebrain/eval.py`):

| id | system | how |
|---|---|---|
| `grep` | **the default agent behavior** | ripgrep-style: case-insensitive match of the query's non-stopword terms; rank files by distinct terms matched, then total hits. This is what an agent does with `rg`/`grep`. |
| `bm25` | keyword only | FileBrain with `dense_weight: 0` |
| `dense` | embeddings only | FileBrain with `dense_weight: 1` |
| `hybrid` | **FileBrain as shipped** | `baseline-v0` policy |
| `hybrid-noheadings` | ablation | index built with the plain chunker (add an opt-in config switch) |
| `hybrid-norerank` | ablation | `rerank_budget: 0` |

Optional: a `filename` baseline (match query terms against paths only).

Keep recency/metadata weights identical across FileBrain variants unless an ablation is about
them, and state exactly what each variant includes.

## 4. Metrics

Per system, on test (and dev, reported separately): **Recall@1, @5, @10**, **MRR@10**,
**nDCG@10** (graded labels), with **95% bootstrap confidence intervals** (1,000 resamples over
queries), broken down per category. Also report query latency p50/p95 and index build time. Add a
`filebrain eval --config ... --queries ... --system ...` command (or `python -m bench.run`) that
writes `bench/results/<system>.json`, deterministic for a fixed corpus and model.

## 5. Report and chart

- `bench/REPORT.md`: setup (model, hardware, commit, corpus stats), the headline table, a
  per-category table, **where hybrid does not win and why** (with 2–3 example queries), threats to
  validity (synthetic, LLM-written corpus and queries, a single embedding model, corpus size), and
  how to reproduce it with one command.
- `docs/benchmark.svg` (matplotlib, readable in light and dark themes): grouped bars of Recall@5
  (or MRR) per system with CI error bars, `grep` first as the baseline. A second, per-category
  chart is welcome.
- Propose (don't apply) a 3–5 line "Benchmark" section for `README.md` with the chart and the
  honest one-sentence takeaway.

## 6. Red-team before you finish

A fresh subagent reviews the study for bias: test-set tuning, label leakage, a weak strawman
`grep`, cherry-picked categories, or numbers in REPORT.md that don't match `bench/results/`. Fix
what it finds and note it in the report.

## Done when

- One command reproduces every number, and the results JSON matches REPORT.md.
- Tests pass and the branch `bench-study` has the commits. Nothing is pushed.
- You reply with the headline table, the chart path, the biggest caveat, and anything you
  couldn't do.
