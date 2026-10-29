from __future__ import annotations

import json
import math
import os
import re
import threading
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from . import store
from .config import FUSION_MODES, active_policy, index_path
from .embeddings import EmbeddingUnavailable, OllamaEmbedder
from .trust import verify_path
from .util import TOKEN_RE, TOKENIZER_VERSION, tokens, utc_iso, words

# Only owner-local corpus material is searchable. The column is kept so a future
# permission tier cannot silently become visible.
ALLOWED_PERMISSIONS = {"local_owner_only"}

# Inherited from the v0 lab: BlooRecall declines to act as a secret finder.
PRIVATE_QUERY_MARKERS = {
    ".env",
    "api key",
    "access token",
    "password",
    "credential locker",
    "secret key",
    "private conversation",
    "personal memory",
}

# Function words are dropped from the query before BM25 (the index keeps every term). BM25's IDF
# makes them light, but rank fusion only sees ranks: a chunk sharing nothing but "the" with the
# query still earns a keyword rank, a short chunk a high one, so on short notes these words
# decided the order (v1.1). Same list as the frozen grep baseline's; a query of nothing but
# function words keeps them all.
STOPWORDS = frozenset(
    """a about after all also an and any are as at be because been before being both but by came can
could did do does done for from get gets got had has have he her here hers him his how i if in into is
it its just like made make many may me might more most much must my never no nor not now of off on one
only or other our out over own said same see she should since so some such than that the their them
then there these they this those through to too under until up use used using very was way we well
were what when where which while who why will with within without would you your""".split()
)
BM25_K1 = 1.5
BM25_B = 0.75
COVERAGE_BONUS = 0.18
RRF_K = 60
WHITESPACE_RE = re.compile(r"\s+")


class PrivateQueryRefused(RuntimeError):
    """Raised when a query asks for material BlooRecall will not surface."""


def keyword_terms(question: str) -> list[str]:
    """The query's BM25 terms: its tokens minus function words (all of them if that is all)."""
    terms = tokens(question)
    return [term for term in terms if term not in STOPWORDS] or terms


def private_query_reason(question: str) -> str | None:
    lowered = question.casefold()
    for marker in sorted(PRIVATE_QUERY_MARKERS):
        if marker in lowered:
            return marker
    return None


class BlooRecallIndex:
    """In-memory view of the on-disk index: postings for BM25, a matrix for dense."""

    def __init__(self, path: Path) -> None:
        self.path = path
        connection = store.connect_read(path)
        try:
            self.metadata = store.read_metadata(connection)
            rows = store.load_search_rows(connection, ALLOWED_PERMISSIONS)
        finally:
            connection.close()
        self.fingerprint = _fingerprint(path)
        self.chunk_ids = [row[0] for row in rows]
        self.paths = [row[1] for row in rows]
        self.ordinals = [int(row[2]) for row in rows]
        self.content_hashes = [row[3] for row in rows]
        self.texts = [row[4] for row in rows]
        self.mtimes = np.array([float(row[8]) for row in rows], dtype=np.float64)
        self.projects = [row[9] for row in rows]
        self.file_types = [row[11] for row in rows]
        self.indexed_ats = [float(row[13]) for row in rows]

        # Term counts are stored per chunk at index time. An index written by an older tokenizer
        # is re-tokenized from its chunk text here, so search is right before the next refresh
        # (which rewrites the stored counts, without re-embedding anything).
        if self.metadata.get("tokenizer_version") == TOKENIZER_VERSION:
            term_counts = [json.loads(row[6]) for row in rows]
        else:
            term_counts = [Counter(tokens(text)) for text in self.texts]
        self.token_counts = np.array(
            [float(sum(counts.values())) for counts in term_counts], dtype=np.float32
        )

        self.count = len(rows)
        # Postings are held as numpy pairs: a Python list of tuples for a corpus this
        # size costs hundreds of megabytes, two arrays per term costs tens.
        raw_postings: dict[str, tuple[list[int], list[float]]] = {}
        for index, counts in enumerate(term_counts):
            for term, frequency in counts.items():
                entry = raw_postings.get(term)
                if entry is None:
                    entry = ([], [])
                    raw_postings[term] = entry
                entry[0].append(index)
                entry[1].append(float(frequency))
        self.postings: dict[str, tuple[np.ndarray, np.ndarray]] = {
            term: (np.array(indices, dtype=np.int64), np.array(frequencies, dtype=np.float32))
            for term, (indices, frequencies) in raw_postings.items()
        }
        del raw_postings, term_counts
        self.average_length = float(self.token_counts.mean()) if self.count else 1.0

        dimension = int(self.metadata.get("embedding_dimension", 0) or 0)
        if self.count and not dimension:
            dimension = len(store.blob_vector(rows[0][7]))
        self.dimension = dimension
        matrix = np.zeros((self.count, dimension), dtype=np.float32)
        for index, row in enumerate(rows):
            vector = np.frombuffer(row[7], dtype="<f4")
            if vector.size != dimension:
                raise RuntimeError(
                    f"chunk {row[0]} has dimension {vector.size}, expected {dimension}; "
                    "rebuild with 'bloorecall refresh --full'"
                )
            matrix[index] = vector
        self.matrix = matrix

        # Path metadata is identical for every chunk of a file; score it once per path.
        self.path_terms = _path_terms(self.paths, self.projects, [row[14] for row in rows])
        self.path_index = np.array(_path_indices(self.paths), dtype=np.int32)
        self.unique_paths = _unique_paths(self.paths)
        self.min_mtime = float(self.mtimes.min()) if self.count else 0.0
        self.max_mtime = float(self.mtimes.max()) if self.count else 1.0

    def verify_hits(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Attach a per-hit trust verdict to each result, verified against disk.

        This runs before results are returned to the agent. Each hit's file is
        stat-checked and re-hashed so the agent always knows whether the content
        behind it has drifted, moved, or been deleted since indexing.
        """
        refreshed_at = float(self.metadata.get("refreshed_at", 0) or 0)
        for row in results:
            check = verify_path(
                path=row["path"],
                indexed_hash=row["content_hash"],
                indexed_at=row["indexed_at"],
                refreshed_at=refreshed_at,
            )
            row["trust"] = {
                "verdict": check.verdict.value,
                "reason": check.reason,
                "file_exists": check.file_exists,
                "hash_match": check.on_disk_hash is not None
                and check.on_disk_hash == check.indexed_hash,
            }
        return results

    def _bm25(self, query_terms: list[str]) -> tuple[np.ndarray, np.ndarray]:
        scores = np.zeros(self.count, dtype=np.float32)
        matched_terms = np.zeros(self.count, dtype=np.float32)
        length_norm = 1 - BM25_B + BM25_B * self.token_counts / max(1.0, self.average_length)
        for term in set(query_terms):
            postings = self.postings.get(term)
            if postings is None:
                continue
            indices, frequencies = postings
            occurrences = query_terms.count(term)
            idf = self._idf(int(indices.size))
            contribution = idf * frequencies * (BM25_K1 + 1) / (
                frequencies + BM25_K1 * length_norm[indices]
            )
            scores[indices] += contribution * occurrences
            matched_terms[indices] += 1.0
        return scores, matched_terms

    def _idf(self, df: int) -> float:
        return math.log(1.0 + (self.count - df + 0.5) / (df + 0.5))

    def term_weights(self, question: str) -> dict[str, float]:
        """The query's terms weighted by rarity (BM25's IDF), for windowing snippets."""
        return {term: self._idf(self.postings[term][0].size if term in self.postings else 0)
                for term in set(tokens(question))}

    def rank(
        self,
        question: str,
        query_vector: list[float] | None,
        policy: dict[str, Any],
        project: str | None = None,
    ) -> list[dict[str, Any]]:
        """Score every chunk and return the best chunk per file.

        `query_vector=None` means keyword-only ranking (the embedder is unavailable).
        `project` is a case-insensitive substring filter applied before ranking, so a small
        project can never be starved out by stronger matches elsewhere.
        """
        if not self.count:
            return []
        query_terms = keyword_terms(question)
        query_set = set(query_terms)
        lexical, matched_terms = self._bm25(query_terms)
        maximum = float(lexical.max()) if self.count else 0.0
        bm25_normalized = lexical / (maximum or 1.0)

        if query_vector is None:
            relevance = bm25_normalized
        else:
            dense_weight = float(policy["dense_weight"])
            similarity = self.matrix @ np.asarray(query_vector, dtype=np.float32)
            fusion = policy.get("fusion", "raw")
            if fusion == "rrf":
                relevance = _rrf(similarity, lexical, dense_weight, int(policy.get("rrf_k", RRF_K)))
            else:
                relevance = (
                    dense_weight * _dense_scale(similarity, fusion)
                    + (1.0 - dense_weight) * bm25_normalized
                )

        query_words = set(words(question))
        overlap_by_path = np.array(
            [
                len(query_words & self.path_terms[path_value]) / max(1, len(query_words))
                for path_value in self.unique_paths
            ],
            dtype=np.float32,
        )
        metadata_overlap = overlap_by_path[self.path_index]

        mtime_range = max(1.0, self.max_mtime - self.min_mtime)
        recency = ((self.mtimes - self.min_mtime) / mtime_range).astype(np.float32)

        scores = (
            relevance
            + float(policy["recency_weight"]) * recency
            + float(policy["metadata_weight"]) * metadata_overlap
        )
        coverage = matched_terms / max(1, len(query_set))
        if query_vector is None:
            # Keyword-only search must not pad its list with files that match nothing (ranked by
            # recency alone): a hit needs a query term in its text or in its path.
            matched = (lexical > 0) | (metadata_overlap > 0)
            scores = np.where(matched, scores, -np.inf).astype(np.float32)
        if project:
            needle = project.casefold()
            allowed = np.array([needle in label.casefold() for label in self.projects], dtype=bool)
            if not allowed.any():
                return []
            scores = np.where(allowed, scores, -np.inf).astype(np.float32)

        # Rows are loaded ordered by (path, ordinal), so a stable sort on the negated
        # score reproduces the v0 tie-break without a Python-level comparison key.
        order = np.argsort(-scores, kind="stable")
        final = scores.copy()
        budget = int(policy["rerank_budget"])
        if budget:
            head = order[:budget]
            final[head] += COVERAGE_BONUS * coverage[head]
            order = np.concatenate([head[np.argsort(-final[head], kind="stable")], order[budget:]])

        best_by_path: dict[str, tuple[float, int]] = {}
        for position in order:
            index = int(position)
            if not np.isfinite(final[index]):
                continue
            path_value = self.paths[index]
            existing = best_by_path.get(path_value)
            score = float(final[index])
            if existing is None or score > existing[0]:
                best_by_path[path_value] = (score, index)
        ranked = sorted(best_by_path.items(), key=lambda item: (-item[1][0], item[0]))
        top_k = int(policy["top_k"])
        return [
            {
                "rank": rank,
                "score": round(score, 8),
                "path": path_value,
                "project": self.projects[index],
                "file_type": self.file_types[index],
                "mtime": float(self.mtimes[index]),
                "mtime_iso": utc_iso(float(self.mtimes[index])),
                "chunk_id": self.chunk_ids[index],
                "chunk_ordinal": self.ordinals[index],
                "text": self.texts[index],
                "content_hash": self.content_hashes[index],
                "indexed_at": float(self.indexed_ats[index]),
            }
            for rank, (path_value, (score, index)) in enumerate(ranked[:top_k], start=1)
        ]


def _dense_scale(similarity: np.ndarray, fusion: str) -> np.ndarray:
    """Put cosine similarities on BM25's [0, 1] scale; see FUSION_MODES in config."""
    if fusion == "raw":
        return (similarity + 1.0) / 2.0
    if fusion == "minmax":
        low = float(similarity.min())
        spread = float(similarity.max()) - low
        if spread <= 0.0:
            # Every chunk is equally similar: dense carries no ranking signal.
            return np.zeros_like(similarity)
        return (similarity - low) / spread
    raise ValueError(f"unknown fusion mode '{fusion}'; expected one of {', '.join(FUSION_MODES)}")


def _ranks(values: np.ndarray) -> np.ndarray:
    ranks = np.empty(values.size, dtype=np.float32)
    ranks[np.argsort(-values, kind="stable")] = np.arange(1, values.size + 1, dtype=np.float32)
    return ranks


def _rrf(similarity: np.ndarray, lexical: np.ndarray, dense_weight: float, k: int) -> np.ndarray:
    """Weighted reciprocal-rank fusion of the dense and BM25 orders, scaled so the best is 1.0.

    Fusing ranks rather than raw scores is the point: cosine similarities from one embedder sit
    in a narrow band (top candidates differ by ~0.05) while max-normalized BM25 spans [0, 1], so
    the raw blend lets BM25 decide the order whatever dense_weight says. Ranks are scale-free, so
    the weight means the same thing for any model or corpus size (minmax rescaling fixes the
    scale too, but anchors to the query's least similar chunk, so its effective weight drifts as the
    corpus grows).

    Both orders rank every chunk: one with no keyword match shares the rank after the last match
    instead of getting nothing from BM25. No keyword evidence then counts as the weakest evidence
    rather than as worse than any, which (v1.1) buried a right note that shares no word with the
    query under every chunk that shares one.
    """
    matched = lexical > 0
    keyword_ranks = np.where(matched, _ranks(lexical), np.count_nonzero(matched) + 1)
    fused = dense_weight / (k + _ranks(similarity))
    fused += (1.0 - dense_weight) / (k + keyword_ranks)
    return (fused / (float(fused.max()) or 1.0)).astype(np.float32)


def _path_terms(paths: list[str], projects: list[str], root_labels: list[str]) -> dict[str, set[str]]:
    """Words naming where each file sits: its project label, its folders and its file stem.

    The folders above a corpus root (/home/<user>/notes) are shared by every file in it, so they
    carry no signal; cut them by taking the deepest folder all of that root's files share.
    """
    folders_by_root: dict[str, set[str]] = {}
    for path_value, root_label in zip(paths, root_labels):
        folders_by_root.setdefault(root_label, set()).add(os.path.dirname(path_value))
    base_by_root = {label: os.path.commonpath(folders) for label, folders in folders_by_root.items()}
    terms: dict[str, set[str]] = {}
    for path_value, project, root_label in zip(paths, projects, root_labels):
        if path_value not in terms:
            below = os.path.relpath(path_value, base_by_root[root_label])
            terms[path_value] = set(words(f"{project} {os.path.splitext(below)[0]}"))
    return terms


def _path_indices(paths: list[str]) -> list[int]:
    lookup: dict[str, int] = {}
    result: list[int] = []
    for value in paths:
        if value not in lookup:
            lookup[value] = len(lookup)
        result.append(lookup[value])
    return result


def _unique_paths(paths: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in paths:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _fingerprint(path: Path) -> tuple[float, int]:
    stat = path.stat()
    return (stat.st_mtime, stat.st_size)


def snippet_for(
    text: str, question: str, limit: int, weights: dict[str, float] | None = None
) -> str:
    """Flatten the chunk and window it on the stretch that holds the most query terms.

    Each distinct term counts once per window, by its weight: the index's IDF, so a rare
    "kiln" outweighs a "how" the query also contains (1.0 each without weights). The window
    opens a little before its first hit and is trimmed to whole words.
    """
    flat = WHITESPACE_RE.sub(" ", text).strip()
    if len(flat) <= limit:
        return flat
    wanted = {token for token in tokens(question) if len(token) > 2}
    hits: list[tuple[int, str]] = []
    for match in TOKEN_RE.finditer(flat):
        term = match.group().casefold()
        if term in wanted:
            hits.append((match.start(), term))
    if not hits:
        return flat[:limit].rstrip() + "…"
    weight = (weights or {}).get
    span = limit * 3 // 4  # the hits must fit here; the rest of the window is lead-in
    best, best_score, right = 0, -1.0, 0
    inside: Counter[str] = Counter()
    for left, (position, term) in enumerate(hits):
        while right < len(hits) and hits[right][0] < position + span:
            inside[hits[right][1]] += 1
            right += 1
        score = sum(weight(name, 1.0) for name in inside)
        if score > best_score:
            best, best_score = left, score
        inside[term] -= 1
        if not inside[term]:
            del inside[term]
    anchor = hits[best][0]
    start = max(0, min(anchor - (limit - span), len(flat) - limit))
    if start:
        boundary = flat.find(" ", start, anchor)
        start = boundary + 1 if boundary >= 0 else start
    window = flat[start : start + limit]
    if start + limit < len(flat) and " " in window:
        window = window[: window.rfind(" ")]
    prefix = "…" if start > 0 else ""
    suffix = "…" if start + len(window) < len(flat) else ""
    return f"{prefix}{window.strip()}{suffix}"


class SearchEngine:
    """Config plus a lazily loaded index that reloads when the index file changes."""

    def __init__(self, config: dict[str, Any], embedder: OllamaEmbedder | None = None) -> None:
        self.config = config
        self.embedder = embedder or OllamaEmbedder.from_config(config)
        self.index_path = index_path(config)
        self._index: BlooRecallIndex | None = None
        self._lock = threading.Lock()

    @property
    def index(self) -> BlooRecallIndex:
        with self._lock:
            if self._index is None or self._index.fingerprint != _fingerprint(self.index_path):
                self._index = BlooRecallIndex(self.index_path)
            return self._index

    def _query_vector(
        self, index: BlooRecallIndex, question: str
    ) -> tuple[list[float] | None, str | None]:
        """Embed the query, or say why this search has to rank by keyword alone.

        Ollama down or the model missing must not take search down with it, and a vector from a
        model other than the index's would rank chunks by noise (or not fit the matrix at all),
        so each falls back to the keyword index with a warning instead of failing the query.
        """
        indexed_model = index.metadata.get("embedding_model", "")
        if indexed_model and indexed_model != self.embedder.model:
            return None, (
                f"index was built with '{indexed_model}' but config asks for "
                f"'{self.embedder.model}'; run 'bloorecall refresh --full' to re-embed"
            )
        try:
            vector = self.embedder.embed_one(question)
        except EmbeddingUnavailable as error:
            return None, str(error)
        if index.count and len(vector) != index.dimension:
            return None, (
                f"the query embedding has {len(vector)} dimensions but the index holds "
                f"{index.dimension}; run 'bloorecall refresh --full' to re-embed"
            )
        return vector, None

    def search(
        self,
        query: str,
        top_k: int | None = None,
        policy_name: str | None = None,
        project: str | None = None,
    ) -> dict[str, Any]:
        question = (query or "").strip()
        if not question:
            raise ValueError("query must not be empty")
        refusal = private_query_reason(question)
        if refusal:
            raise PrivateQueryRefused(
                f"BlooRecall does not search for credential-shaped material (matched '{refusal}')"
            )
        defaults = self.config["search_defaults"]
        policy = active_policy(self.config, policy_name)
        requested = int(top_k or defaults.get("top_k", policy["top_k"]))
        limit = max(1, min(requested, int(defaults.get("max_top_k", 50))))
        policy["top_k"] = limit

        index = self.index
        vector, warning = self._query_vector(index, question)
        retrieval = "keyword-only" if vector is None else "hybrid"
        results = index.rank(question, vector, policy, project=project)[:limit]

        snippet_chars = int(defaults.get("snippet_chars", 240))
        weights = index.term_weights(question)
        for rank, row in enumerate(results, start=1):
            row["rank"] = rank
            row["snippet"] = snippet_for(row.pop("text"), question, snippet_chars, weights)
        # Heimdall-style per-hit disk verification: stat + re-hash before the
        # agent sees the result. Adds two file reads per top hit — cheap on a
        # local box, worth the staleness guarantee.
        index.verify_hits(results)

        return {
            "query": question,
            "retrieval": retrieval,
            **({"warning": warning} if warning else {}),
            "policy": policy["policy_id"],
            "top_k": limit,
            "project_filter": project,
            "index": {
                "path": str(self.index_path),
                "source_count": int(index.metadata.get("source_count", 0) or 0),
                "chunk_count": index.count,
                "embedding_model": index.metadata.get("embedding_model", ""),
                "manifest_sha256": index.metadata.get("manifest_sha256", ""),
                "refreshed_at_iso": utc_iso(float(index.metadata.get("refreshed_at", 0) or 0)),
            },
            "results": results,
        }
