from __future__ import annotations

import json
import math
import re
import threading
from pathlib import Path
from typing import Any

import numpy as np

from . import store
from .config import active_policy, index_path
from .embeddings import EmbeddingUnavailable, OllamaEmbedder
from .trust import TrustVerdict, verify_path
from .util import tokens, utc_iso

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

BM25_K1 = 1.5
BM25_B = 0.75
COVERAGE_BONUS = 0.18
WHITESPACE_RE = re.compile(r"\s+")


class PrivateQueryRefused(RuntimeError):
    """Raised when a query asks for material BlooRecall will not surface."""


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
            model = self.metadata.get("embedding_model", "")
            self._cached_text_hashes: set[str] = store.cached_text_hashes(connection, model)
        finally:
            connection.close()
        self.fingerprint = _fingerprint(path)
        self.chunk_ids = [row[0] for row in rows]
        self.paths = [row[1] for row in rows]
        self.ordinals = [int(row[2]) for row in rows]
        self.content_hashes = [row[3] for row in rows]
        self.texts = [row[4] for row in rows]
        self.token_counts = np.array([float(row[5]) for row in rows], dtype=np.float32)
        self.mtimes = np.array([float(row[8]) for row in rows], dtype=np.float64)
        self.projects = [row[9] for row in rows]
        self.file_types = [row[11] for row in rows]
        self.text_hashes = [row[12] for row in rows]
        self.indexed_ats = [float(row[13]) for row in rows]

        # Path-level lookups for trust verification: every chunk of a file shares
        # the same content_hash / indexed_at, so we key on path.
        self._path_text_hashes: dict[str, list[str]] = {}
        for path_value, text_hash in zip(self.paths, self.text_hashes):
            self._path_text_hashes.setdefault(path_value, []).append(text_hash)

        self.count = len(rows)
        # Postings are held as numpy pairs: a Python list of tuples for a corpus this
        # size costs hundreds of megabytes, two arrays per term costs tens.
        raw_postings: dict[str, tuple[list[int], list[float]]] = {}
        for index, row in enumerate(rows):
            for term, frequency in json.loads(row[6]).items():
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
        del raw_postings
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
        self.path_terms: dict[str, set[str]] = {}
        for path_value, project in zip(self.paths, self.projects):
            if path_value not in self.path_terms:
                self.path_terms[path_value] = set(tokens(f"{path_value} {project}"))
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
                cached_text_hashes=self._cached_text_hashes,
                path_text_hashes=self._path_text_hashes.get(row["path"], []),
            )
            row["trust"] = {
                "verdict": check.verdict.value,
                "reason": check.reason,
                "file_exists": check.file_exists,
                "hash_match": check.on_disk_hash is not None
                and check.on_disk_hash == check.indexed_hash,
                "embedding_fresh": check.embedding_fresh,
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
            df = int(indices.size)
            idf = math.log(1.0 + (self.count - df + 0.5) / (df + 0.5))
            contribution = idf * frequencies * (BM25_K1 + 1) / (
                frequencies + BM25_K1 * length_norm[indices]
            )
            scores[indices] += contribution * occurrences
            matched_terms[indices] += 1.0
        return scores, matched_terms

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
        query_terms = tokens(question)
        query_set = set(query_terms)
        lexical, matched_terms = self._bm25(query_terms)
        maximum = float(lexical.max()) if self.count else 0.0
        bm25_normalized = lexical / (maximum or 1.0)

        if query_vector is None:
            dense_weight = 0.0
            dense_normalized = np.zeros(self.count, dtype=np.float32)
        else:
            dense_weight = float(policy["dense_weight"])
            query = np.asarray(query_vector, dtype=np.float32)
            dense_normalized = (self.matrix @ query + 1.0) / 2.0

        overlap_by_path = np.array(
            [
                len(query_set & self.path_terms[path_value]) / max(1, len(query_set))
                for path_value in self.unique_paths
            ],
            dtype=np.float32,
        )
        metadata_overlap = overlap_by_path[self.path_index]

        mtime_range = max(1.0, self.max_mtime - self.min_mtime)
        recency = ((self.mtimes - self.min_mtime) / mtime_range).astype(np.float32)

        scores = (
            dense_weight * dense_normalized
            + (1.0 - dense_weight) * bm25_normalized
            + float(policy["recency_weight"]) * recency
            + float(policy["metadata_weight"]) * metadata_overlap
        )
        coverage = matched_terms / max(1, len(query_set))
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


def snippet_for(text: str, question: str, limit: int) -> str:
    """Window the chunk around the densest run of query terms, then flatten it."""
    flat = WHITESPACE_RE.sub(" ", text).strip()
    if len(flat) <= limit:
        return flat
    lowered = flat.casefold()
    positions = [
        lowered.find(term) for term in {token for token in tokens(question) if len(token) > 2}
    ]
    hits = sorted(position for position in positions if position >= 0)
    if not hits:
        return flat[:limit].rstrip() + "…"
    centre = hits[len(hits) // 2]
    start = max(0, centre - limit // 3)
    window = flat[start : start + limit].strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if start + limit < len(flat) else ""
    return f"{prefix}{window}{suffix}"


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
        # Ollama down or the model missing must not take search down with it: keep answering
        # from the keyword index and say so, instead of failing the whole query.
        retrieval = "hybrid"
        warning: str | None = None
        vector: list[float] | None
        try:
            vector = self.embedder.embed_one(question)
        except EmbeddingUnavailable as error:
            vector, retrieval, warning = None, "keyword-only", str(error)
        results = index.rank(question, vector, policy, project=project)[:limit]

        snippet_chars = int(defaults.get("snippet_chars", 240))
        for rank, row in enumerate(results, start=1):
            row["rank"] = rank
            row["snippet"] = snippet_for(row.pop("text"), question, snippet_chars)
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
