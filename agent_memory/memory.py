"""Core Memory class — save, search, prune."""

import os
from typing import Optional, Union, List

from .storage import Storage
from .search import Searcher
from .prune import Pruner


# ── Validators ──────────────────────────────────────────────────

def _normalize_tags(tags: Union[List[str], str, None]) -> List[str]:
    """Normalize tags to a clean list of strings.

    Accepts None, a single string, or a list of strings.
    Raises TypeError for unsupported types.
    """
    if tags is None:
        return []
    if isinstance(tags, str):
        tag = tags.strip()
        return [tag] if tag else []
    if isinstance(tags, list):
        if not all(isinstance(t, str) for t in tags):
            raise TypeError("tags must be list[str], str, or None")
        return [t.strip() for t in tags if t.strip()]
    raise TypeError("tags must be list[str], str, or None")


def _validate_importance(importance: float) -> float:
    """Validate importance is a float in [0, 1]."""
    try:
        value = float(importance)
    except (TypeError, ValueError):
        raise TypeError("importance must be a number")
    if not 0 <= value <= 1:
        raise ValueError("importance must be between 0 and 1")
    return value


def _validate_keep_ratio(keep_ratio: float) -> float:
    """Validate keep_ratio is a float in (0, 1]."""
    try:
        value = float(keep_ratio)
    except (TypeError, ValueError):
        raise TypeError("keep_ratio must be a number")
    if not 0 < value <= 1:
        raise ValueError("keep_ratio must be in (0, 1]")
    return value


def _validate_top_k(top_k: int) -> int:
    """Validate top_k is a positive integer."""
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    return top_k


def _validate_mode(mode: str) -> str:
    """Validate mode is 'semantic' or 'keyword'."""
    if mode not in ("semantic", "keyword"):
        raise ValueError("mode must be 'semantic' or 'keyword'")
    return mode


def _validate_non_empty(content: str, name: str = "content") -> str:
    """Validate string is non-empty after stripping."""
    cleaned = (content or "").strip()
    if not cleaned:
        raise ValueError(f"{name} must not be empty")
    return cleaned


# ── Main class ──────────────────────────────────────────────────

class Memory:
    """Lightweight long-term memory for AI agents.

    Args:
        storage: Path to SQLite database directory.
        model: Embedding model name for semantic search.
    """

    def __init__(self, storage: str = "./agent_memory",
                 model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.storage = Storage(storage)
        self.searcher = Searcher(model, self.storage)
        self.pruner = Pruner(self.storage)

    def save(self, content: str, tags: Union[List[str], str, None] = None,
             importance: float = 0.5) -> int:
        """Save a memory entry.

        Args:
            content: Text content to remember (non-empty).
            tags: Optional tags — str, list[str], or None.
            importance: Importance score in [0, 1].

        Returns:
            Memory ID.

        Raises:
            ValueError: If content is empty or importance out of range.
            TypeError: If tags is an unsupported type.
        """
        content = _validate_non_empty(content, "content")
        tags = _normalize_tags(tags)
        importance = _validate_importance(importance)
        return self.storage.insert(content, tags, importance)

    def search(self, query: str, top_k: int = 5, mode: str = "semantic",
               tags: Union[List[str], str, None] = None) -> list:
        """Search memories.

        Args:
            query: Search query (non-empty).
            top_k: Max results (positive int).
            mode: 'semantic' or 'keyword'.
            tags: Optional tag filter.

        Returns:
            List of MemoryResult objects.

        Raises:
            ValueError: On invalid query, top_k, or mode.
            TypeError: On invalid tags type.
        """
        query = _validate_non_empty(query, "query")
        top_k = _validate_top_k(top_k)
        mode = _validate_mode(mode)
        tags = _normalize_tags(tags)

        if mode == "semantic":
            return self.searcher.semantic_search(query, top_k, tags)
        return self.searcher.keyword_search(query, top_k, tags)

    def prune(self, keep_ratio: float = 0.8):
        """Prune low-importance memories.

        Args:
            keep_ratio: Fraction of memories to keep in (0, 1].

        Raises:
            ValueError: If keep_ratio is out of range.
        """
        keep_ratio = _validate_keep_ratio(keep_ratio)
        self.pruner.prune(keep_ratio)

    def stats(self) -> dict:
        """Get memory statistics."""
        return self.storage.stats()

    def clear(self):
        """Delete all memories (including embeddings)."""
        self.storage.clear()

    def export(self) -> list:
        """Export all memories as list of dicts."""
        return self.storage.export()

    def get(self, memory_id: int):
        """Retrieve a single memory by ID.

        Args:
            memory_id: The memory ID.

        Returns:
            MemoryResult or None if not found.
        """
        results = self.storage.get_by_ids([memory_id])
        return results[0] if results else None

    def delete(self, memory_id: int):
        """Delete a single memory by ID.

        Args:
            memory_id: The memory ID to delete.
        """
        self.storage.delete_by_ids([memory_id])

    def close(self):
        """Close resources (no-op for SQLite)."""
        self.storage.close()
