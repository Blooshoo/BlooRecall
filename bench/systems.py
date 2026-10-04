"""The systems under test, behind one interface.

Every system answers `search(query, top_k) -> [corpus-relative paths]`
(formatted "bench/corpus/<project>/<file>", matching query labels).

Why a mirror: BlooRecall refuses to index anything under its own project
directory (`bloorecall self-ingestion` gate), and the benchmark corpus is
versioned inside the repo at bench/corpus/. The harness therefore mirrors the
corpus once per run to a fixed temp location (identical bytes, mtimes
preserved with copy2), and points every system — including grep, so all
systems see exactly the same files — at the mirror. Labels in queries.jsonl
and results JSON stay repo-relative and portable.

BlooRecall variants all share:
- the same index build (except hybrid-noheadings, which uses the opt-in
  plain chunker — the only code-level ablation switch, `chunker_override`);
- the same recency (0.05) and metadata (0.15) weights and coverage
  re-rank budget (20) unless the variant is explicitly about removing
  them (hybrid-norerank sets rerank_budget: 0);
- ranking via BlooRecallIndex.rank(), i.e. the shipped scoring path minus
  per-hit disk verification and snippet windowing, which change trust
  annotations and snippets but never the file ranking.

Per-variant honesty notes (repeated in REPORT.md):
- grep/filename: pure-Python scan over corpus files; no index.
- bm25: BlooRecall keyword-only — the query is NOT embedded (vector=None,
  the shipped fallback path when Ollama is down).
- dense: BlooRecall with dense_weight=1.0 (query embedded; BM25 still
  computed but weighted out by the policy, exactly as the shipped policy
  arithmetic would do).
- hybrid: BlooRecall exactly as shipped — baseline-v0 policy (dense 0.55 /
  bm25 0.45 / recency 0.05 / metadata 0.15, coverage re-rank over the
  top 20).
- hybrid-noheadings: baseline-v0 policy over an index built with the
  plain paragraph chunker (no heading breadcrumbs). Same embeddings.
- hybrid-norerank: baseline-v0 with rerank_budget 0 (no coverage bonus).
- hybrid-norecency: baseline-v0 with recency_weight 0 (quantifies how much
  the engineered mtimes contribute through the recency feature).
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from bloorecall import indexer
from bloorecall.config import index_path
from bloorecall.embeddings import OllamaEmbedder
from bloorecall.search import BlooRecallIndex
from bloorecall.util import PROJECT_ROOT

from bench.grep_baseline import FilenameBaseline, GrepBaseline

CORPUS_SOURCE = PROJECT_ROOT / "bench" / "corpus"
CORPUS_PREFIX = "bench/corpus"
MIRROR_NAME = "bloorecall-bench-corpus"


def prepare_corpus_mirror() -> Path:
    """Mirror bench/corpus to a fixed temp dir (bytes identical, mtimes kept).

    A fixed name keeps the indexed absolute paths stable across runs and
    machines; BlooRecall tokenizes absolute paths for its metadata feature, so
    a per-run random path would add nondeterministic tokens.
    """
    mirror = Path(tempfile.gettempdir()) / MIRROR_NAME
    if mirror.exists():
        shutil.rmtree(mirror)
    shutil.copytree(CORPUS_SOURCE, mirror, copy_function=shutil.copy2)
    return mirror


def resolve_config(raw_config: Dict[str, Any], corpus_root: Path) -> Dict[str, Any]:
    """Copy the bench config with corpus roots pointed at the corpus mirror."""
    config = dict(raw_config)
    config["corpus_roots"] = [
        {**root, "path": str(corpus_root / Path(root["path"]).name)}
        for root in raw_config["corpus_roots"]
    ]
    return config


def plain_variant_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Config for the hybrid-noheadings index: opt-in plain chunker, own index."""
    variant = dict(config)
    variant["index_path"] = config["plain_index_path"]
    variant["parse_version"] = config["plain_parse_version"]
    variant["chunker_override"] = "plain"
    return variant


def build_index(
    config: Dict[str, Any],
    *,
    fresh: bool,
    progress=None,
    embedder: Optional[OllamaEmbedder] = None,
) -> Dict[str, Any]:
    """(Re)build a bench index; returns the refresh summary (has elapsed_seconds)."""
    target = index_path(config)
    target.parent.mkdir(parents=True, exist_ok=True)
    embedder = embedder or OllamaEmbedder.from_config(config)
    return indexer.refresh(config, full=fresh, progress=progress or (lambda _m: None), embedder=embedder)


class GrepSystem:
    """Wraps bench.grep_baseline for the runner's uniform interface."""

    def __init__(self, config: Dict[str, Any], variant: str, corpus_root: Path) -> None:
        self.corpus_root = corpus_root
        self.roots = [Path(root["path"]) for root in config["corpus_roots"]]
        self.allowed_extensions = list(config["allowed_extensions"])
        self.variant: Any = (
            GrepBaseline(self.roots, self.allowed_extensions)
            if variant == "grep"
            else FilenameBaseline(self.roots, self.allowed_extensions)
        )

    @property
    def system_id(self) -> str:
        return self.variant.system_id

    def setup(self, fresh: bool = False, embedder: Any = None) -> Dict[str, Any]:
        return self.variant.setup(self.corpus_root, f"{CORPUS_PREFIX}/")

    def search(self, query: str, top_k: int = 10) -> List[str]:
        return self.variant.search(query, top_k)

    def close(self) -> None:
        self.variant.close()


class BlooRecallSystem:
    """One BlooRecall ranking configuration over one (shared) index."""

    def __init__(
        self,
        config: Dict[str, Any],
        system_id: str,
        *,
        policy_name: str,
        embed_query: bool,
        chunker: str = "headings",
        corpus_root: Optional[Path] = None,
    ) -> None:
        if chunker == "plain":
            config = plain_variant_config(config)
        self.config = config
        self.corpus_root = corpus_root
        self.system_id = system_id
        self.policy_name = policy_name
        self.embed_query = embed_query
        self.chunker = chunker
        self.embedder: Optional[OllamaEmbedder] = None
        self.index: Optional[BlooRecallIndex] = None
        self.policy: Dict[str, Any] = {}

    def setup(self, fresh: bool = False, embedder: Any = None) -> Dict[str, Any]:
        if fresh or not index_path(self.config).exists():
            summary = build_index(self.config, fresh=True, embedder=embedder)
        else:
            summary = {"elapsed_seconds": 0.0, "reused_existing": True}
        self.embedder = (
            (embedder or OllamaEmbedder.from_config(self.config)) if self.embed_query else None
        )
        self.index = BlooRecallIndex(index_path(self.config))
        from bloorecall.config import active_policy

        self.policy = active_policy(self.config, self.policy_name)
        return summary

    def search(self, query: str, top_k: int = 10) -> List[str]:
        assert self.index is not None
        vector = None
        if self.embed_query:
            assert self.embedder is not None
            vector = self.embedder.embed_one(query)
        policy = dict(self.policy)
        policy["top_k"] = top_k
        rows = self.index.rank(query, vector, policy)
        results = []
        for row in rows:
            absolute = Path(row["path"])
            base = self.corpus_root
            if base is None:
                for root in self.config["corpus_roots"]:
                    root_path = Path(root["path"])
                    if absolute.is_relative_to(root_path):
                        base = root_path
                        break
            if base is not None and absolute.is_relative_to(base):
                results.append(f"{CORPUS_PREFIX}/{absolute.relative_to(base).as_posix()}")
        return results

    def close(self) -> None:
        self.index = None
        self.embedder = None


def make_systems(config: Dict[str, Any], corpus_root: Path) -> Dict[str, Any]:
    """All systems, keyed by id. Index build sharing happens in the runner."""
    resolved = resolve_config(config, corpus_root)
    return {
        "grep": GrepSystem(resolved, "grep", corpus_root),
        "filename": GrepSystem(resolved, "filename", corpus_root),
        "bm25": BlooRecallSystem(
            resolved, "bm25", policy_name="bench-bm25", embed_query=False, corpus_root=corpus_root
        ),
        "dense": BlooRecallSystem(
            resolved, "dense", policy_name="bench-dense", embed_query=True, corpus_root=corpus_root
        ),
        "hybrid": BlooRecallSystem(
            resolved, "hybrid", policy_name="baseline-v0", embed_query=True, corpus_root=corpus_root
        ),
        "hybrid-noheadings": BlooRecallSystem(
            resolved, "hybrid-noheadings", policy_name="baseline-v0", embed_query=True,
            chunker="plain", corpus_root=corpus_root,
        ),
        "hybrid-norerank": BlooRecallSystem(
            resolved, "hybrid-norerank", policy_name="bench-norerank", embed_query=True,
            corpus_root=corpus_root,
        ),
        "hybrid-norecency": BlooRecallSystem(
            resolved, "hybrid-norecency", policy_name="bench-norecency", embed_query=True,
            corpus_root=corpus_root,
        ),
    }


# Indexes are shared across BlooRecall variants: one headings index serves
# bm25/dense/hybrid/hybrid-norerank; the plain index serves hybrid-noheadings.
def index_key_for(system_id: str) -> str:
    return "plain" if system_id == "hybrid-noheadings" else "main"
