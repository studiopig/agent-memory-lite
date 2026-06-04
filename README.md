# 🧠 Agent Memory Lite

> 轻量级 AI Agent 记忆管理 — 语义搜索、自动摘要、上下文修剪
>
> Lightweight long-term memory for AI agents. Semantic search, auto-summarization, context pruning.

[![PyPI](https://img.shields.io/pypi/v/agent-memory-lite?style=flat)](https://pypi.org/project/agent-memory-lite/)
[![Python](https://img.shields.io/pypi/pyversions/agent-memory-lite?style=flat)](https://pypi.org/project/agent-memory-lite/)
[![Stars](https://img.shields.io/github/stars/studiopig/agent-memory-lite?style=social)](https://github.com/studiopig/agent-memory-lite)

---

## 🎯 Why

Agent 越跑越聪明，但对话历史越来越长 → 成本爆炸、上下文窗口不够用、关键信息被稀释。

`agent-memory-lite` 解决三个核心问题：

1. **记什么** — 自动识别值得保留的信息
2. **怎么查** — 语义搜索 + 关键词，秒级召回
3. **怎么剪** — 智能修剪冗余，保留 80% 信号

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

# Auto-prune: keep top 80% by importance
mem.prune(keep_ratio=0.8)

# Get stats
print(mem.stats())
# {'total': 42, 'total_chars': 5210, 'top_tags': ['project', 'user-pref']}
```

---

## 🔧 Features

| 功能 | 描述 |
|------|------|
| **Semantic Search** | 基于 embedding 的语义搜索，默认使用轻量模型 |
| **Keyword Search** | 正则 + 关键词匹配 |
| **Tag Filtering** | 标签分类 + 过滤 |
| **Auto-prune** | 按重要性自动修剪，保留信号 |
| **Deduplication** | 自动去重相似记忆 |
| **SQLite Backend** | 零配置持久化 |
| **Importance Score** | 0-1 重要性评分 |

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
| `save(content, tags=[], importance=0.5)` | 保存记忆 |
| `search(query, top_k=5, mode="semantic", tags=None)` | 搜索记忆 |
| `get(memory_id)` | 按 ID 获取单条记忆 |
| `delete(memory_id)` | 删除指定记忆 |
| `prune(keep_ratio=0.8)` | 修剪低重要度记忆 |
| `stats()` | 获取统计信息 |
| `clear()` | 清空所有记忆 |
| `export()` | 导出全部记忆 |
| `close()` | 关闭数据库连接 |

---

## 🆚 Comparison

| | Agent Memory Lite | Mem0 | Cognee |
|------|:--:|:--:|:--:|
| 零配置 | ✅ | ❌ | ❌ |
| 本地运行 | ✅ | ✅ | ❌ |
| 轻量 | ✅ | ❌ | ❌ |
| 自动修剪 | ✅ | ❌ | ❌ |
| SQLite | ✅ | ❌ | ❌ |
| 中文友好 | ✅ | ❌ | ❌ |

---

## 📁 Project Structure

```
agent-memory-lite/
├── agent_memory/
│   ├── __init__.py
│   ├── memory.py      # Core Memory class
│   ├── storage.py     # SQLite backend
│   ├── search.py      # Semantic + keyword search
│   └── prune.py       # Auto-pruning logic
├── README.md
├── LICENSE
└── pyproject.toml
```

---

## 🤝 Contributing

欢迎 PR！特别需要：
- 🧪 更多 embedding 后端支持
- 🔌 MCP Server 封装
- 📊 记忆可视化 Dashboard

---

<p align="center">
  <i>Memory is all you need.</i>
</p>
