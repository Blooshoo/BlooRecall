from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Identifiers stay whole (retry_policy.max_attempts, ERR_QUOTA_429, docs/setup.md) but a token
# ends on a letter or digit, so a sentence's last word is the same token as anywhere else
# ("backoff." used to be its own term, which no query could match).
TOKEN_RE = re.compile(r"[a-z0-9](?:[a-z0-9_./:-]*[a-z0-9])?", re.IGNORECASE)
# Bump whenever tokens() changes: an index stamped with another version is re-tokenized from
# its stored chunk text (in memory when search loads it, on disk by the next refresh).
TOKENIZER_VERSION = "2"
WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def tokens(text: str) -> list[str]:
    """Index- and query-time tokenizer; changing it means bumping TOKENIZER_VERSION."""
    return [token.casefold() for token in TOKEN_RE.findall(text)]


def words(text: str) -> list[str]:
    """Bare alphanumeric runs: "notes/reconnect-design.md" -> notes, reconnect, design, md."""
    return [word.casefold() for word in WORD_RE.findall(text)]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def batched(items: list[Any], size: int) -> Iterator[list[Any]]:
    for start in range(0, len(items), max(1, size)):
        yield items[start : start + size]


def utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def resolve_under_project(path: str | Path) -> Path:
    """Resolve a config-relative path against the project root."""
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def ensure_write_target(path: Path) -> Path:
    """BlooRecall only ever writes inside its own project directory."""
    resolved = path.resolve()
    if not resolved.is_relative_to(PROJECT_ROOT):
        raise ValueError(f"refusing to write outside the BlooRecall project: {resolved}")
    return resolved


def iter_unique(items: Iterable[Any]) -> Iterator[Any]:
    seen: set[Any] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        yield item
