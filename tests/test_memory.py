"""Tests for agent-memory-lite — validators, CRUD, prune, edge cases."""

import os
import shutil
import tempfile

import pytest
from agent_memory import Memory
from agent_memory.memory import (
    _normalize_tags,
    _validate_importance,
    _validate_keep_ratio,
    _validate_mode,
    _validate_non_empty,
    _validate_top_k,
)
from agent_memory.prune import Pruner
from agent_memory.storage import Storage


# ═════════════════════════════════════════════════════════════════
#  normalize_tags
# ═════════════════════════════════════════════════════════════════

def test_tags_none():
    assert _normalize_tags(None) == []

def test_tags_str():
    assert _normalize_tags("hello") == ["hello"]

def test_tags_str_whitespace():
    assert _normalize_tags("  hello  ") == ["hello"]

def test_tags_empty_str():
    assert _normalize_tags("") == []

def test_tags_whitespace_str():
    assert _normalize_tags("   ") == []

def test_tags_list():
    assert _normalize_tags(["a", "b"]) == ["a", "b"]

def test_tags_list_whitespace():
    assert _normalize_tags([" a ", " b "]) == ["a", "b"]

def test_tags_int_raises():
    with pytest.raises(TypeError):
        _normalize_tags(123)

def test_tags_list_int_raises():
    with pytest.raises(TypeError):
        _normalize_tags([1, 2, 3])


# ═════════════════════════════════════════════════════════════════
#  validate_importance
# ═════════════════════════════════════════════════════════════════

def test_importance_valid():
    assert _validate_importance(0.5) == 0.5

def test_importance_zero():
    assert _validate_importance(0) == 0

def test_importance_one():
    assert _validate_importance(1) == 1

def test_importance_negative_raises():
    with pytest.raises(ValueError):
        _validate_importance(-0.1)

def test_importance_over_one_raises():
    with pytest.raises(ValueError):
        _validate_importance(1.5)

def test_importance_str_raises():
    with pytest.raises(TypeError):
        _validate_importance("high")


# ═════════════════════════════════════════════════════════════════
#  validate_keep_ratio
# ═════════════════════════════════════════════════════════════════

def test_keep_ratio_valid():
    assert _validate_keep_ratio(0.8) == 0.8

def test_keep_ratio_one():
    assert _validate_keep_ratio(1) == 1

def test_keep_ratio_near_zero():
    assert _validate_keep_ratio(0.01) == 0.01

def test_keep_ratio_zero_raises():
    with pytest.raises(ValueError):
        _validate_keep_ratio(0)

def test_keep_ratio_negative_raises():
    with pytest.raises(ValueError):
        _validate_keep_ratio(-0.5)


# ═════════════════════════════════════════════════════════════════
#  validate_top_k
# ═════════════════════════════════════════════════════════════════

def test_top_k_valid():
    assert _validate_top_k(5) == 5

def test_top_k_zero_raises():
    with pytest.raises(ValueError):
        _validate_top_k(0)

def test_top_k_negative_raises():
    with pytest.raises(ValueError):
        _validate_top_k(-1)


# ═════════════════════════════════════════════════════════════════
#  validate_mode
# ═════════════════════════════════════════════════════════════════

def test_mode_semantic():
    assert _validate_mode("semantic") == "semantic"

def test_mode_keyword():
    assert _validate_mode("keyword") == "keyword"

def test_mode_invalid_raises():
    with pytest.raises(ValueError):
        _validate_mode("fuzzy")


# ═════════════════════════════════════════════════════════════════
#  validate_non_empty
# ═════════════════════════════════════════════════════════════════

def test_content_valid():
    assert _validate_non_empty("hello") == "hello"

def test_content_whitespace_trim():
    assert _validate_non_empty("  hello  ") == "hello"

def test_content_empty_raises():
    with pytest.raises(ValueError):
        _validate_non_empty("")

def test_content_whitespace_raises():
    with pytest.raises(ValueError):
        _validate_non_empty("   ")


# ═════════════════════════════════════════════════════════════════
#  Memory CRUD integration
# ═════════════════════════════════════════════════════════════════

@pytest.fixture
def mem():
    tmpdir = tempfile.mkdtemp(prefix="memtest_")
    m = Memory(storage=tmpdir)
    yield m
    m.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_save_returns_unique_ids(mem):
    id1 = mem.save("content A", importance=0.8)
    id2 = mem.save("content B", importance=0.9)
    assert id1 != id2
    assert id1 > 0 and id2 > 0


def test_save_empty_raises(mem):
    with pytest.raises(ValueError):
        mem.save("")


def test_save_importance_out_of_range_raises(mem):
    with pytest.raises(ValueError):
        mem.save("test", importance=2.0)


def test_keyword_search(mem):
    mem.save("Python programming", tags=["python"], importance=0.8)
    mem.save("Machine learning", tags=["ml"], importance=0.9)
    results = mem.search("python", mode="keyword")
    assert len(results) == 1
    assert "Python" in results[0].content


def test_search_empty_query_raises(mem):
    with pytest.raises(ValueError):
        mem.search("")


def test_search_invalid_mode_raises(mem):
    with pytest.raises(ValueError):
        mem.search("test", mode="invalid")


def test_search_invalid_top_k_raises(mem):
    with pytest.raises(ValueError):
        mem.search("test", top_k=0)


def test_tag_filter(mem):
    mem.save("Python", tags=["lang"], importance=0.5)
    mem.save("React", tags=["frontend"], importance=0.5)
    results = mem.search("Python", mode="keyword", tags="lang")
    assert all("lang" in r.tags for r in results)


def test_get_by_id(mem):
    mid = mem.save("hello world")
    result = mem.get(mid)
    assert result is not None
    assert result.content == "hello world"


def test_get_nonexistent(mem):
    assert mem.get(99999) is None


def test_delete(mem):
    mid = mem.save("delete me")
    mem.delete(mid)
    assert mem.get(mid) is None


def test_stats(mem):
    mem.save("a", importance=0.5)
    mem.save("b", importance=0.5)
    s = mem.stats()
    assert s["total"] == 2


def test_export(mem):
    mem.save("a")
    mem.save("b")
    data = mem.export()
    assert len(data) == 2


def test_clear(mem):
    mem.save("a")
    mem.save("b")
    mem.clear()
    assert mem.stats()["total"] == 0


def test_prune(mem):
    mem.save("important", importance=0.9)
    mem.save("unimportant", importance=0.1)
    mem.prune(keep_ratio=0.5)
    assert mem.stats()["total"] == 1


def test_prune_invalid_ratio_raises(mem):
    with pytest.raises(ValueError):
        mem.prune(keep_ratio=0)

    with pytest.raises(ValueError):
        mem.prune(keep_ratio=1.5)


# ═════════════════════════════════════════════════════════════════
#  Pruner: Chinese dedup
# ═════════════════════════════════════════════════════════════════

@pytest.fixture
def pruner():
    tmpdir = tempfile.mkdtemp(prefix="prune_")
    s = Storage(tmpdir)
    p = Pruner(s)
    yield p
    s.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_chinese_identical_dedup(pruner):
    sim = pruner._similarity("你好世界这是一个测试句子", "你好世界这是一个测试句子")
    assert sim > 0.9


def test_chinese_different_no_dedup(pruner):
    sim = pruner._similarity("你好世界这是一个测试句子", "完全不同的内容文本")
    assert sim < 0.9


def test_english_identical_dedup(pruner):
    sim = pruner._similarity("hello world", "hello world")
    assert sim > 0.9
