from __future__ import annotations

import json
import sqlite3
import sys
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .util import ensure_write_target

SCHEMA_VERSION = "2"

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (
    canonical_path TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    file_type TEXT NOT NULL,
    mtime REAL NOT NULL,
    byte_count INTEGER NOT NULL,
    project TEXT NOT NULL,
    root_label TEXT NOT NULL,
    permissions TEXT NOT NULL,
    chunk_count INTEGER NOT NULL,
    indexed_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    canonical_path TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    term_counts_json TEXT NOT NULL,
    embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_path_idx ON chunks(canonical_path);
CREATE TABLE IF NOT EXISTS vectors (
    text_hash TEXT NOT NULL,
    model TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    last_used REAL NOT NULL,
    PRIMARY KEY (text_hash, model)
);
"""


@dataclass
class SourceRow:
    canonical_path: str
    content_hash: str
    file_type: str
    mtime: float
    byte_count: int
    project: str
    root_label: str
    permissions: str
    chunk_count: int
    indexed_at: float


def vector_blob(vector: Iterable[float]) -> bytes:
    values = array("f", vector)
    if sys.byteorder != "little":
        values.byteswap()
    return values.tobytes()


def blob_vector(blob: bytes) -> list[float]:
    values = array("f")
    values.frombytes(blob)
    if sys.byteorder != "little":
        values.byteswap()
    return list(values)


def connect_write(path: Path) -> sqlite3.Connection:
    ensure_write_target(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.executescript(SCHEMA)
    connection.commit()
    return connection


def connect_read(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise RuntimeError(f"BlooRecall index not found at {path}; run 'bloorecall refresh' first")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def read_metadata(connection: sqlite3.Connection) -> dict[str, str]:
    return dict(connection.execute("SELECT key, value FROM metadata"))


def write_metadata(connection: sqlite3.Connection, values: dict[str, Any]) -> None:
    connection.executemany(
        "INSERT INTO metadata(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        [(key, str(value)) for key, value in values.items()],
    )


def load_sources(connection: sqlite3.Connection) -> dict[str, SourceRow]:
    rows = connection.execute(
        """SELECT canonical_path, content_hash, file_type, mtime, byte_count, project,
                  root_label, permissions, chunk_count, indexed_at FROM sources"""
    ).fetchall()
    return {row[0]: SourceRow(*row) for row in rows}


def upsert_source(connection: sqlite3.Connection, row: SourceRow) -> None:
    connection.execute(
        """INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(canonical_path) DO UPDATE SET
             content_hash=excluded.content_hash,
             file_type=excluded.file_type,
             mtime=excluded.mtime,
             byte_count=excluded.byte_count,
             project=excluded.project,
             root_label=excluded.root_label,
             permissions=excluded.permissions,
             chunk_count=excluded.chunk_count,
             indexed_at=excluded.indexed_at""",
        (
            row.canonical_path,
            row.content_hash,
            row.file_type,
            row.mtime,
            row.byte_count,
            row.project,
            row.root_label,
            row.permissions,
            row.chunk_count,
            row.indexed_at,
        ),
    )


def touch_source(connection: sqlite3.Connection, canonical_path: str, mtime: float, indexed_at: float) -> None:
    connection.execute(
        "UPDATE sources SET mtime = ?, indexed_at = ? WHERE canonical_path = ?",
        (mtime, indexed_at, canonical_path),
    )


def update_source_labels(
    connection: sqlite3.Connection, canonical_path: str, project: str, root_label: str
) -> None:
    connection.execute(
        "UPDATE sources SET project = ?, root_label = ? WHERE canonical_path = ?",
        (project, root_label, canonical_path),
    )


def delete_source(connection: sqlite3.Connection, canonical_path: str) -> None:
    connection.execute("DELETE FROM chunks WHERE canonical_path = ?", (canonical_path,))
    connection.execute("DELETE FROM sources WHERE canonical_path = ?", (canonical_path,))


def replace_chunks(connection: sqlite3.Connection, canonical_path: str, rows: list[tuple[Any, ...]]) -> None:
    connection.execute("DELETE FROM chunks WHERE canonical_path = ?", (canonical_path,))
    connection.executemany("INSERT OR REPLACE INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)


def chunk_row(
    chunk_id: str,
    canonical_path: str,
    ordinal: int,
    content_hash: str,
    text_hash: str,
    text: str,
    token_count: int,
    term_counts: dict[str, int],
    embedding_blob: bytes,
) -> tuple[Any, ...]:
    return (
        chunk_id,
        canonical_path,
        ordinal,
        content_hash,
        text_hash,
        text,
        token_count,
        json.dumps(term_counts, sort_keys=True, separators=(",", ":")),
        embedding_blob,
    )


def cached_vectors(connection: sqlite3.Connection, model: str, text_hashes: list[str]) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    for start in range(0, len(text_hashes), 400):
        batch = text_hashes[start : start + 400]
        placeholders = ",".join("?" for _ in batch)
        rows = connection.execute(
            f"SELECT text_hash, embedding FROM vectors WHERE model = ? AND text_hash IN ({placeholders})",
            [model, *batch],
        ).fetchall()
        found.update({row[0]: row[1] for row in rows})
    return found


def store_vectors(
    connection: sqlite3.Connection, model: str, entries: list[tuple[str, bytes, int]], now: float
) -> None:
    connection.executemany(
        """INSERT INTO vectors(text_hash, model, dimension, embedding, last_used)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(text_hash, model) DO UPDATE SET last_used=excluded.last_used""",
        [(text_hash, model, dimension, blob, now) for text_hash, blob, dimension in entries],
    )


def mark_vectors_used(connection: sqlite3.Connection, model: str, text_hashes: list[str], now: float) -> None:
    connection.executemany(
        "UPDATE vectors SET last_used = ? WHERE model = ? AND text_hash = ?",
        [(now, model, text_hash) for text_hash in text_hashes],
    )


def prune_vectors(connection: sqlite3.Connection, older_than: float) -> int:
    cursor = connection.execute("DELETE FROM vectors WHERE last_used < ?", (older_than,))
    return cursor.rowcount or 0


def load_search_rows(connection: sqlite3.Connection, allowed_permissions: set[str]) -> list[tuple[Any, ...]]:
    placeholders = ",".join("?" for _ in allowed_permissions)
    return connection.execute(
        f"""SELECT c.chunk_id, c.canonical_path, c.ordinal, c.content_hash, c.text,
                   c.token_count, c.term_counts_json, c.embedding,
                   s.mtime, s.project, s.permissions, s.file_type,
                   c.text_hash, s.indexed_at
            FROM chunks c JOIN sources s ON s.canonical_path = c.canonical_path
            WHERE s.permissions IN ({placeholders})
            ORDER BY c.canonical_path, c.ordinal""",
        sorted(allowed_permissions),
    ).fetchall()


def cached_text_hashes(connection: sqlite3.Connection, model: str) -> set[str]:
    """Return the set of text_hash values that have a cached vector for *model*.

    Used by the trust-verdict layer to decide whether a hit's embedding cache is
    still fresh rather than pruned.
    """
    rows = connection.execute(
        "SELECT text_hash FROM vectors WHERE model = ?", (model,)
    ).fetchall()
    return {row[0] for row in rows}
