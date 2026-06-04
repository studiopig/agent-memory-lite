"""SQLite storage backend for agent memory."""

import json
import os
import sqlite3
import time
from collections import Counter
from typing import Optional


class MemoryResult:
    """Search result object."""
    def __init__(self, id: int, content: str, score: float, tags: list, importance: float, created_at: float):
        self.id = id
        self.content = content
        self.score = score
        self.tags = tags
        self.importance = importance
        self.created_at = created_at

    def __repr__(self):
        return f"MemoryResult(id={self.id}, score={self.score:.2f})"


class Storage:
    """SQLite-backed memory persistence."""

    def __init__(self, db_path: str):
        os.makedirs(db_path, exist_ok=True)
        self.db_path = os.path.join(db_path, "memory.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    importance REAL DEFAULT 0.5,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    memory_id INTEGER PRIMARY KEY,
                    vector BLOB,
                    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
                )
            """)

    def insert(self, content: str, tags: list, importance: float) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO memories (content, tags, importance, created_at) VALUES (?, ?, ?, ?)",
                (content, json.dumps(tags), importance, time.time()),
            )
            return cursor.lastrowid

    def get_all(self) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM memories ORDER BY importance DESC").fetchall()
            return [
                MemoryResult(
                    id=r["id"], content=r["content"], score=0,
                    tags=json.loads(r["tags"]), importance=r["importance"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def get_by_ids(self, ids: list) -> list:
        if not ids:
            return []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ",".join("?" * len(ids))
            rows = conn.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders})",
                ids,
            ).fetchall()
            return [
                MemoryResult(
                    id=r["id"], content=r["content"], score=0,
                    tags=json.loads(r["tags"]), importance=r["importance"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def delete_by_ids(self, ids: list):
        if not ids:
            return
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ",".join("?" * len(ids))
            conn.execute(f"DELETE FROM memories WHERE id IN ({placeholders})", ids)

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            total_chars = conn.execute("SELECT COALESCE(SUM(LENGTH(content)), 0) FROM memories").fetchone()[0]
            tags_raw = conn.execute("SELECT tags FROM memories").fetchall()
            all_tags = []
            for (t,) in tags_raw:
                all_tags.extend(json.loads(t))
            tag_counts = Counter(all_tags).most_common(10)
            return {
                "total": total,
                "total_chars": total_chars,
                "top_tags": [t[0] for t in tag_counts],
            }

    def clear(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memories")

    def export(self) -> list:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, content, tags, importance, created_at FROM memories ORDER BY id").fetchall()
            return [
                {
                    "id": r[0], "content": r[1], "tags": json.loads(r[2]),
                    "importance": r[3], "created_at": r[4],
                }
                for r in rows
            ]
