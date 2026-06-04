"""MCP Server wrapper for Agent Memory Lite.

Start with:
    agent-memory serve
    agent-memory serve --storage ./my_memories --model intfloat/multilingual-e5-small
"""

import asyncio
import json
import os
import sys
from typing import Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    raise ImportError(
        "mcp package required for MCP server mode. "
        "Install with: pip install agent-memory-lite[mcp]"
    )

from .memory import Memory


_CONFIG = {
    "storage": os.environ.get("MEMORY_STORAGE", "./agent_memory"),
    "model": os.environ.get("MEMORY_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
}


def _memory() -> Memory:
    """Get or create the Memory instance."""
    if "_instance" not in _CONFIG:
        _CONFIG["_instance"] = Memory(
            storage=_CONFIG["storage"],
            model=_CONFIG["model"],
        )
    return _CONFIG["_instance"]


# ── MCP Server ──────────────────────────────────────────────────

server = Server("agent-memory-lite")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="memory_save",
            description="Save a memory entry for the AI agent to remember",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Text content to remember"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization (e.g. ['user-pref', 'project'])",
                    },
                    "importance": {
                        "type": "number",
                        "description": "Importance score 0-1 (higher = more likely to survive pruning)",
                        "default": 0.5,
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="memory_search",
            description="Search memories — semantic (meaning-based) or keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Max results", "default": 5},
                    "mode": {
                        "type": "string",
                        "enum": ["semantic", "keyword"],
                        "description": "Search mode",
                        "default": "semantic",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="memory_get",
            description="Retrieve a single memory by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "integer", "description": "Memory ID to retrieve"},
                },
                "required": ["memory_id"],
            },
        ),
        Tool(
            name="memory_delete",
            description="Delete a single memory by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "integer", "description": "Memory ID to delete"},
                },
                "required": ["memory_id"],
            },
        ),
        Tool(
            name="memory_stats",
            description="Get memory statistics (total count, byte usage, top tags)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="memory_prune",
            description="Prune low-importance memories — keep only the top portion by importance",
            inputSchema={
                "type": "object",
                "properties": {
                    "keep_ratio": {
                        "type": "number",
                        "description": "Fraction of memories to keep (0-1]. 0.8 = keep top 80%",
                        "default": 0.8,
                    },
                },
            },
        ),
        Tool(
            name="memory_clear",
            description="⚠️ Delete ALL memories and embeddings (irreversible)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="memory_export",
            description="Export all memories as a JSON-serializable list",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    mem = _memory()

    try:
        if name == "memory_save":
            memory_id = mem.save(
                content=arguments["content"],
                tags=arguments.get("tags"),
                importance=arguments.get("importance", 0.5),
            )
            result = {"id": memory_id, "status": "saved"}

        elif name == "memory_search":
            results = mem.search(
                query=arguments["query"],
                top_k=arguments.get("top_k", 5),
                mode=arguments.get("mode", "semantic"),
                tags=arguments.get("tags"),
            )
            result = [
                {
                    "id": r.id,
                    "content": r.content,
                    "score": round(r.score, 4),
                    "tags": r.tags,
                    "importance": r.importance,
                }
                for r in results
            ]

        elif name == "memory_get":
            r = mem.get(arguments["memory_id"])
            if r is None:
                result = {"found": False, "id": arguments["memory_id"]}
            else:
                result = {
                    "found": True,
                    "id": r.id,
                    "content": r.content,
                    "tags": r.tags,
                    "importance": r.importance,
                }

        elif name == "memory_delete":
            mem.delete(arguments["memory_id"])
            result = {"id": arguments["memory_id"], "status": "deleted"}

        elif name == "memory_stats":
            result = mem.stats()

        elif name == "memory_prune":
            mem.prune(keep_ratio=arguments.get("keep_ratio", 0.8))
            stats = mem.stats()
            result = {"status": "pruned", "remaining": stats["total"]}

        elif name == "memory_clear":
            mem.clear()
            result = {"status": "cleared"}

        elif name == "memory_export":
            result = mem.export()

        else:
            raise ValueError(f"Unknown tool: {name}")

    except ValueError as e:
        result = {"error": str(e)}
    except TypeError as e:
        result = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


# ── Server entry ────────────────────────────────────────────────

async def _serve_async():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def serve(storage: str | None = None, model: str | None = None):
    """Start MCP server for Agent Memory Lite.

    Args:
        storage: Path to SQLite database directory.
        model: Embedding model name for semantic search.
    """
    if storage:
        _CONFIG["storage"] = storage
    if model:
        _CONFIG["model"] = model

    sys.stderr.write(
        f"Agent Memory Lite MCP Server starting\n"
        f"  storage: {_CONFIG['storage']}\n"
        f"  model:   {_CONFIG['model']}\n"
    )
    sys.stderr.flush()
    asyncio.run(_serve_async())


if __name__ == "__main__":
    serve()
