# Langchain + LangGraph 重构设计

**日期**: 2026-03-12
**目标**: 使用 Langchain + LangGraph 重构金融日报系统，实现三种报告的不同侧重点

---

## 1. 设计目标

将现有的线性流程重构为基于 LangGraph 的状态机工作流，支持：
- **盘前早报** (8:30) - 侧重今日预测和准备
- **盘中快讯** (11:30) - 侧重实时动态和异常
- **盘后总结** (15:30) - 侧重深度分析

---

## 2. 架构选择

| 方面 | 选择 | 理由 |
|------|------|------|
| AKShare 采集 | 保留现有逻辑 | 已验证可用，LangGraph 仅用于编排 |
| 状态结构 | 单一状态对象 | 流程固定，简单直接 |
| 工作流结构 | 单图 + 条件路由 | 80% 流程共享，差异仅在 Prompt |
| 检查点 | 无检查点 | 定时自动化任务，无需断点续传 |
| Prompt 管理 | 配置文件分离 | 简单清晰，易于维护 |

---

## 3. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        调度层                                │
│                   APScheduler 定时任务                       │
│            8:30 / 11:30 / 15:30 触发                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      LangGraph 工作流                        │
│  collect → clean → store → vectorize → rag                   │
│                     ↓                                        │
│                  条件路由                                     │
│         ┌───────────┼───────────┐                           │
│         ▼           ▼           ▼                           │
│   pre_generate  mid_generate  post_generate                  │
│         └───────────┼───────────┘                           │
│                     ▼                                        │
│                   save                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    现有组件（保留）                           │
│  • NewsCollector / MarketCollector                          │
│  • RuleCleaner / LLMCleaner                                 │
│  • vector_store / rag_retriever                             │
│  • database / llm_client                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 状态定义

```python
class ReportState(TypedDict):
    """日报生成的状态对象"""

    # 输入参数
    report_type: str  # "pre_market" | "mid_close" | "after_close"

    # 采集阶段
    news_data: List[Dict]
    market_data: Dict

    # 清洗阶段
    cleaned_news: List[Dict]

    # RAG 阶段
    context: str

    # 生成阶段
    report: str

    # 元数据
    errors: List[str]
```

---

## 5. 节点设计

### 共享节点
- `collect_node` - 数据采集
- `clean_node` - 数据清洗（规则 + LLM）
- `store_node` - 存储 SQLite
- `vectorize_node` - 向量化 Chroma
- `rag_node` - RAG 检索
- `save_node` - 保存日报

### 报告类型专属节点
- `pre_market_generate_node` - 盘前早报生成
- `mid_close_generate_node` - 盘中快讯生成
- `after_close_generate_node` - 盘后总结生成

### 路由函数
- `route_by_report_type` - 根据 `report_type` 路由到对应生成节点

---

## 6. 报告类型差异

### 盘前早报 (8:30)
**侧重点**: 今日预测和准备

内容结构：
- 一句话早报摘要
- 美股隔夜回顾（标普500、纳指、中概股）
- A股开盘预测（3-5条）
- 今日事件日历
- 个股公告精选

### 盘中快讯 (11:30)
**侧重点**: 实时动态和异常

内容结构：
- 一句话上午总结
- 大盘走势回顾
- 热门行业/概念（资金流向）
- 个股异动榜
- 下午关注提示

### 盘后总结 (15:30)
**侧重点**: 深度分析

内容结构：
- 一句话日总结
- 全日行情回顾
- 资金面分析（行业/概念/龙虎榜）
- 深度市场解读
- 明日关注重点

---

## 7. 文件结构

```
Financial-daily-report/
├── pyproject.toml
├── config/
│   ├── settings.py
│   └── prompts.py                    # 扩展：三种 Prompt
├── src/
│   ├── main.py                       # 重构：调用图
│   ├── workflow/                     # 新增
│   │   ├── __init__.py
│   │   ├── state.py                  # ReportState
│   │   ├── nodes.py                  # 节点实现
│   │   └── graph.py                  # 图构建
│   ├── collectors/                   # 保持不变
│   ├── processors/
│   ├── rag/
│   ├── generators/
│   ├── storage/
│   └── scheduler/
└── tests/
    └── test_workflow.py              # 新增
```

---

## 8. 依赖更新

```toml
[project]
dependencies = [
    "akshare>=1.12.0",
    "openai>=1.12.0",
    "chromadb>=0.4.0",
    "apscheduler>=3.10.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
    "langchain>=0.1.0",           # 新增
    "langgraph>=0.0.0",           # 新增
    "langchain-core>=0.1.0",      # 新增
]
```

---

## 9. 向后兼容

- 保持所有现有组件不变
- 现有测试继续通过
- 原有的 `DAILY_REPORT_PROMPT` 重命名为 `AFTER_CLOSE_PROMPT`
- API 入口保持一致

---

## 10. 实施计划概要

1. 添加 Langchain 依赖
2. 创建 `src/workflow/` 模块
3. 实现 `state.py` - ReportState 定义
4. 实现 `nodes.py` - 各节点函数
5. 实现 `graph.py` - 图构建
6. 扩展 `prompts.py` - 添加三种 Prompt
7. 重构 `main.py` - 使用图调用
8. 添加工作流测试
9. 更新文档
10. 完整测试验证
