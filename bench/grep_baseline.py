"""The `grep` baseline: a faithful Python implementation of what a coding agent
does by default with `rg`/`grep`.

Spec (fixed before any system ran, from BENCHMARK-STUDY-PROMPT.md):
- take the query's non-stopword terms;
- case-insensitive substring match of each term against every candidate file's
  text (the equivalent of `rg -i term1 term2 ...` over the corpus);
- rank files by DISTINCT terms matched (descending), then by total hits
  (number of lines containing at least one term, i.e. `rg -i -c 't1|t2'`),
  then by path for determinism.

The `filename` variant matches the same terms against the file path only.

This is deliberately not tuned: no stemming, no scoring weights, no embeddings.
Latency reported for it is THIS implementation's (pure Python), not the C
`rg` binary's.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from bloorecall.util import tokens

# Compact standard English stopword list, frozen for the study. Queries are
# short questions ("how do we retry a dropped socket"), so the common
# interrogatives and articles must not drive ranking.
STOPWORDS = frozenset(
    """a about after all also an and any are as at be because been before being both but by came can
could did do does done for from get gets got had has have he her here hers him his how i if in into is
it its just like made make many may me might more most much must my never no nor not now of off on one
only or other our out over own said same see she should since so some such than that the their them
then there these they this those through to too under until up use used using very was way we well
were what when where which while who why will with within without would you your""".split()
)


def query_terms(question: str) -> List[str]:
    seen: List[str] = []
    for term in tokens(question):
        if term in STOPWORDS:
            continue
        if term not in seen:
            seen.append(term)
    return seen


class GrepBaseline:
    """Scans the corpus roots the benchmark config points at, per query."""

    system_id = "grep"

    def __init__(self, roots: List[Path], allowed_extensions: List[str]) -> None:
        self.roots = roots
        self.allowed_extensions = {suffix.casefold() for suffix in allowed_extensions}
        self.files: List[Path] = []
        self.relative: Dict[Path, str] = {}

    def setup(self, base: Path, prefix: str = "") -> Dict[str, Any]:
        candidates: List[Path] = []
        for root in self.roots:
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.is_symlink():
                    continue
                if path.suffix.casefold() not in self.allowed_extensions:
                    continue
                candidates.append(path)
                self.relative[path] = f"{prefix}{path.relative_to(base).as_posix()}"
        self.files = candidates
        return {"files_scanned": len(self.files)}

    def _match_terms(self, path: Path, terms: List[str]) -> Tuple[int, int]:
        """(distinct terms matched, lines containing at least one term)."""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return 0, 0
        lowered = text.casefold()
        distinct = sum(1 for term in terms if term in lowered)
        if distinct == 0:
            return 0, 0
        hits = sum(1 for line in lowered.splitlines() if any(term in line for term in terms))
        return distinct, hits

    def search(self, question: str, top_k: int = 10) -> List[str]:
        terms = query_terms(question)
        if not terms:
            return []
        scored: List[Tuple[int, int, str, Path]] = []
        for path in self.files:
            distinct, hits = self._match_terms(path, terms)
            if distinct:
                scored.append((-distinct, -hits, self.relative[path], path))
        scored.sort()
        return [self.relative[path] for *_, path in scored[:top_k]]

    def close(self) -> None:
        self.files = []


class FilenameBaseline(GrepBaseline):
    """Same terms, matched against the file path only (an agent trying names)."""

    system_id = "filename"

    def search(self, question: str, top_k: int = 10) -> List[str]:
        terms = query_terms(question)
        if not terms:
            return []
        scored: List[Tuple[int, str]] = []
        for path in self.files:
            relative = self.relative[path]
            lowered = relative.casefold()
            distinct = sum(1 for term in terms if term in lowered)
            if distinct:
                scored.append((-distinct, relative))
        scored.sort()
        return [relative for _, relative in scored[:top_k]]
