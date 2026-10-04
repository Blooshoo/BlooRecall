from __future__ import annotations

import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from . import store
from .config import index_path, manifest_path
from .corpus import (
    LOCAL_OWNER_ONLY,
    chunk_id_for,
    chunk_for_type,
    chunk_text,
    read_source,
    secret_reason,
    walk_corpus,
)
from .embeddings import OllamaEmbedder
from .store import SourceRow
from .util import batched, ensure_write_target, sha256_bytes, sha256_text, stable_json, tokens

Progress = Callable[[str], None]


def _noop(_message: str) -> None:
    return None


class EmbeddingPool:
    """Embeds only chunk text that is not already cached under the active model."""

    def __init__(self, connection, embedder: OllamaEmbedder, progress: Progress) -> None:
        self.connection = connection
        self.embedder = embedder
        self.progress = progress
        self.pending: dict[str, str] = {}
        self.embedded = 0
        self.reused = 0
        self.dimension = 0

    def request(self, text_hash: str, text: str) -> None:
        self.pending.setdefault(text_hash, text)

    def resolve(self) -> dict[str, bytes]:
        if not self.pending:
            return {}
        now = time.time()
        wanted = sorted(self.pending)
        blobs = store.cached_vectors(self.connection, self.embedder.model, wanted)
        self.reused += len(blobs)
        if blobs:
            store.mark_vectors_used(self.connection, self.embedder.model, sorted(blobs), now)
        missing = [text_hash for text_hash in wanted if text_hash not in blobs]
        if missing:
            self.progress(f"embedding {len(missing)} new chunks ({len(blobs)} reused from cache)")
        for batch in batched(missing, self.embedder.batch_size):
            vectors = self.embedder.embed([self.pending[text_hash] for text_hash in batch])
            fresh: list[tuple[str, bytes, int]] = []
            for text_hash, vector in zip(batch, vectors, strict=True):
                if not self.dimension:
                    self.dimension = len(vector)
                elif len(vector) != self.dimension:
                    raise RuntimeError("embedding dimension changed mid-run; rerun with --full")
                blob = store.vector_blob(vector)
                blobs[text_hash] = blob
                fresh.append((text_hash, blob, len(vector)))
            # Commit each batch so an interrupted first build resumes from the cache
            # instead of re-embedding everything.
            store.store_vectors(self.connection, self.embedder.model, fresh, now)
            self.connection.commit()
            self.embedded += len(batch)
            self.progress(f"embedded {self.embedded}/{len(missing)}")
        if not self.dimension and blobs:
            self.dimension = len(store.blob_vector(next(iter(blobs.values()))))
        self.pending = {}
        return blobs


def refresh(
    config: dict[str, Any],
    *,
    full: bool = False,
    progress: Progress | None = None,
    embedder: OllamaEmbedder | None = None,
) -> dict[str, Any]:
    say = progress or _noop
    target = index_path(config)
    ensure_write_target(target)
    if full and target.exists():
        for suffix in ("", "-wal", "-shm"):
            candidate = Path(f"{target}{suffix}")
            if candidate.exists():
                candidate.unlink()
        say("removed existing index for a full rebuild")

    embedder = embedder or OllamaEmbedder.from_config(config)
    connection = store.connect_write(target)
    started = time.time()
    try:
        metadata = store.read_metadata(connection)
        stored_model = metadata.get("embedding_model")
        if stored_model and stored_model != embedder.model and not full:
            raise RuntimeError(
                f"index was built with '{stored_model}' but config asks for '{embedder.model}'; "
                "rerun with --full to rebuild"
            )

        say("walking corpus roots")
        walk = walk_corpus(config)
        say(f"{len(walk.sources)} candidate files, {len(walk.rejections)} rejected by gates")
        if walk.missing_roots:
            say(f"WARNING missing corpus roots (skipping deletions there): {', '.join(walk.missing_roots)}")

        known = store.load_sources(connection)
        seen: set[str] = set()
        # Seeded so every refresh summary carries the same keys, zero or not.
        stats = Counter(
            {
                "added": 0,
                "reindexed": 0,
                "touched": 0,
                "unchanged": 0,
                "removed": 0,
                "relabelled": 0,
                "secret_blocked": 0,
                "unreadable": 0,
                "empty_after_chunking": 0,
                "orphan_kept": 0,
                "vectors_pruned": 0,
            }
        )
        pool = EmbeddingPool(connection, embedder, say)
        # (canonical_path, ordinal, text_hash, text, content_hash) awaiting a vector
        staged: list[tuple[str, int, str, str, str]] = []
        staged_sources: dict[str, SourceRow] = {}

        for source in walk.sources:
            canonical = str(source.path)
            seen.add(canonical)
            previous = known.get(canonical)
            if (
                previous
                and not full
                and previous.byte_count == source.size
                and abs(previous.mtime - source.mtime) < 1e-6
            ):
                stats["unchanged"] += 1
                if previous.project != source.project or previous.root_label != source.root_label:
                    store.update_source_labels(connection, canonical, source.project, source.root_label)
                    stats["relabelled"] += 1
                continue
            payload = read_source(source.path)
            if payload is None:
                stats["unreadable"] += 1
                if previous:
                    store.delete_source(connection, canonical)
                    stats["removed"] += 1
                continue
            data, text = payload
            reason = secret_reason(text)
            if reason:
                stats["secret_blocked"] += 1
                walk.rejections.append({"path": canonical, "reason": reason})
                if previous:
                    store.delete_source(connection, canonical)
                    stats["removed"] += 1
                continue
            content_hash = sha256_bytes(data)
            if previous and previous.content_hash == content_hash and not full:
                store.touch_source(connection, canonical, source.mtime, started)
                if previous.project != source.project or previous.root_label != source.root_label:
                    store.update_source_labels(connection, canonical, source.project, source.root_label)
                stats["touched"] += 1
                continue

            # Opt-in ablation switch (benchmark-only; default "" keeps the shipped
            # chunker): chunker_override="plain" indexes even Markdown with the
            # paragraph packer, losing heading breadcrumbs.
            chunker_override = str(config.get("chunker_override") or "")
            if chunker_override and chunker_override != "plain":
                raise ValueError(f"unknown chunker_override: {chunker_override}")
            pieces = (
                chunk_text(text, int(config["chunk_chars"]), int(config["chunk_overlap_chars"]))
                if chunker_override == "plain"
                else chunk_for_type(
                    text,
                    source.path.suffix,
                    int(config["chunk_chars"]),
                    int(config["chunk_overlap_chars"]),
                )
            )
            if not pieces:
                stats["empty_after_chunking"] += 1
                if previous:
                    store.delete_source(connection, canonical)
                    stats["removed"] += 1
                continue
            for ordinal, piece in enumerate(pieces):
                text_hash = sha256_text(piece)
                pool.request(text_hash, piece)
                staged.append((canonical, ordinal, text_hash, piece, content_hash))
            staged_sources[canonical] = SourceRow(
                canonical_path=canonical,
                content_hash=content_hash,
                file_type=source.path.suffix.casefold().lstrip("."),
                mtime=source.mtime,
                byte_count=len(data),
                project=source.project,
                root_label=source.root_label,
                permissions=LOCAL_OWNER_ONLY,
                chunk_count=len(pieces),
                indexed_at=started,
            )
            stats["reindexed" if previous else "added"] += 1

        blobs = pool.resolve()
        by_path: dict[str, list[tuple[Any, ...]]] = {}
        for canonical, ordinal, text_hash, piece, content_hash in staged:
            term_counts = Counter(tokens(piece))
            by_path.setdefault(canonical, []).append(
                store.chunk_row(
                    chunk_id=chunk_id_for(canonical, ordinal, text_hash),
                    canonical_path=canonical,
                    ordinal=ordinal,
                    content_hash=content_hash,
                    text_hash=text_hash,
                    text=piece,
                    token_count=sum(term_counts.values()),
                    term_counts=dict(term_counts),
                    embedding_blob=blobs[text_hash],
                )
            )
        for canonical, rows in by_path.items():
            store.replace_chunks(connection, canonical, rows)
            store.upsert_source(connection, staged_sources[canonical])

        covered = tuple(walk.covered_roots)
        for canonical in sorted(set(known) - seen):
            if not any(canonical == root or canonical.startswith(f"{root}/") for root in covered):
                stats["orphan_kept"] += 1
                continue
            store.delete_source(connection, canonical)
            stats["removed"] += 1

        retention_days = float(config.get("vector_cache_days", 14))
        stats["vectors_pruned"] = store.prune_vectors(connection, started - retention_days * 86400)

        manifest_rows = _manifest_rows(connection)
        manifest_digest = sha256_text("\n".join(stable_json(row) for row in manifest_rows))
        chunk_count = int(connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
        dimension = pool.dimension or int(metadata.get("embedding_dimension", 0) or 0)
        store.write_metadata(
            connection,
            {
                "schema_version": store.SCHEMA_VERSION,
                "index_format": config["index_format"],
                "parse_version": config["parse_version"],
                "embedding_model": embedder.model,
                "embedding_dimension": dimension,
                "chunk_count": chunk_count,
                "source_count": len(manifest_rows),
                "manifest_sha256": manifest_digest,
                "chunk_chars": config["chunk_chars"],
                "chunk_overlap_chars": config["chunk_overlap_chars"],
                "float_encoding": "little-endian-float32",
                "refreshed_at": started,
                "config_path": config.get("_config_path", ""),
            },
        )
        connection.commit()
    finally:
        connection.close()

    _write_manifest(manifest_path(config), manifest_rows)
    _write_rejections(manifest_path(config).with_name("rejections.jsonl"), walk.rejections)

    summary = {
        "index_path": str(target),
        "manifest_path": str(manifest_path(config)),
        "manifest_sha256": manifest_digest,
        "embedding_model": embedder.model,
        "embedding_dimension": dimension,
        "source_count": len(manifest_rows),
        "chunk_count": chunk_count,
        "chunks_embedded": pool.embedded,
        "chunks_reused_from_cache": pool.reused,
        "rejected_count": len(walk.rejections),
        "missing_roots": walk.missing_roots,
        "elapsed_seconds": round(time.time() - started, 3),
        **{key: int(value) for key, value in sorted(stats.items())},
    }
    return summary


def _manifest_rows(connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """SELECT canonical_path, content_hash, file_type, mtime, byte_count, project,
                  root_label, permissions, chunk_count
           FROM sources ORDER BY canonical_path"""
    ).fetchall()
    return [
        {
            "canonical_path": row[0],
            "content_hash": row[1],
            "file_type": row[2],
            "mtime": row[3],
            "byte_count": row[4],
            "project": row[5],
            "root_label": row[6],
            "permissions": row[7],
            "chunk_count": row[8],
        }
        for row in rows
    ]


def _write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_write_target(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(stable_json(row) + "\n")


def _write_rejections(path: Path, rows: list[dict[str, str]]) -> None:
    ensure_write_target(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in sorted(rows, key=lambda item: (item["reason"], item["path"])):
            handle.write(stable_json(row) + "\n")
