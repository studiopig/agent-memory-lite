"""Semantic and keyword search for agent memory."""

import json
import re
from typing import Optional

from .storage import Storage, MemoryResult


class Searcher:
    """Memory search with semantic (embedding) and keyword modes."""

    def __init__(self, model_name: str, storage: Storage):
        self.model_name = model_name
        self.storage = storage
        self._model = None

    def _get_model(self):
        """Lazy-load embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers required for semantic search. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def semantic_search(self, query: str, top_k: int = 5, tags: list = None) -> list:
        """Semantic search using embeddings.

        Embeddings are cached in the SQLite database so they are
        computed only once per memory, then reused on subsequent searches.
        """
        model = self._get_model()
        memories = self.storage.get_all()

        # Filter by tags
        if tags:
            tag_set = set(tags)
            memories = [m for m in memories if tag_set & set(m.tags)]

        if not memories:
            return []

        # Compute query embedding
        query_emb = model.encode([query])[0]

        # Load or compute memory embeddings (cached in SQLite)
        memory_embs = []
        for m in memories:
            emb = self.storage.get_embedding(m.id)
            if emb is None:
                emb = model.encode([m.content])[0]
                self.storage.save_embedding(m.id, emb)
            memory_embs.append(emb)

        # Cosine similarity
        import numpy as np
        scores = [
            float(np.dot(query_emb, mem_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(mem_emb) + 1e-8))
            for mem_emb in memory_embs
        ]

        # Sort and top-k
        results = [
            MemoryResult(
                id=m.id, content=m.content, score=s,
                tags=m.tags, importance=m.importance, created_at=m.created_at,
            )
            for m, s in zip(memories, scores)
        ]
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def keyword_search(self, query: str, top_k: int = 5, tags: list = None) -> list:
        """Keyword/regex-based search."""
        memories = self.storage.get_all()

        if tags:
            tag_set = set(tags)
            memories = [m for m in memories if tag_set & set(m.tags)]

        results = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        for m in memories:
            matches = len(pattern.findall(m.content))
            if matches > 0:
                score = min(1.0, matches / max(len(m.content.split()), 1) * 10 + m.importance * 0.3)
                results.append(
                    MemoryResult(
                        id=m.id, content=m.content, score=score,
                        tags=m.tags, importance=m.importance, created_at=m.created_at,
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
