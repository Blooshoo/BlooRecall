import os
from typing import Annotated, Any, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .config import load_config
from .search import PrivateQueryRefused, SearchEngine

INSTRUCTIONS = """BlooRecall locates files on the local machine by meaning and by keyword.

Use bloorecall_search when the question is "where is / where did I put / which file
describes X". It returns file paths with a scored snippet, not file contents — read
the returned path if you need the whole document. The index covers local docs, plans,
specs, notes and runbooks only; secrets, credential stores and private memory are
excluded by design and credential-shaped queries are refused.

Each result carries a **trust verdict** (Heimdall-style disk verification):
- **strong** — file on disk matches the indexed hash and embedding cache is fresh.
- **rebuilt** — file matches disk but was re-indexed in the most recent refresh.
- **weak** — file exists but the hash drifted or the embedding cache is stale.
- **stale** — file is missing from disk."""


def build_server(config_path: Optional[str] = None) -> FastMCP:
    config = load_config(config_path)
    engine = SearchEngine(config)
    defaults = config["search_defaults"]
    server = FastMCP(name="bloorecall", instructions=INSTRUCTIONS)

    @server.tool(
        name="bloorecall_search",
        description=(
            "Find local files by meaning and keyword. Returns ranked paths with scores, "
            "project labels, last-modified dates, matching snippets, and a per-hit "
            "trust verdict (strong/rebuilt/weak/stale) verified against disk."
        ),
    )
    def bloorecall_search(
        query: Annotated[str, Field(description="Natural-language description of the file you want")],
        top_k: Annotated[
            int, Field(description="How many files to return", ge=1, le=int(defaults.get("max_top_k", 50)))
        ] = int(defaults.get("top_k", 10)),
        project: Annotated[
            Optional[str],
            Field(description="Optional substring filter on the project label, e.g. 'notes'"),
        ] = None,
    ) -> dict[str, Any]:
        try:
            payload = engine.search(query=query, top_k=top_k, project=project)
        except PrivateQueryRefused as error:
            return {"query": query, "results": [], "refused": True, "reason": str(error)}
        except (RuntimeError, ValueError) as error:
            return {"query": query, "results": [], "error": str(error)}
        return {
            "query": payload["query"],
            "result_count": len(payload["results"]),
            "retrieval": payload["retrieval"],
            **({"warning": payload["warning"]} if "warning" in payload else {}),
            "index_refreshed_at": payload["index"]["refreshed_at_iso"],
            "results": [
                {
                    "rank": row["rank"],
                    "path": row["path"],
                    "score": row["score"],
                    "project": row["project"],
                    "modified": row["mtime_iso"][:10],
                    "snippet": row["snippet"],
                    "trust": row["trust"],
                }
                for row in payload["results"]
            ],
        }

    return server


def run_stdio(config_path: Optional[str] = None) -> None:
    build_server(config_path or os.environ.get("BLOORECALL_CONFIG")).run(transport="stdio")


if __name__ == "__main__":
    run_stdio()
