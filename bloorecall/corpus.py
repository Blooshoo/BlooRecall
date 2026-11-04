from __future__ import annotations

import fnmatch
from collections import defaultdict, deque
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .util import PROJECT_ROOT, sha256_bytes

# Secret shapes inherited from the v0 lab. A file matching any of these is never
# indexed, even if it survived the path and filename gates, and a query holding one is refused.
SECRET_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    # sk- as well as sk_: OpenAI-style keys use the hyphen.
    ("API token", re.compile(r"\b(?:sk|ghp|github_pat)[_-][A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "key or token assignment",
        re.compile(
            r"(?im)^\s*(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[=:]\s*['\"]?[A-Za-z0-9_./+-]{20,}"
        ),
    ),
]

LOCAL_OWNER_ONLY = "local_owner_only"


@dataclass(frozen=True)
class SourceFile:
    path: Path
    project: str
    root_label: str
    size: int
    mtime: float


@dataclass
class WalkResult:
    sources: list[SourceFile]
    rejections: list[dict[str, str]]
    missing_roots: list[str]
    covered_roots: list[str]
    missing_labels: list[str]
    # Roots holding more indexable files than their max_files: {root, label, files, max_files}.
    over_budget: list[dict[str, Any]]


def printable(path: Path) -> str:
    """A path as text that survives JSON and SQLite, even when its name is not valid UTF-8."""
    return str(path).encode("utf-8", "backslashreplace").decode("utf-8")


class Exclusions:
    def __init__(self, config: dict[str, Any]) -> None:
        raw = config["exclusions"]
        self.path_parts = {part.casefold() for part in raw.get("denied_path_parts", [])}
        self.name_fragments = tuple(fragment.casefold() for fragment in raw.get("denied_name_fragments", []))
        self.globs = tuple(raw.get("denied_globs", []))
        self.allowed_extensions = {suffix.casefold() for suffix in config["allowed_extensions"]}
        self.max_file_bytes = int(config.get("max_file_bytes", 262144))

    def directory_denied(self, name: str) -> bool:
        return name.casefold() in self.path_parts or name.startswith(".")

    def reject_reason(self, path: Path) -> str | None:
        # Extension first: it discards most of the tree and keeps the rejection log
        # about genuine safety decisions rather than source files we never wanted.
        if path.suffix.casefold() not in self.allowed_extensions:
            return "extension not allowlisted"
        try:
            str(path).encode("utf-8")
        except UnicodeEncodeError:
            return "file name is not valid UTF-8"
        # .openclaw is the existing workspace infrastructure ancestor, not a corpus subtree.
        if any(part.startswith(".") and part != ".openclaw" for part in path.parts):
            return "hidden path segment"
        denied = {part.casefold() for part in path.parts} & self.path_parts
        if denied:
            return f"denied path segment: {sorted(denied)[0]}"
        name = path.name.casefold()
        if any(fragment in name for fragment in self.name_fragments):
            return "sensitive filename"
        as_text = str(path)
        if any(fnmatch.fnmatch(as_text, pattern) for pattern in self.globs):
            return "denied glob"
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            return "symlink source"
        try:
            resolved = path.resolve()
        except OSError:
            return "unresolvable path"
        if resolved == PROJECT_ROOT or PROJECT_ROOT in resolved.parents:
            return "bloorecall self-ingestion"
        return None


def _walk_root(
    root: Path,
    exclusions: Exclusions,
    max_depth: int = 0,
    pruned: list[dict[str, str]] | None = None,
) -> Iterator[Path]:
    """max_depth 0 means unlimited; 1 means files directly under the root only."""
    if root.is_symlink() or exclusions.directory_denied(root.name):
        return
    if root.is_file():
        yield root
        return
    for current, directories, filenames in os.walk(root, onerror=lambda _error: None):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        if max_depth and depth >= max_depth - 1:
            directories[:] = []
        else:
            keep: list[str] = []
            for name in sorted(directories):
                if exclusions.directory_denied(name) or (current_path / name).is_symlink():
                    if pruned is not None and not name.startswith("."):
                        pruned.append(
                            {
                                "path": printable(current_path / name),
                                "reason": f"denied path segment: {name.casefold()}",
                            }
                        )
                    continue
                keep.append(name)
            directories[:] = keep
        for filename in sorted(filenames):
            yield current_path / filename


def _project_label(path: Path, root: Path, root_label: str) -> str:
    """Stable, human-meaningful bucket: root label plus the first directory under it."""
    if root.is_file():
        return root_label
    try:
        relative = path.relative_to(root)
    except ValueError:
        return root_label
    if len(relative.parts) > 1:
        return f"{root_label}/{relative.parts[0]}"
    return root_label


def _balanced(sources: list[SourceFile], root: Path, limit: int, per_project: int) -> tuple[list[SourceFile], list[SourceFile]]:
    """Round-robin first-level projects/worktrees; safe locators consume quotas too."""
    groups: dict[str, list[SourceFile]] = defaultdict(list)
    for source in sources:
        groups[source.project].append(source)

    def order(source: SourceFile) -> tuple:
        rel = source.path.relative_to(root.resolve())
        name = source.path.name.casefold()
        locator = len(rel.parts) <= 2 and (name in {"readme.md", "agents.md", "state.md"}
                    or "handoff" in name or "next-push" in name)
        shallow_doc = len(rel.parts) <= 3 and len(rel.parts) > 1 and rel.parts[-2] in {"docs", "specs"}
        return (not locator, not shallow_doc, -source.mtime, str(source.path))

    queues = {key: deque(sorted(rows, key=order)[:per_project]) for key, rows in sorted(groups.items())}
    selected: list[SourceFile] = []
    while queues and (not limit or len(selected) < limit):
        for key in list(queues):
            if limit and len(selected) >= limit:
                break
            selected.append(queues[key].popleft())
            if not queues[key]:
                del queues[key]
    kept = {item.path for item in selected}
    return selected, [item for item in sources if item.path not in kept]


def walk_corpus(config: dict[str, Any]) -> WalkResult:
    exclusions = Exclusions(config)
    sources: list[SourceFile] = []
    rejections: list[dict[str, str]] = []
    missing_roots: list[str] = []
    covered_roots: list[str] = []
    missing_labels: list[str] = []
    over_budget: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for entry in config["corpus_roots"]:
        root = Path(entry["path"]).expanduser()
        label = entry.get("label") or root.name
        if not root.exists():
            missing_roots.append(str(root))
            missing_labels.append(label)
            continue
        covered_roots.append(str(root.resolve()))
        accepted: list[SourceFile] = []
        for path in _walk_root(root, exclusions, int(entry.get("max_depth", 0) or 0), rejections):
            relative_parts = path.relative_to(root).parts if root.is_dir() else (path.name,)
            if any(part.startswith(".") for part in relative_parts):
                continue
            reason = exclusions.reject_reason(path)
            if reason:
                if reason != "extension not allowlisted":
                    rejections.append({"path": printable(path), "reason": reason})
                continue
            try:
                stat = path.stat()
            except OSError:
                rejections.append({"path": str(path), "reason": "unreadable metadata"})
                continue
            if stat.st_size == 0:
                rejections.append({"path": str(path), "reason": "empty file"})
                continue
            if stat.st_size > exclusions.max_file_bytes:
                rejections.append({"path": str(path), "reason": "over max_file_bytes"})
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            accepted.append(
                SourceFile(
                    path=resolved,
                    project=_project_label(resolved, root.resolve(), label),
                    root_label=label,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                )
            )
        limit = int(entry.get("max_files", 0) or 0)
        if entry.get("selection", "newest") == "balanced":
            if limit and len(accepted) > limit:
                over_budget.append({"root": str(root), "label": label, "files": len(accepted), "max_files": limit})
            accepted, dropped = _balanced(accepted, root, limit, int(entry.get("max_files_per_project", 200)))
            for item in dropped:
                rejections.append({"path": str(item.path), "reason": "over balanced project/root budget"})
        if limit and len(accepted) > limit:
            # Keep the freshest files when a root exceeds its budget.
            over_budget.append({"root": str(root), "label": label, "files": len(accepted), "max_files": limit})
            accepted.sort(key=lambda item: (-item.mtime, str(item.path)))
            for dropped in accepted[limit:]:
                rejections.append({"path": str(dropped.path), "reason": "over root max_files budget"})
            accepted = accepted[:limit]
        seen.update(item.path for item in accepted)
        sources.extend(accepted)
    sources.sort(key=lambda item: str(item.path))
    rejections.sort(key=lambda row: (row["reason"], row["path"]))
    return WalkResult(
        sources=sources,
        rejections=rejections,
        missing_roots=sorted(missing_roots),
        covered_roots=sorted(covered_roots),
        missing_labels=sorted(missing_labels),
        over_budget=over_budget,
    )


def secret_reason(text: str) -> str | None:
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return f"secret-shaped: {name}"
    return None


def read_source(path: Path) -> tuple[bytes, str] | None:
    try:
        data = path.read_bytes()
        return data, data.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def chunk_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Paragraph-packing chunker copied from the v0 lab so chunk boundaries match."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return []
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            step = max(1, max_chars - overlap_chars)
            for start in range(0, len(paragraph), step):
                piece = paragraph[start : start + max_chars].strip()
                if piece:
                    chunks.append(piece)
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            overlap = current[-overlap_chars:].strip() if overlap_chars else ""
            current = f"{overlap}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def chunk_markdown(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Heading-aware chunker for markdown: each chunk is prefixed with its heading breadcrumb.

    A paragraph like "run it this weekend" under "# DESIGN.md > ## Phased build > ### P0" is
    indexed carrying that trail, so a query about "the design doc's phase zero" matches the
    paragraph even though the words only appear in the headings. Section bodies are packed by the
    same deterministic paragraph packer as plain text, so chunk geometry is unchanged.
    """
    stack: list[tuple[int, str]] = []
    section_lines: list[str] = []
    chunks: list[str] = []

    def flush() -> None:
        body = "\n".join(section_lines).strip()
        section_lines.clear()
        if not body:
            return
        crumb = " > ".join(title for _, title in stack)
        # Reserve room for the breadcrumb line so a prefixed chunk still respects max_chars.
        budget = max(1, max_chars - (len(crumb) + 1 if crumb else 0))
        for piece in chunk_text(body, budget, overlap_chars):
            chunks.append(f"{crumb}\n{piece}" if crumb else piece)

    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, heading.group(2).strip()))
        else:
            section_lines.append(line)
    flush()
    # A file with no headings (or only front matter) still produces its plain chunks.
    return chunks or chunk_text(text, max_chars, overlap_chars)


def chunk_for_type(text: str, file_type: str, max_chars: int, overlap_chars: int) -> list[str]:
    if file_type.casefold().lstrip(".") in {"md", "markdown"}:
        return chunk_markdown(text, max_chars, overlap_chars)
    return chunk_text(text, max_chars, overlap_chars)


def chunk_id_for(canonical_path: str, ordinal: int, text_hash: str) -> str:
    return sha256_bytes(f"{canonical_path}:{ordinal}:{text_hash}".encode("utf-8"))[:24]
