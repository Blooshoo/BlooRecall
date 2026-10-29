# Haiku probe

A stress test for rank fusion, not a benchmark of anything you would search. Forty haiku, one per
file, and for each a query that describes it without sharing a content word with it:

> *Fog swallows the bridge; / a ferry's low horn tells us / the river is there.*
>
> "mist hides the crossing; a deep steamboat call reveals the water"

Keyword search has nothing true to match, so the gap between `dense` and `hybrid-rrf` is what
keyword noise costs the fused ranking. Real notes share far more words with the queries that find
them; short ones (stickies, three-line reminders) sit closest to this case.

```bash
python3 -m bench.haiku_probe     # bench config's Ollama model; file times equalised so
                                 # recency cannot reward the order the poems were written in
```

Measured with all-MiniLM-L6-v2 (a stand-in, since the probe was built without Ollama to hand):

| | R@1 | R@5 | MRR@10 |
|---|---|---|---|
| dense, v1.1 | 0.800 | 0.950 | 0.849 |
| hybrid-rrf, v1.1 | 0.125 | 0.575 | 0.287 |
| hybrid-rrf, v1.2 | 0.550 | 0.925 | 0.694 |

v1.1 counted function words ("the", "a", "on") as keyword evidence, and a poem sharing no word
with the query got nothing from BM25, so it ranked below every poem that shared one. v1.2 drops
function words from the BM25 query and ranks unmatched chunks just after the last match.

Provenance: poems and queries were written by a Claude Haiku agent told never to reuse a noun,
verb, adjective or adverb of the target poem in its query. `tests/tests_bench.py` holds every
query to that (the possessive "s" of "gust's" aside).
