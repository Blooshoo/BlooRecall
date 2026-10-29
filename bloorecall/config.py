from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .util import PROJECT_ROOT, resolve_under_project

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"
CONFIG_ENV_VAR = "BLOORECALL_CONFIG"

REQUIRED_KEYS = (
    "index_format",
    "parse_version",
    "index_path",
    "embedding",
    "corpus_roots",
    "allowed_extensions",
    "chunk_chars",
    "chunk_overlap_chars",
    "exclusions",
    "active_policy",
    "policies",
    "search_defaults",
)
POLICY_KEYS = ("dense_weight", "recency_weight", "metadata_weight", "rerank_budget", "top_k")
# How dense and BM25 evidence are combined (optional policy key "fusion").
# "rrf" fuses the two rank orders (reciprocal-rank fusion); it is scale-free, so dense_weight
# means what it says, and hybrid-rrf-v1 ships it. "raw" is the v0 score blend with cosine mapped
# to (cos+1)/2: that squeezes every chunk into a narrow band while BM25 is max-normalized to
# span [0, 1], so BM25 dominates whatever dense_weight says. "minmax" rescales the query's
# similarities to span [0, 1] before blending. A policy without the key gets "raw", so a
# policy id always names one behavior and baseline-v0's benchmark results stay reproducible.
FUSION_MODES = ("raw", "minmax", "rrf")


def config_path(explicit: str | Path | None = None) -> Path:
    """Resolution order: explicit argument, BLOORECALL_CONFIG, project config.json."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    from_env = os.environ.get(CONFIG_ENV_VAR)
    if from_env:
        return Path(from_env).expanduser().resolve()
    return DEFAULT_CONFIG_PATH


def load_config(explicit: str | Path | None = None) -> dict[str, Any]:
    path = config_path(explicit)
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError(
            f"BlooRecall config not found: {path}. Run `bloorecall init --root <dir>` to create one "
            "(or copy config.example.json and edit its corpus_roots)."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"BlooRecall config is not valid JSON ({path}): {error}") from error
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise RuntimeError(f"BlooRecall config {path} is missing keys: {', '.join(missing)}")
    _validate_corpus(data, path)
    _validate_policies(data, path)
    data["_config_path"] = str(path)
    return data


def default_config(roots: list[dict[str, Any]]) -> dict[str, Any]:
    """A complete, ready-to-edit config for `bloorecall init`, with the given corpus roots."""
    return {
        "config_version": "bloorecall-v1",
        "index_format": "bloorecall-sqlite-v2",
        "parse_version": "bloorecall-chunker-v2-headings",
        "index_path": "var/index.sqlite3",
        "embedding": {
            "model": "qwen3-embedding:0.6b",
            "endpoint": "http://127.0.0.1:11434/api/embed",
            "batch_size": 64,
            "timeout_seconds": 300,
            "keep_alive": "30m",
        },
        "corpus_roots": roots,
        "allowed_extensions": [".md", ".txt", ".rst"],
        "max_file_bytes": 262144,
        "chunk_chars": 1600,
        "chunk_overlap_chars": 180,
        "exclusions": {
            "denied_path_parts": [
                ".git", "node_modules", "site-packages", "vendor", "dist", "build",
                "coverage", "target", ".venv", "venv", "__pycache__", "backup", "backups",
                "secrets", "credentials", "memory", "memories", "sessions", "conversations",
            ],
            "denied_name_fragments": [".env", "credential", "secret", "password", "id_rsa"],
            "denied_globs": [],
        },
        "policies": {
            "hybrid-rrf-v1": {
                "policy_id": "hybrid-rrf-v1",
                "fusion": "rrf",
                "dense_weight": 0.5,
                "rrf_k": 60,
                "recency_weight": 0.05,
                "metadata_weight": 0.15,
                "rerank_budget": 20,
                "top_k": 10,
            }
        },
        "active_policy": "hybrid-rrf-v1",
        "search_defaults": {"top_k": 10, "max_top_k": 50, "snippet_chars": 240},
        "vector_cache_days": 14,
    }


def _validate_corpus(data: dict[str, Any], path: Path) -> None:
    # An empty root list would empty the index on the next refresh, and an overlap as long as
    # the chunk makes the packer step one character at a time: refuse both up front.
    roots = data["corpus_roots"]
    if not isinstance(roots, list) or not roots or not all(
        isinstance(root, dict) and root.get("path") for root in roots
    ):
        raise RuntimeError(f"corpus_roots in {path} must list at least one folder as {{\"path\": ...}}")
    size, overlap = data["chunk_chars"], data["chunk_overlap_chars"]
    if not (isinstance(size, int) and isinstance(overlap, int) and 0 <= overlap < size):
        raise RuntimeError(
            f"{path}: chunk_chars must be a positive integer and chunk_overlap_chars 0 or more, below it"
        )
    if int(data.get("max_file_bytes", 1)) < 1:
        raise RuntimeError(f"max_file_bytes in {path} must be positive")


def _validate_policies(data: dict[str, Any], path: Path) -> None:
    policies = data["policies"]
    if not isinstance(policies, dict) or not policies:
        raise RuntimeError(f"BlooRecall config {path} defines no policies")
    active = data["active_policy"]
    if active not in policies:
        raise RuntimeError(f"active_policy '{active}' is not defined in {path}")
    for name, policy in policies.items():
        missing = [key for key in POLICY_KEYS if key not in policy]
        if missing:
            raise RuntimeError(f"policy '{name}' in {path} is missing: {', '.join(missing)}")
        fusion = policy.get("fusion", "raw")
        if fusion not in FUSION_MODES:
            raise RuntimeError(
                f"policy '{name}' in {path} has fusion '{fusion}'; expected one of {', '.join(FUSION_MODES)}"
            )


def active_policy(config: dict[str, Any], override: str | None = None) -> dict[str, Any]:
    name = override or config["active_policy"]
    policies = config["policies"]
    if name not in policies:
        known = ", ".join(sorted(policies))
        raise RuntimeError(f"unknown policy '{name}'; configured policies: {known}")
    return dict(policies[name])


def index_path(config: dict[str, Any]) -> Path:
    return resolve_under_project(config["index_path"])


def manifest_path(config: dict[str, Any]) -> Path:
    return index_path(config).with_name("manifest.jsonl")
