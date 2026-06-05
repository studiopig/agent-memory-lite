"""Edge-case and regression tests — catches bugs missed by happy-path tests."""

import os
import shutil
import tempfile

import pytest
from agent_memory import Memory
from agent_memory.storage import MemoryResult


# ═════════════════════════════════════════════════════════════════
#  Edge: MemoryResult
# ═════════════════════════════════════════════════════════════════

def test_result_str():
    r = MemoryResult(id=1, content="hello", score=0.95, tags=[], importance=0.5, created_at=0)
    assert str(r) == "hello"

def test_result_eq():
    r1 = MemoryResult(id=1, content="a", score=0.5, tags=[], importance=0.5, created_at=0)
    r2 = MemoryResult(id=1, content="b", score=0.9, tags=[], importance=0.5, created_at=0)
    r3 = MemoryResult(id=2, content="a", score=0.5, tags=[], importance=0.5, created_at=0)
    assert r1 == r2  # same id
    assert r1 != r3  # different id
    assert r1 != "not a result"  # different type

def test_result_repr():
    r = MemoryResult(id=42, content="x", score=0.123, tags=[], importance=0.5, created_at=0)
    assert "id=42" in repr(r)
    assert "0.12" in repr(r)


# ═════════════════════════════════════════════════════════════════
#  Edge: Memory API surface
# ═════════════════════════════════════════════════════════════════

@pytest.fixture
def mem():
    tmpdir = tempfile.mkdtemp(prefix="edge_")
    m = Memory(storage=tmpdir)
    yield m
    m.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_save_with_string_tags(mem):
    """save should accept a single string as tags and auto-wrap it."""
    mid = mem.save("test", tags="single")
    r = mem.get(mid)
    assert r.tags == ["single"]


def test_save_with_none_tags(mem):
    """Verify default tags=None works (README now says tags=None)."""
    mid = mem.save("test")
    r = mem.get(mid)
    assert r.tags == []


def test_save_with_emoji(mem):
    """Unicode emoji should be preserved."""
    mid = mem.save("你好 🌍 🚀 test")
    r = mem.get(mid)
    assert "🌍" in r.content
    assert "🚀" in r.content


def test_search_empty_db(mem):
    """Searching empty DB should return empty list, not crash."""
    results = mem.search("anything", mode="keyword")
    assert results == []


def test_keyword_search_case_insensitive(mem):
    mem.save("PYTHON", importance=0.5)
    results = mem.search("python", mode="keyword")
    assert len(results) == 1


def test_keyword_search_with_regex_chars(mem):
    """Regex special chars should be escaped (literal substring match)."""
    mem.save("hello.world", importance=0.5)
    mem.save("helloXworld", importance=0.5)
    results = mem.search("hello.world", mode="keyword")
    # Should match "hello.world" only, not "helloXworld"
    contents = [r.content for r in results]
    assert "hello.world" in contents
    assert "helloXworld" not in contents


def test_delete_nonexistent_is_noop(mem):
    """Deleting non-existent ID should not crash."""
    mem.delete(99999)


def test_prune_empty_db(mem):
    """Pruning empty DB should not crash."""
    mem.prune(keep_ratio=0.8)


def test_clear_then_use(mem):
    """After clear, save should work again."""
    mem.save("first")
    mem.clear()
    mid = mem.save("second")
    # SQLite autoincrement continues after DELETE, so mid >= 1
    r = mem.get(mid)
    assert r is not None
    assert r.content == "second"


def test_clear_then_stats(mem):
    """Stats after clear should be zero."""
    mem.save("test")
    mem.clear()
    assert mem.stats()["total"] == 0


def test_save_high_importance_boundary(mem):
    """importance=1.0 should be allowed."""
    mid = mem.save("critical", importance=1.0)
    r = mem.get(mid)
    assert r.importance == 1.0


def test_save_low_importance_boundary(mem):
    """importance=0.0 should be allowed."""
    mid = mem.save("noise", importance=0.0)
    r = mem.get(mid)
    assert r.importance == 0.0


def test_empty_tags_list(mem):
    """Explicit empty tags list should work."""
    mid = mem.save("test", tags=[])
    r = mem.get(mid)
    assert r.tags == []


def test_tags_with_empty_strings_filtered(mem):
    """Empty strings in tags list should be filtered out."""
    mid = mem.save("test", tags=["a", "", "  ", "b"])
    r = mem.get(mid)
    assert r.tags == ["a", "b"]


def test_prune_keep_all(mem):
    """keep_ratio=1.0 should keep everything."""
    mem.save("a", importance=0.5)
    mem.save("b", importance=0.5)
    mem.prune(keep_ratio=1.0)
    assert mem.stats()["total"] == 2


def test_prune_keep_one(mem):
    """keep_ratio close to 0 should keep at least 1."""
    mem.save("important", importance=1.0)
    mem.save("noise", importance=0.01)
    mem.prune(keep_ratio=0.5)
    assert mem.stats()["total"] == 1


def test_export_empty(mem):
    """Export empty DB should return []."""
    assert mem.export() == []


def test_large_content(mem):
    """Large content (10KB) should be stored and retrieved."""
    large = "x" * 10000
    mid = mem.save(large)
    r = mem.get(mid)
    assert len(r.content) == 10000
