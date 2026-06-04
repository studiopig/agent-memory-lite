"""Core Memory class — save, search, prune."""

import json
import os
from typing import Optional

from .storage import Storage
from .search import Searcher
from .prune import Pruner


class Memory:
    """Lightweight long-term memory for AI agents.

    Args:
        storage: Path to SQLite database directory.
        model: Embedding model name for semantic search.
    """

    def __init__(self, storage: str = "./agent_memory", model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.storage = Storage(storage)
        self.searcher = Searcher(model, self.storage)
        self.pruner = Pruner(self.storage)

    def save(self, content: str, tags: list = None, importance: float = 0.5) -> int:
        """Save a memory entry.

        Args:
            content: The text content to remember.
            tags: Optional list of string tags.
            importance: Importance score 0.0-1.0.

        Returns:
            The ID of the saved memory.
        """
        tags = tags or []
        return self.storage.insert(content, tags, importance)

    def search(self, query: str, top_k: int = 5, mode: str = "semantic", tags: list = None) -> list:
        """Search memories.

        Args:
            query: Search query.
            top_k: Maximum results to return.
            mode: 'semantic' or 'keyword'.
            tags: Optional filter by tags.

        Returns:
            List of MemoryResult objects with .content, .score, .tags, .importance.
        """
        if mode == "semantic":
            return self.searcher.semantic_search(query, top_k, tags)
        return self.searcher.keyword_search(query, top_k, tags)

    def prune(self, keep_ratio: float = 0.8):
        """Prune low-importance memories.

        Args:
            keep_ratio: Fraction of memories to keep (0.0-1.0).
        """
        self.pruner.prune(keep_ratio)

    def stats(self) -> dict:
        """Get memory statistics."""
        return self.storage.stats()

    def clear(self):
        """Delete all memories."""
        self.storage.clear()

    def export(self) -> list:
        """Export all memories as list of dicts."""
        return self.storage.export()
