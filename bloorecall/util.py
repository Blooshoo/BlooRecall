from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_./:-]*", re.IGNORECASE)


def tokens(text: str) -> list[str]:
    """Tokenizer shared with the v0 lab; changing it invalidates index comparability."""
    return [token.casefold() for token in TOKEN_RE.findall(text)]


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
