#!/usr/bin/env python3
"""End-to-end MCP check: spawn bin/bloorecall-mcp over stdio and call bloorecall_search.

Usage: python3 scripts/mcp-smoke.py "where is the bloorecall lab report"
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def main(query: str, top_k: int) -> int:
    parameters = StdioServerParameters(command=str(PROJECT_ROOT / "bin" / "bloorecall-mcp"), args=[])
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialization = await session.initialize()
            print(f"server: {initialization.serverInfo.name} {initialization.serverInfo.version}")
            tools = await session.list_tools()
            print(f"tools: {[tool.name for tool in tools.tools]}")
            result = await session.call_tool("bloorecall_search", {"query": query, "top_k": top_k})
            payload = json.loads(result.content[0].text)
            print(json.dumps(payload, indent=2, ensure_ascii=False)[:4000])
            return 0 if payload.get("results") else 1


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "where is the bloorecall v0 lab report"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    raise SystemExit(asyncio.run(main(question, count)))
