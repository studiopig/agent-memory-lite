# 🧠 Agent Memory Lite

> 轻量级 AI Agent 记忆管理 — 语义搜索、标签过滤、重要性修剪
>
> Lightweight long-term memory for AI agents. Semantic search, tag filtering, importance-based pruning.

[![PyPI](https://img.shields.io/pypi/v/agent-memory-lite?style=flat)](https://pypi.org/project/agent-memory-lite/)
[![Python](https://img.shields.io/pypi/pyversions/agent-memory-lite?style=flat)](https://pypi.org/project/agent-memory-lite/)
[![Stars](https://img.shields.io/github/stars/studiopig/agent-memory-lite?style=social)](https://github.com/studiopig/agent-memory-lite)

---

## 🎯 Why

Agent 越跑越聪明，但对话历史越来越长 → 成本爆炸、上下文窗口不够用、关键信息被稀释。

`agent-memory-lite` 解决三个核心问题：

1. **记什么** — 由调用方设定 importance score（0-1），标识值得保留的信息
2. **怎么查** — 语义搜索 + 关键词，秒级召回
3. **怎么剪** — 按 importance 修剪冗余，支持去重

---

## 📦 Install

```bash
pip install agent-memory-lite
```

## 🚀 Quick Start

```python
from agent_memory import Memory

# Initialize
mem = Memory(storage="./agent_memory")

# Save a memory
mem.save("用户偏好简洁回复，不喜欢废话", importance=0.8)

# Save with metadata
mem.save(
    "项目使用 React + FastAPI，部署在 K8s",
    tags=["tech-stack", "project"],
    importance=0.9,
)

# Semantic search
results = mem.search("用户喜欢什么风格？", top_k=3)
for r in results:
    print(f"[{r.score:.2f}] {r.content}")

# Keyword search + filter
results = mem.search("React", mode="keyword", tags=["project"])

# Get/delete by ID
mem.get(1)
mem.delete(1)

# Prune: keep top 80% by importance
mem.prune(keep_ratio=0.8)

# Get stats
print(mem.stats())
# {'total': 42, 'total_bytes': 5210, 'top_tags': ['project', 'user-pref']}
```

### 🔌 Run as MCP Server

```bash
# Install with MCP support
pip install agent-memory-lite[mcp]

# Start the server (for Claude Desktop / Cline / Continue)
agent-memory serve --storage ./my_memories
```

MCP client config:

```json
{
  "mcpServers": {
    "memory": {
      "command": "agent-memory",
      "args": ["serve", "--storage", "./agent_memory"]
    }
  }
}
```

Available MCP tools: `memory_save`, `memory_search`, `memory_get`, `memory_delete`, `memory_prune`, `memory_stats`, `memory_clear`, `memory_export`.

---

## 🔧 Features

| 功能 | 描述 |
|------|------|
| **Semantic Search** | 基于 embedding 的语义搜索，默认使用轻量模型 |
| **Keyword Search** | 关键词子串匹配 |
| **Tag Filtering** | 标签分类 + 过滤 |
| **Importance Pruning** | 按 importance 修剪，保留高优先级记忆 |
| **Deduplication** | Prune 时自动去重相似记忆（Jaccard similarity） |
| **SQLite Backend** | 零配置持久化 |
| **CRUD API** | save / search / get / delete / prune / stats / export |

---

## 🏗 Architecture

```
┌─────────────────────────────────────┐
│           Agent Memory Lite          │
├───────────┬─────────────┬───────────┤
│  Storage  │   Search    │   Prune   │
│ (SQLite)  │ (semantic/  │ (retain   │
│           │  keyword)   │  signal)  │
└───────────┴─────────────┴───────────┘
```

---

## 📖 API

### Memory(storage="./memory", model="sentence-transformers/all-MiniLM-L6-v2")

| Method | Description |
|--------|-------------|
| `save(content, tags=[], importance=0.5)` | 保存记忆 → 返回 ID |
| `search(query, top_k=5, mode="semantic", tags=None)` | 搜索记忆 |
| `get(memory_id)` | 按 ID 获取单条记忆 → MemoryResult 或 None |
| `delete(memory_id)` | 删除指定记忆 |
| `prune(keep_ratio=0.8)` | 修剪低 importance 记忆 |
| `stats()` | 获取统计信息 |
| `clear()` | 清空所有记忆（含 embeddings） |
| `export()` | 导出全部记忆为 list[dict] |
| `close()` | 关闭数据库连接 |

**参数校验：** 所有公开方法均做严格输入校验。`content` 不允许空字符串，`importance` 必须在 [0,1]，`keep_ratio` 必须在 (0,1]，`mode` 只接受 `"semantic"` 或 `"keyword"`。

---

## 🆚 Comparison

| | Agent Memory Lite | Mem0 | Cognee |
|------|:--:|:--:|:--:|
| 零配置 | ✅ | ❌ | ❌ |
| 本地运行 | ✅ | ✅ | ❌ |
| 轻量 | ✅ | ❌ | ❌ |
| Importance 修剪 | ✅ | ❌ | ❌ |
| SQLite | ✅ | ❌ | ❌ |
| 中文去重 | ✅ | ❌ | ❌ |

---

## 📁 Project Structure

```
agent-memory-lite/
├── agent_memory/
│   ├── __init__.py
│   ├── memory.py      # Core Memory class + validators
│   ├── storage.py     # SQLite backend + embeddings cache
│   ├── search.py      # Semantic + keyword search
│   ├── prune.py       # Importance-based pruning + dedup
│   ├── server.py      # MCP Server wrapper
│   └── cli.py         # CLI entry point
├── examples/
│   └── demo.py        # Full workflow demo
├── tests/
│   └── test_memory.py
├── README.md
├── LICENSE
└── pyproject.toml
```

---

## 🤝 Contributing

欢迎 PR！特别需要：
- 🧪 更多 embedding 后端支持（OpenAI、Cohere 等）
- 📊 记忆可视化 Dashboard
- 🌐 REST API 封装

---

<p align="center">
  <i>Memory is all you need.</i>
</p>
