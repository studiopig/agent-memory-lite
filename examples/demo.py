"""
Agent Memory Lite — Demo Script

Demonstrates the full workflow:
    save → search (semantic + keyword) → prune → stats → export → clear

Usage:
    python examples/demo.py
"""

import os
import shutil
import tempfile
import textwrap

from agent_memory import Memory


def demo():
    db_path = tempfile.mkdtemp(prefix="memory_demo_")

    print("=" * 60)
    print("  🧠 Agent Memory Lite — Demo")
    print("=" * 60)
    print(f"  Storage: {db_path}\n")

    mem = Memory(storage=db_path)

    # ── Save ──
    print("📝 Saving memories...")
    mem.save(
        "用户偏爱简洁直接的回复风格，不喜欢冗长的铺垫和客套话",
        tags=["user-pref", "communication"],
        importance=0.95,
    )
    mem.save(
        "项目技术栈：React 18 + FastAPI + PostgreSQL + Docker，部署在阿里云 K8s",
        tags=["tech-stack", "project"],
        importance=0.90,
    )
    mem.save(
        "团队成员：张三（前端）、李四（后端）、王五（DevOps），王五 7 月离职",
        tags=["team", "project"],
        importance=0.85,
    )
    mem.save(
        "生产环境凌晨 2 点有一次 Redis 内存溢出，已通过增加 maxmemory 解决",
        tags=["incident", "production"],
        importance=0.80,
    )
    mem.save(
        "下次团建想去成都，时间大概在 9 月中旬",
        tags=["team", "social"],
        importance=0.30,
    )
    mem.save(
        "今天午饭吃的黄焖鸡，不好吃",
        tags=["personal"],
        importance=0.05,
    )
    print(f"  ✓ Saved 6 memories\n")

    # ── Semantic Search ──
    print("🔍 Semantic search: '有哪些技术栈？'")
    results = mem.search("有哪些技术栈？", top_k=3)
    for r in results:
        print(f"  [{r.score:.3f}] {r.content[:60]}...")
    print()

    # ── Keyword Search ──
    print("🔍 Keyword search: '团队'")
    results = mem.search("团队", mode="keyword", top_k=3)
    for r in results:
        print(f"  [{r.score:.3f}] {r.content[:60]}...")
    print()

    # ── Tag Filter ──
    print("🔍 Tag filter + keyword: tags='project', query='技术'")
    results = mem.search("技术", mode="keyword", tags=["project"])
    for r in results:
        print(f"  [imp={r.importance:.2f}] {r.content[:60]}...")
    print()

    # ── Stats ──
    stats = mem.stats()
    print(f"📊 Stats: {stats['total']} memories, {stats['total_bytes']} bytes")
    print(f"  Top tags: {stats['top_tags']}\n")

    # ── Get / Delete ──
    item = mem.get(1)
    print(f"📖 Get ID=1: {item.content[:50]}...")
    mem.delete(6)
    print(f"🗑  Deleted ID=6 (low importance)\n")

    # ── Prune ──
    print(f"✂️  Pruning — keeping top 67%...")
    mem.prune(keep_ratio=0.67)
    print(f"  After prune: {mem.stats()['total']} memories\n")

    # ── Export ──
    data = mem.export()
    print(f"📦 Export: {len(data)} items")
    for d in data:
        print(f"  ID={d['id']} | imp={d['importance']:.2f} | tags={d['tags']}")
    print()

    # ── Clear ──
    mem.clear()
    print(f"🧹 Cleared all. Remaining: {mem.stats()['total']}")
    mem.close()

    shutil.rmtree(db_path, ignore_errors=True)
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo()
