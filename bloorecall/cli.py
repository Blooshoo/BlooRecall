from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import active_policy, index_path, load_config, manifest_path
from .util import utc_iso

DESCRIPTION = "BlooRecall v1 — local hybrid file locator (BM25 + local dense embeddings)."


def _print(message: str = "") -> None:
    print(message, file=sys.stderr)


def _relative_home(path: str) -> str:
    home = str(Path.home())
    return path.replace(home, "~", 1) if path.startswith(home) else path


def _verdict_marker(trust: dict[str, Any] | None) -> str:
    """Render the trust verdict as a single inline token for CLI output."""
    if trust is None:
        return "[no-trust]"
    verdict = trust.get("verdict", "unknown")
    label = {"strong": "OK", "rebuilt": "NEW", "weak": "DRIFT", "stale": "GONE"}.get(verdict, "?")
    return f"[{label}]"


def command_init(args: argparse.Namespace) -> int:
    from .config import config_path, default_config

    target = Path(args.config).expanduser().resolve() if args.config else config_path()
    if target.exists() and not args.force:
        _print(f"config already exists: {target} (use --force to overwrite)")
        return 1
    raw_roots = args.root or [str(Path.cwd())]
    roots: list[dict[str, Any]] = []
    for item in raw_roots:
        root = Path(item).expanduser().resolve()
        if not root.exists():
            _print(f"skipping missing root: {root}")
            continue
        roots.append({"path": str(root), "label": root.name or "root", "max_files": 4000})
    if not roots:
        _print("no usable corpus roots; pass --root <dir> (repeatable)")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(default_config(roots), indent=2) + "\n", encoding="utf-8")
    _print(f"wrote {target}")
    _print(f"roots: {', '.join(root['label'] for root in roots)}")
    _print("next: `bloorecall refresh` to build the index, then `bloorecall search \"...\"`")
    return 0


def command_search(args: argparse.Namespace) -> int:
    from .search import PrivateQueryRefused, SearchEngine

    config = load_config(args.config)
    engine = SearchEngine(config)
    try:
        payload = engine.search(
            query=args.query, top_k=args.top_k, policy_name=args.policy, project=args.project
        )
    except PrivateQueryRefused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    results = payload["results"]
    if not results:
        _print(f"no matches for {payload['query']!r}")
        return 1
    for row in results:
        print(f"{row['rank']:>2}. {row['score']:.4f}  {_relative_home(row['path'])}")
        trust = row.get("trust")
        print(
            f"    {row['project']} · {row['mtime_iso'][:10]} "
            f"· {_verdict_marker(trust)} {trust.get('reason', '')}" if trust
            else f"    {row['project']} · {row['mtime_iso'][:10]}"
        )
        print(f"    {row['snippet']}")
        print()
    index = payload["index"]
    _print(
        f"{len(results)} result(s) · policy {payload['policy']} · "
        f"{index['source_count']} files / {index['chunk_count']} chunks · "
        f"index refreshed {index['refreshed_at_iso'][:19]}Z"
    )
    if payload.get("retrieval") == "keyword-only":
        _print(f"note: keyword-only results (embeddings unavailable: {payload.get('warning', '')})")
    return 0


def command_refresh(args: argparse.Namespace) -> int:
    from .indexer import refresh

    config = load_config(args.config)
    progress = None if args.quiet else lambda message: _print(f"[bloorecall] {message}")
    summary = refresh(config, full=args.full, progress=progress)
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    print(
        f"indexed {summary['source_count']} files / {summary['chunk_count']} chunks "
        f"in {summary['elapsed_seconds']}s"
    )
    for key in ("added", "reindexed", "touched", "unchanged", "removed", "secret_blocked"):
        if summary.get(key):
            print(f"  {key}: {summary[key]}")
    print(
        f"  embeddings: {summary['chunks_embedded']} new, "
        f"{summary['chunks_reused_from_cache']} reused"
    )
    print(f"  manifest sha256: {summary['manifest_sha256']}")
    if summary["missing_roots"]:
        print(f"  WARNING missing roots: {', '.join(summary['missing_roots'])}")
    return 0


def command_status(args: argparse.Namespace) -> int:
    from . import store

    config = load_config(args.config)
    target = index_path(config)
    payload: dict[str, Any] = {
        "config_path": config["_config_path"],
        "index_path": str(target),
        "index_exists": target.exists(),
        "manifest_path": str(manifest_path(config)),
        "active_policy": active_policy(config)["policy_id"],
        "corpus_roots": [entry["path"] for entry in config["corpus_roots"]],
    }
    if target.exists():
        connection = store.connect_read(target)
        try:
            metadata = store.read_metadata(connection)
            projects = connection.execute(
                "SELECT project, COUNT(*) FROM sources GROUP BY project ORDER BY COUNT(*) DESC LIMIT 15"
            ).fetchall()
        finally:
            connection.close()
        payload["index"] = metadata
        payload["top_projects"] = [{"project": row[0], "files": row[1]} for row in projects]
        payload["refreshed_at_iso"] = utc_iso(float(metadata.get("refreshed_at", 0) or 0))
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    print(f"config      {payload['config_path']}")
    print(f"index       {payload['index_path']}")
    print(f"policy      {payload['active_policy']}")
    if not payload["index_exists"]:
        print("index       MISSING — run 'bloorecall refresh'")
        return 1
    metadata = payload["index"]
    print(f"model       {metadata.get('embedding_model')} (dim {metadata.get('embedding_dimension')})")
    print(f"content     {metadata.get('source_count')} files / {metadata.get('chunk_count')} chunks")
    print(f"refreshed   {payload['refreshed_at_iso']}")
    print(f"manifest    {metadata.get('manifest_sha256')}")
    print(f"trust       per-result disk verification enabled (strong/rebuilt/weak/stale)")
    print("projects")
    for row in payload["top_projects"]:
        print(f"  {row['files']:>5}  {row['project']}")
    return 0


def command_serve(args: argparse.Namespace) -> int:
    from .mcp_server import run_stdio

    run_stdio(args.config)
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    from . import store
    from .embeddings import OllamaEmbedder

    problems = 0
    config = load_config(args.config)
    print(f"config      OK  {config['_config_path']}")

    missing = [
        entry["path"]
        for entry in config["corpus_roots"]
        if not Path(entry["path"]).expanduser().exists()
    ]
    if missing:
        problems += 1
        print(f"roots       WARN missing: {', '.join(missing)}")
    else:
        print(f"roots       OK  {len(config['corpus_roots'])} configured")

    embedder = OllamaEmbedder.from_config(config)
    try:
        vector = embedder.embed_one("bloorecall doctor probe")
        print(f"ollama      OK  {embedder.model} → {len(vector)} dims at {embedder.endpoint}")
    except RuntimeError as error:
        problems += 1
        print(f"ollama      FAIL {error}")

    target = index_path(config)
    if not target.exists():
        problems += 1
        print(f"index       FAIL missing {target} — run 'bloorecall refresh'")
    else:
        connection = store.connect_read(target)
        try:
            metadata = store.read_metadata(connection)
        finally:
            connection.close()
        if metadata.get("embedding_model") != embedder.model:
            problems += 1
            print(
                f"index       FAIL built with {metadata.get('embedding_model')}, "
                f"config wants {embedder.model} — run 'bloorecall refresh --full'"
            )
        else:
            print(f"index       OK  {metadata.get('chunk_count')} chunks, manifest {metadata.get('manifest_sha256', '')[:12]}")

    try:
        import mcp  # noqa: F401

        print("mcp sdk     OK")
    except ImportError:
        problems += 1
        print("mcp sdk     FAIL 'mcp' package not installed — pip install --user mcp")
    return 1 if problems else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bloorecall", description=DESCRIPTION)
    parser.add_argument("--config", help="path to config.json (default: project config.json)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="write a starter config.json for your folders")
    init.add_argument(
        "--root",
        action="append",
        metavar="DIR",
        help="a folder to index (repeatable); defaults to the current directory",
    )
    init.add_argument("--force", action="store_true", help="overwrite an existing config")
    init.set_defaults(func=command_init)

    search = subparsers.add_parser("search", help="find files matching a natural-language query")
    search.add_argument("query", help="what you are looking for")
    search.add_argument("-k", "--top-k", type=int, help="number of files to return")
    search.add_argument("-p", "--project", help="only return files whose project label contains this")
    search.add_argument("--policy", help="named retrieval policy from config.json")
    search.add_argument("--json", action="store_true", help="emit JSON")
    search.set_defaults(func=command_search)

    refresh = subparsers.add_parser("refresh", help="incrementally reindex the corpus")
    refresh.add_argument("--full", action="store_true", help="discard the index and rebuild it")
    refresh.add_argument("--quiet", action="store_true", help="suppress progress output")
    refresh.add_argument("--json", action="store_true", help="emit JSON")
    refresh.set_defaults(func=command_refresh)

    status = subparsers.add_parser("status", help="show index and config state")
    status.add_argument("--json", action="store_true", help="emit JSON")
    status.set_defaults(func=command_status)

    serve = subparsers.add_parser("serve", help="run the MCP stdio server")
    serve.set_defaults(func=command_serve)

    doctor = subparsers.add_parser("doctor", help="check config, Ollama, index, and MCP deps")
    doctor.add_argument(
        "--verify-drift",
        action="store_true",
        help="also run a read-only drift audit (exits 1 on drift)",
    )
    doctor.set_defaults(func=command_doctor)

    verify = subparsers.add_parser(
        "verify", help="read-only drift audit: re-hash sources vs disk, exit 1 on drift"
    )
    verify.add_argument("--deep", action="store_true", help="re-hash every source even if mtime/size match")
    verify.add_argument("--json", action="store_true", help="emit JSON summary")
    verify.set_defaults(func=lambda args: _command_verify(args))
    return parser


def _command_verify(args: argparse.Namespace) -> int:
    """Dispatch to the standalone drift audit script."""
    from .verify_drift import run_drift_audit

    config = load_config(args.config)
    return run_drift_audit(config, deep=args.deep, as_json=args.json)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (RuntimeError, ValueError) as error:
        print(f"bloorecall: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
