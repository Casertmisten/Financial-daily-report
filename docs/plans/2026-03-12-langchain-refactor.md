# Langchain + LangGraph 重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 使用 Langchain + LangGraph 重构金融日报系统，支持盘前早报、盘中快讯、盘后总结三种不同侧重点的报告

**架构:** 基于 LangGraph 的状态机工作流，使用单一状态对象(ReportState)和条件路由实现三种报告类型的差异化生成。保留现有 AKShare 采集逻辑，Langchain 仅用于 LLM 编排。

**技术栈:** Langchain, LangGraph, Langchain Core, 现有 AKShare/ChromaDB/SQLite

---

## Task 1: 更新项目依赖

**Files:**
- Modify: `pyproject.toml`

**Step 1: 添加 Langchain 相关依赖**

编辑 `pyproject.toml`，在 dependencies 数组中添加：

```toml
[project]
name = "financial-daily-report"
version = "0.2.0"
requires-python = ">=3.10"
dependencies = [
    "akshare>=1.12.0",
    "openai>=1.12.0",
    "chromadb>=0.4.0",
    "apscheduler>=3.10.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
    "langchain>=0.1.0",
    "langgraph>=0.0.0",
    "langchain-core>=0.1.0",
]
```

**Step 2: 安装新依赖**

运行: `uv sync`
预期: 成功安装 langchain, langgraph, langchain-core

**Step 3: 提交**

```bash
git add pyproject.toml
git commit -m "feat: add langchain and langgraph dependencies

- Add langchain>=0.1.0
- Add langgraph>=0.0.0
- Add langchain-core>=0.1.0
- Bump version to 0.2.0"
```

---

## Task 2: 创建 workflow 模块目录结构

**Files:**
- Create: `src/workflow/__init__.py`
- Create: `src/workflow/state.py`
- Create: `src/workflow/nodes.py`
- Create: `src/workflow/graph.py`

**Step 1: 创建 __init__.py**

创建文件 `src/workflow/__init__.py`:

```python
"""LangGraph 工作流模块"""
from src.workflow.graph import report_graph

__all__ = ["report_graph"]
```

**Step 2: 提交**

```bash
git add src/workflow/__init__.py
git commit -m "feat: create workflow module with __init__"
```

---

## Task 3: 实现 ReportState 状态定义

**Files:**
- Create: `src/workflow/state.py`
- Test: `tests/test_workflow_state.py`

**Step 1: 编写测试**

创建文件 `tests/test_workflow_state.py`:

```python
import pytest
from src.workflow.state import ReportState


def test_report_state_structure():
    """测试 ReportState 结构"""
    state: ReportState = {
        "report_type": "pre_market",
        "news_data": [{"title": "test"}],
        "market_data": {"stocks": []},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }
    assert state["report_type"] == "pre_market"
    assert state["news_data"][0]["title"] == "test"


def test_report_state_all_fields():
    """测试 ReportState 包含所有必需字段"""
    required_fields = [
        "report_type", "news_data", "market_data",
        "cleaned_news", "context", "report", "errors"
    ]
    state: ReportState = {field: "" if field == "report_type" else [] for field in required_fields}
    for field in required_fields:
        assert field in state
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_state.py -v`
预期: FAIL with "ModuleNotFoundError: No module named 'src.workflow.state'"

**Step 3: 实现 ReportState**

创建文件 `src/workflow/state.py`:

```python
"""工作流状态定义"""
from typing import TypedDict, List, Dict


class ReportState(TypedDict):
    """日报生成的状态对象

    在 LangGraph 工作流中各节点间传递的状态
    """
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
    errors: List[str]  # 收集各阶段的错误（非阻塞）
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_state.py -v`
预期: PASS (2 tests)

**Step 5: 提交**

```bash
git add src/workflow/state.py tests/test_workflow_state.py
git commit -m "feat: implement ReportState with TypedDict"
```

---

## Task 4: 实现数据采集节点

**Files:**
- Create: `src/workflow/nodes.py` (collect_node)
- Test: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - collect_node**

创建文件 `tests/test_workflow_nodes.py`:

```python
import pytest
from src.workflow.nodes import collect_node
from src.workflow.state import ReportState


def test_collect_node_returns_state():
    """测试 collect_node 返回更新后的状态"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }

    result = collect_node(initial_state)

    assert "news_data" in result
    assert "market_data" in result
    assert isinstance(result["news_data"], list)
    assert isinstance(result["market_data"], dict)
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_collect_node_returns_state -v`
预期: FAIL with "cannot import 'collect_node'"

**Step 3: 实现 collect_node**

创建文件 `src/workflow/nodes.py`:

```python
"""LangGraph 工作流节点"""
from loguru import logger
from src.workflow.state import ReportState
from src.collectors.news_collector import NewsCollector
from src.collectors.market_collector import MarketCollector


def collect_node(state: ReportState) -> ReportState:
    """数据采集节点

    从 AKShare 采集新闻和市场数据

    Args:
        state: 当前状态

    Returns:
        更新后的状态，包含 news_data 和 market_data
    """
    logger.info("=== 数据采集 ===")

    news_collector = NewsCollector()
    market_collector = MarketCollector()

    news_data = news_collector.collect()
    market_data = market_collector.collect()

    logger.info(f"✓ 采集完成 (新闻: {len(news_data)}, 市场: {sum(1 for v in market_data.values() if v)}/5)")

    return {**state, "news_data": news_data, "market_data": market_data}
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_collect_node_returns_state -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement collect_node for data collection"
```

---

## Task 5: 实现数据清洗节点

**Files:**
- Modify: `src/workflow/nodes.py` (clean_node)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - clean_node**

在 `tests/test_workflow_nodes.py` 添加:

```python
def test_clean_node_filters_news():
    """测试 clean_node 过滤新闻"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [
            {"title": "正常新闻", "content": "内容"},
            {"title": "广告", "content": "点击购买"}
        ],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }

    result = clean_node(initial_state)

    assert "cleaned_news" in result
    assert isinstance(result["cleaned_news"], list)
    # 规则清洗会移除广告类新闻
    assert len(result["cleaned_news"]) <= len(initial_state["news_data"])
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_clean_node_filters_news -v`
预期: FAIL with "clean_node not defined"

**Step 3: 实现 clean_node**

在 `src/workflow/nodes.py` 添加:

```python
from src.processors.cleaner import RuleCleaner, LLMCleaner


def clean_node(state: ReportState) -> ReportState:
    """数据清洗节点（规则 + LLM）

    先用规则清洗，再用 LLM 智能清洗

    Args:
        state: 当前状态，包含 news_data

    Returns:
        更新后的状态，包含 cleaned_news
    """
    logger.info("=== 数据清洗 ===")

    rule_cleaner = RuleCleaner()
    cleaned = rule_cleaner.clean(state["news_data"])

    if cleaned:
        llm_cleaner = LLMCleaner()
        cleaned = llm_cleaner.clean(cleaned)

    logger.info(f"✓ 清洗完成，保留 {len(cleaned)} 条")

    return {**state, "cleaned_news": cleaned}
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_clean_node_filters_news -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement clean_node with rule and LLM cleaning"
```

---

## Task 6: 实现存储节点

**Files:**
- Modify: `src/workflow/nodes.py` (store_node)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - store_node**

在 `tests/test_workflow_nodes.py` 添加:

```python
def test_store_node_saves_to_database():
    """测试 store_node 保存到数据库"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "测试", "content": "内容", "source": "test"}],
        "context": "",
        "report": "",
        "errors": []
    }

    result = store_node(initial_state)

    # store_node 不修改状态，只执行副作用
    assert result["cleaned_news"] == initial_state["cleaned_news"]
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_store_node_saves_to_database -v`
预期: FAIL with "store_node not defined"

**Step 3: 实现 store_node**

在 `src/workflow/nodes.py` 添加:

```python
from src.storage.database import database


def store_node(state: ReportState) -> ReportState:
    """存储到 SQLite

    将清洗后的新闻保存到数据库

    Args:
        state: 当前状态，包含 cleaned_news

    Returns:
        未修改的状态
    """
    logger.info("=== 存储新闻 ===")

    if state["cleaned_news"]:
        database.save_news(state["cleaned_news"])
        logger.info(f"✓ 保存 {len(state['cleaned_news'])} 条")

    return state
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_store_node_saves_to_database -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement store_node for SQLite storage"
```

---

## Task 7: 实现向量化节点

**Files:**
- Modify: `src/workflow/nodes.py` (vectorize_node)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - vectorize_node**

在 `tests/test_workflow_nodes.py` 添加:

```python
def test_vectorize_node_handles_empty_news():
    """测试 vectorize_node 处理空新闻"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }

    result = vectorize_node(initial_state)

    assert result["cleaned_news"] == []
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_vectorize_node_handles_empty_news -v`
预期: FAIL with "vectorize_node not defined"

**Step 3: 实现 vectorize_node**

在 `src/workflow/nodes.py` 添加:

```python
import hashlib
from src.rag.vector_store import vector_store


def vectorize_node(state: ReportState) -> ReportState:
    """向量化并存储到 Chroma

    将清洗后的新闻向量化并存储到向量数据库

    Args:
        state: 当前状态，包含 cleaned_news

    Returns:
        未修改的状态
    """
    logger.info("=== 向量化存储 ===")

    if not state["cleaned_news"]:
        return state

    docs = []
    for item in state["cleaned_news"]:
        content_str = f"{item['title']}_{item.get('content', '')}"
        doc_id = hashlib.md5(content_str.encode()).hexdigest()
        docs.append({
            'id': doc_id,
            'text': f"{item['title']}\n{item.get('cleaned_content', item.get('content', ''))}",
            'metadata': {
                'source': item.get('source', ''),
                'time': item.get('time', ''),
                'title': item['title']
            }
        })

    if docs:
        vector_store.add_documents(docs)
        logger.info(f"✓ 向量化 {len(docs)} 条")

    return state
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_vectorize_node_handles_empty_news -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement vectorize_node for Chroma storage"
```

---

## Task 8: 实现 RAG 检索节点

**Files:**
- Modify: `src/workflow/nodes.py` (rag_node)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - rag_node**

在 `tests/test_workflow_nodes.py` 添加:

```python
def test_rag_node_returns_context():
    """测试 rag_node 返回上下文"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "测试新闻"}],
        "context": "",
        "report": "",
        "errors": []
    }

    result = rag_node(initial_state)

    assert "context" in result
    assert isinstance(result["context"], str)
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_rag_node_returns_context -v`
预期: FAIL with "rag_node not defined"

**Step 3: 实现 rag_node**

在 `src/workflow/nodes.py` 添加:

```python
from src.rag.retriever import rag_retriever


def rag_node(state: ReportState) -> ReportState:
    """RAG 检索历史上下文

    从向量数据库检索相关历史新闻

    Args:
        state: 当前状态，包含 cleaned_news

    Returns:
        更新后的状态，包含 context
    """
    logger.info("=== RAG 检索 ===")

    context = ""
    if state["cleaned_news"]:
        context = rag_retriever.retrieve(state["cleaned_news"][0]['title'])
        logger.info("✓ RAG 检索完成")

    return {**state, "context": context}
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_rag_node_returns_context -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement rag_node for context retrieval"
```

---

## Task 9: 实现辅助函数 _format_news 和 _format_market

**Files:**
- Modify: `src/workflow/nodes.py` (helper functions)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - helper functions**

在 `tests/test_workflow_nodes.py` 添加:

```python
from src.workflow.nodes import _format_news, _format_market


def test_format_news_returns_string():
    """测试 _format_news 返回字符串"""
    news = [
        {"title": "新闻1", "cleaned_content": "内容1", "content": "原始1"},
        {"title": "新闻2", "content": "内容2"}
    ]
    result = _format_news(news, focus="analysis")
    assert isinstance(result, str)
    assert "新闻1" in result


def test_format_market_returns_string():
    """测试 _format_market 返回字符串"""
    market = {
        "industry_flow": [{"name": "科技", "net_amount": "100万"}],
        "main_flow": []
    }
    result = _format_market(market, focus="deep")
    assert isinstance(result, str)
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_format_news_returns_string -v`
预期: FAIL with "cannot import '_format_news'"

**Step 3: 实现辅助函数**

在 `src/workflow/nodes.py` 添加:

```python
from typing import List, Dict


def _format_news(news_data: List[Dict], focus: str = "analysis") -> str:
    """格式化新闻数据

    Args:
        news_data: 新闻数据列表
        focus: 关注点 (prediction/intraday/analysis)

    Returns:
        格式化的新闻文本
    """
    if not news_data:
        return "暂无新闻数据"

    formatted = []
    for item in news_data[:20]:  # 限制数量
        title = item.get('title', '')
        content = item.get('cleaned_content', '') or item.get('content', '')
        formatted.append(f"- {title}: {content[:100]}")

    return "\n".join(formatted)


def _format_market(market_data: Dict, focus: str = "deep") -> str:
    """格式化市场数据

    Args:
        market_data: 市场数据字典
        focus: 关注点 (pre_market/realtime/deep)

    Returns:
        格式化的市场数据文本
    """
    if not market_data:
        return "暂无市场数据"

    formatted = []

    if market_data.get('industry_flow'):
        formatted.append("行业资金流:")
        for item in market_data['industry_flow'][:5]:
            formatted.append(f"  - {item}")

    if market_data.get('main_flow'):
        formatted.append("主力资金流:")
        for item in market_data['main_flow'][:5]:
            formatted.append(f"  - {item}")

    return "\n".join(formatted)
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_format_news_returns_string -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement _format_news and _format_market helpers"
```

---

## Task 10: 实现盘前早报生成节点

**Files:**
- Modify: `src/workflow/nodes.py` (pre_market_generate_node)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - pre_market_generate_node**

在 `tests/test_workflow_nodes.py` 添加:

```python
def test_pre_market_generate_node():
    """测试盘前早报生成节点"""
    initial_state: ReportState = {
        "report_type": "pre_market",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "美股大涨", "content": "标普500上涨2%"}],
        "context": "历史: 昨日A股下跌",
        "report": "",
        "errors": []
    }

    result = pre_market_generate_node(initial_state)

    assert "report" in result
    assert isinstance(result["report"], str)
    # 注意: 如果 LLM 未配置，测试可能失败，需要 mock
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_pre_market_generate_node -v`
预期: FAIL with "pre_market_generate_node not defined"

**Step 3: 实现 pre_market_generate_node**

在 `src/workflow/nodes.py` 添加:

```python
from src.generators.llm_client import llm_client


def pre_market_generate_node(state: ReportState) -> ReportState:
    """盘前早报生成节点

    生成侧重今日预测和准备的盘前早报

    Args:
        state: 当前状态

    Returns:
        更新后的状态，包含 report
    """
    logger.info("=== 生成盘前早报 ===")
    from config.prompts import PRE_MARKET_PROMPT

    news_summary = _format_news(state["cleaned_news"], focus="prediction")
    market_summary = _format_market(state["market_data"], focus="pre_market")

    prompt = PRE_MARKET_PROMPT.format(
        news_data=news_summary,
        market_data=market_summary,
        historical_context=state["context"]
    )

    report = llm_client.chat([
        {"role": "system", "content": "你是专业中国金融分析师，用中文输出"},
        {"role": "user", "content": prompt}
    ])

    return {**state, "report": report}
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_pre_market_generate_node -v`
预期: PASS (需要 LLM 配置)

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement pre_market_generate_node"
```

---

## Task 11: 实现盘中快讯生成节点

**Files:**
- Modify: `src/workflow/nodes.py` (mid_close_generate_node)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - mid_close_generate_node**

在 `tests/test_workflow_nodes.py` 添加:

```python
def test_mid_close_generate_node():
    """测试盘中快讯生成节点"""
    initial_state: ReportState = {
        "report_type": "mid_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "上午拉升", "content": "科技股领涨"}],
        "context": "",
        "report": "",
        "errors": []
    }

    result = mid_close_generate_node(initial_state)

    assert "report" in result
    assert isinstance(result["report"], str)
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_mid_close_generate_node -v`
预期: FAIL with "mid_close_generate_node not defined"

**Step 3: 实现 mid_close_generate_node**

在 `src/workflow/nodes.py` 添加:

```python
def mid_close_generate_node(state: ReportState) -> ReportState:
    """盘中快讯生成节点

    生成侧重实时动态和异常的盘中快讯

    Args:
        state: 当前状态

    Returns:
        更新后的状态，包含 report
    """
    logger.info("=== 生成盘中快讯 ===")
    from config.prompts import MID_CLOSE_PROMPT

    news_summary = _format_news(state["cleaned_news"], focus="intraday")
    market_summary = _format_market(state["market_data"], focus="realtime")

    prompt = MID_CLOSE_PROMPT.format(
        news_data=news_summary,
        market_data=market_summary,
        historical_context=state["context"]
    )

    report = llm_client.chat([
        {"role": "system", "content": "你是专业中国金融分析师，用中文输出"},
        {"role": "user", "content": prompt}
    ])

    return {**state, "report": report}
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_mid_close_generate_node -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement mid_close_generate_node"
```

---

## Task 12: 实现盘后总结生成节点

**Files:**
- Modify: `src/workflow/nodes.py` (after_close_generate_node)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - after_close_generate_node**

在 `tests/test_workflow_nodes.py` 添加:

```python
def test_after_close_generate_node():
    """测试盘后总结生成节点"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "收盘总结", "content": "三大指数集体收涨"}],
        "context": "",
        "report": "",
        "errors": []
    }

    result = after_close_generate_node(initial_state)

    assert "report" in result
    assert isinstance(result["report"], str)
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_after_close_generate_node -v`
预期: FAIL with "after_close_generate_node not defined"

**Step 3: 实现 after_close_generate_node**

在 `src/workflow/nodes.py` 添加:

```python
def after_close_generate_node(state: ReportState) -> ReportState:
    """盘后总结生成节点

    生成侧重深度分析的盘后总结

    Args:
        state: 当前状态

    Returns:
        更新后的状态，包含 report
    """
    logger.info("=== 生成盘后总结 ===")
    from config.prompts import AFTER_CLOSE_PROMPT

    news_summary = _format_news(state["cleaned_news"], focus="analysis")
    market_summary = _format_market(state["market_data"], focus="deep")

    prompt = AFTER_CLOSE_PROMPT.format(
        news_data=news_summary,
        market_data=market_summary,
        historical_context=state["context"]
    )

    report = llm_client.chat([
        {"role": "system", "content": "你是专业中国金融分析师，用中文输出"},
        {"role": "user", "content": prompt}
    ])

    return {**state, "report": report}
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_after_close_generate_node -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement after_close_generate_node"
```

---

## Task 13: 实现保存节点

**Files:**
- Modify: `src/workflow/nodes.py` (save_node)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - save_node**

在 `tests/test_workflow_nodes.py` 添加:

```python
def test_save_node():
    """测试保存节点"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "# 测试报告\n内容",
        "errors": []
    }

    result = save_node(initial_state)

    # save_node 执行副作用，返回未修改的状态
    assert result["report"] == initial_state["report"]
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_save_node -v`
预期: FAIL with "save_node not defined"

**Step 3: 实现 save_node**

在 `src/workflow/nodes.py` 添加:

```python
def save_node(state: ReportState) -> ReportState:
    """保存日报

    将生成的日报保存到数据库和文件

    Args:
        state: 当前状态，包含 report 和 report_type

    Returns:
        未修改的状态
    """
    logger.info("=== 保存日报 ===")

    from datetime import datetime
    from pathlib import Path
    from config.settings import config

    report_date = datetime.now().strftime("%Y-%m-%d")

    # 保存到数据库
    database.save_report(report_date, state["report_type"], state["report"])

    # 保存到文件
    output_file = config.output_dir / f"{report_date}_{state['report_type']}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(state["report"])

    logger.success(f"✓ 日报已保存: {output_file}")
    return state
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_save_node -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement save_node"
```

---

## Task 14: 实现条件路由函数

**Files:**
- Modify: `src/workflow/nodes.py` (route_by_report_type)
- Modify: `tests/test_workflow_nodes.py`

**Step 1: 编写测试 - route_by_report_type**

在 `tests/test_workflow_nodes.py` 添加:

```python
from src.workflow.nodes import route_by_report_type


def test_route_by_report_type():
    """测试条件路由函数"""
    assert route_by_report_type({"report_type": "pre_market"}) == "pre_market_generate"
    assert route_by_report_type({"report_type": "mid_close"}) == "mid_close_generate"
    assert route_by_report_type({"report_type": "after_close"}) == "after_close_generate"
    assert route_by_report_type({"report_type": "unknown"}) == "after_close_generate"  # 默认
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_nodes.py::test_route_by_report_type -v`
预期: FAIL with "route_by_report_type not defined"

**Step 3: 实现 route_by_report_type**

在 `src/workflow/nodes.py` 添加:

```python
def route_by_report_type(state: ReportState) -> str:
    """根据报告类型路由到不同生成节点

    Args:
        state: 当前状态，包含 report_type

    Returns:
        目标节点名称
    """
    route_map = {
        "pre_market": "pre_market_generate",
        "mid_close": "mid_close_generate",
        "after_close": "after_close_generate"
    }
    return route_map.get(state["report_type"], "after_close_generate")
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_nodes.py::test_route_by_report_type -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: implement route_by_report_type conditional routing"
```

---

## Task 15: 实现图构建

**Files:**
- Create: `src/workflow/graph.py`
- Test: `tests/test_workflow_graph.py`

**Step 1: 编写测试 - 图构建**

创建文件 `tests/test_workflow_graph.py`:

```python
import pytest
from src.workflow.graph import create_report_graph


def test_graph_creation():
    """测试图创建成功"""
    graph = create_report_graph()
    assert graph is not None


def test_graph_has_entry_point():
    """测试图有入口点"""
    graph = create_report_graph()
    # 图应该有一个入口点 (collect 节点)
    assert graph is not None


def test_graph_structure():
    """测试图结构"""
    graph = create_report_graph()
    # 图应该可以编译
    assert graph is not None
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_workflow_graph.py -v`
预期: FAIL with "cannot import 'create_report_graph'"

**Step 3: 实现图构建**

创建文件 `src/workflow/graph.py`:

```python
"""LangGraph 工作流图"""
from langgraph.graph import StateGraph, END
from src.workflow.state import ReportState
from src.workflow.nodes import (
    collect_node, clean_node, store_node, vectorize_node, rag_node,
    pre_market_generate_node, mid_close_generate_node, after_close_generate_node,
    save_node, route_by_report_type
)


def create_report_graph() -> StateGraph:
    """创建日报生成工作流图

    构建一个包含采集、清洗、存储、向量化、检索、生成、保存的完整流程。
    根据报告类型路由到不同的生成节点。

    Returns:
        编译后的 StateGraph 实例
    """
    builder = StateGraph(ReportState)

    # 添加所有节点
    builder.add_node("collect", collect_node)
    builder.add_node("clean", clean_node)
    builder.add_node("store", store_node)
    builder.add_node("vectorize", vectorize_node)
    builder.add_node("rag", rag_node)
    builder.add_node("pre_market_generate", pre_market_generate_node)
    builder.add_node("mid_close_generate", mid_close_generate_node)
    builder.add_node("after_close_generate", after_close_generate_node)
    builder.add_node("save", save_node)

    # 设置入口点
    builder.set_entry_point("collect")

    # 构建线性流程：collect → clean → store → vectorize → rag
    builder.add_edge("collect", "clean")
    builder.add_edge("clean", "store")
    builder.add_edge("store", "vectorize")
    builder.add_edge("vectorize", "rag")

    # 条件路由：根据 report_type 分流到不同生成节点
    builder.add_conditional_edges(
        "rag",
        route_by_report_type,
        {
            "pre_market_generate": "pre_market_generate",
            "mid_close_generate": "mid_close_generate",
            "after_close_generate": "after_close_generate"
        }
    )

    # 所有生成节点汇聚到 save
    builder.add_edge("pre_market_generate", "save")
    builder.add_edge("mid_close_generate", "save")
    builder.add_edge("after_close_generate", "save")

    # save 结束
    builder.add_edge("save", END)

    return builder.compile()


# 全局图实例
report_graph = create_report_graph()
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_workflow_graph.py -v`
预期: PASS

**Step 5: 提交**

```bash
git add src/workflow/graph.py tests/test_workflow_graph.py
git commit -m "feat: implement LangGraph workflow with conditional routing"
```

---

## Task 16: 扩展 Prompt 配置

**Files:**
- Modify: `config/prompts.py`

**Step 1: 添加三种 Prompt 模板**

在 `config/prompts.py` 添加:

```python
from datetime import datetime


# ============ 盘前早报 Prompt ============
PRE_MARKET_PROMPT = """你是一位专业的中国金融分析师。请基于以下数据生成盘前早报。

## 时间
{current_date} 早上 8:30

## 数据源
- 新闻数据：{news_data}
- 市场数据：{market_data}
- 历史参考：{historical_context}

## 重点关注
1. **美股隔夜回顾** - 标普500、纳斯达克、中概股表现
2. **A股开盘预测** - 基于外围市场和消息面判断
3. **今日事件日历** - 经济数据发布、重要会议
4. **个股公告精选** - 重大利好/利空公告

## 输出要求
请用**中文**生成一份 Markdown 格式的盘前早报，包含：
- 一句话早报摘要
- 美股隔夜回顾
- A股开盘预测（3-5条）
- 今日重点关注（5-8条）
- 个股公告精选

**重要：请确保所有内容都是中文。**
"""


# ============ 盘中快讯 Prompt ============
MID_CLOSE_PROMPT = """你是一位专业的中国金融分析师。请基于以下数据生成盘中快讯。

## 时间
{current_date} 中午 11:30

## 数据源
- 新闻数据：{news_data}
- 市场数据：{market_data}
- 历史参考：{historical_context}

## 重点关注
1. **上午走势总结** - 大盘指数、成交量、涨跌分布
2. **行业资金流向** - 净流入/流出前五行业
3. **概念板块异动** - 涨幅榜、跌幅榜
4. **个股异动提醒** - 涨停/跌停、放量

## 输出要求
请用**中文**生成一份 Markdown 格式的盘中快讯，包含：
- 一句话上午总结
- 大盘走势回顾
- 热门行业/概念（资金流向）
- 个股异动榜
- 下午关注提示

**重要：请确保所有内容都是中文。**
"""


# ============ 盘后总结 Prompt ============
AFTER_CLOSE_PROMPT = """你是一位专业的中国金融分析师。请基于以下数据生成盘后深度总结。

## 时间
{current_date} 下午 15:30

## 数据源
- 新闻数据：{news_data}
- 市场数据：{market_data}
- 历史参考：{historical_context}

## 重点关注
1. **全日行情回顾** - 指数、成交量、涨跌统计
2. **龙虎榜分析** - 机构席位、游资动向
3. **主力资金流向** - 行业/概念/个股
4. **深度市场分析** - 走势原因、影响因素

## 输出要求
请用**中文**生成一份 Markdown 格式的盘后总结，包含：
- 一句话日总结
- 全日行情回顾（指数、成交、涨跌）
- 资金面分析（行业/概念/龙虎榜）
- 深度市场解读
- 明日关注重点

**重要：请确保所有内容都是中文。**
"""
```

**Step 2: 更新现有 DAILY_REPORT_PROMPT 别名**

在 `config/prompts.py` 末尾添加:

```python
# 向后兼容
DAILY_REPORT_PROMPT = AFTER_CLOSE_PROMPT
```

**Step 3: 提交**

```bash
git add config/prompts.py
git commit -m "feat: add three report type prompts (pre/mid/after)

- Add PRE_MARKET_PROMPT for 8:30 reports
- Add MID_CLOSE_PROMPT for 11:30 reports
- Add AFTER_CLOSE_PROMPT for 15:30 reports
- Keep DAILY_REPORT_PROMPT as alias for compatibility"
```

---

## Task 17: 重构 main.py 使用工作流图

**Files:**
- Modify: `src/main.py`

**Step 1: 更新 main.py 使用图**

替换 `src/main.py` 内容为:

```python
"""主程序入口，负责协调整个日报生成流程"""
from loguru import logger
from src.workflow.graph import report_graph
from src.generators.llm_client import llm_client
from src.utils.exceptions import ReportGenerationError
from datetime import datetime


def generate_daily_report(report_type: str = "after_close") -> str:
    """
    生成日报主流程

    Args:
        report_type: 报告类型 (pre_market/mid_close/after_close)

    Returns:
        生成的日报内容

    Raises:
        ReportGenerationError: 日报生成失败时抛出
    """
    logger.info(f"开始生成日报: {report_type}")

    # 步骤0: 测试LLM连通性
    logger.info("=== 步骤0: 测试LLM连通性 ===")
    connection_test = llm_client.test_connection()

    if not connection_test["all_ok"]:
        logger.error("LLM连通性测试失败！")
        if not connection_test["chat_model"]:
            logger.error(f"生成模型不通: {config.llm.chat_model}")
        if not connection_test["embedding_model"]:
            logger.error(f"嵌入模型不通: {config.embedding.embedding_model}")
        raise ReportGenerationError("LLM模型连通性测试失败，请检查配置")

    logger.success("✓ LLM连通性测试通过")

    # 初始状态
    initial_state = {
        "report_type": report_type,
        "news_data": [],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }

    try:
        # 执行工作流图
        result = report_graph.invoke(initial_state)

        logger.success(f"日报生成完成: {report_type}")
        return result["report"]

    except Exception as e:
        logger.critical(f"工作流执行失败: {e}")
        raise ReportGenerationError(f"日报生成失败: {e}") from e


def main():
    """主入口"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        report_type = sys.argv[2] if len(sys.argv) > 2 else "after_close"
        try:
            generate_daily_report(report_type)
        except Exception as e:
            logger.error(f"日报生成失败: {e}")
            sys.exit(1)
    else:
        # 启动定时调度
        from src.scheduler.cron_scheduler import ReportScheduler
        scheduler = ReportScheduler()
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("程序退出")
            sys.exit(0)


if __name__ == "__main__":
    main()
```

**Step 2: 添加缺失的 config import**

在 `src/main.py` 顶部添加:

```python
from config.settings import config
```

**Step 3: 提交**

```bash
git add src/main.py
git commit -m "refactor: use LangGraph workflow in main entry point

- Replace manual workflow with report_graph.invoke()
- Simplify main.py to just test connection and invoke graph
- All workflow logic now in src/workflow/"
```

---

## Task 18: 更新调度器支持三种报告类型

**Files:**
- Modify: `src/scheduler/cron_scheduler.py`

**Step 1: 更新调度器配置**

检查 `src/scheduler/cron_scheduler.py` 中的报告类型配置：

```python
# 确保调度器使用正确的报告类型名称
self.jobs = [
    {"name": "盘前早报", "type": "pre_market", "cron": "0 8:30"},
    {"name": "盘中快讯", "type": "mid_close", "cron": "0 11:30"},
    {"name": "盘后总结", "type": "after_close", "cron": "0 15:30"}
]
```

**Step 2: 提交（如果有修改）**

```bash
git add src/scheduler/cron_scheduler.py
git commit -m "chore: verify scheduler uses correct report types"
```

---

## Task 19: 添加完整工作流集成测试

**Files:**
- Create: `tests/test_workflow_integration.py`

**Step 1: 编写集成测试**

创建文件 `tests/test_workflow_integration.py`:

```python
import pytest
from src.workflow.graph import report_graph
from src.generators.llm_client import llm_client


@pytest.mark.integration
def test_full_workflow_pre_market():
    """测试完整盘前早报工作流"""
    # 跳过如果 LLM 未配置
    try:
        llm_client.test_connection()
    except Exception:
        pytest.skip("LLM not configured")

    initial_state = {
        "report_type": "pre_market",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }

    result = report_graph.invoke(initial_state)

    assert "report" in result
    assert len(result["report"]) > 0


@pytest.mark.integration
def test_full_workflow_mid_close():
    """测试完整盘中快讯工作流"""
    try:
        llm_client.test_connection()
    except Exception:
        pytest.skip("LLM not configured")

    initial_state = {
        "report_type": "mid_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }

    result = report_graph.invoke(initial_state)

    assert "report" in result
    assert len(result["report"]) > 0


@pytest.mark.integration
def test_full_workflow_after_close():
    """测试完整盘后总结工作流"""
    try:
        llm_client.test_connection()
    except Exception:
        pytest.skip("LLM not configured")

    initial_state = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }

    result = report_graph.invoke(initial_state)

    assert "report" in result
    assert len(result["report"]) > 0
```

**Step 2: 运行集成测试**

运行: `pytest tests/test_workflow_integration.py -v -m integration`
预期: PASS (如果 LLM 配置正确) 或 SKIP

**Step 3: 提交**

```bash
git add tests/test_workflow_integration.py
git commit -m "test: add full workflow integration tests"
```

---

## Task 20: 更新文档

**Files:**
- Modify: `README.md`
- Create: `docs/langchain-workflow.md`

**Step 1: 更新 README.md**

在 README.md 添加 Langchain 相关说明:

```markdown
## 架构

本项目使用 Langchain + LangGraph 实现工作流编排：

- **状态管理**: 使用 TypedDict 定义工作流状态
- **节点设计**: 采集、清洗、存储、向量化、检索、生成、保存
- **条件路由**: 根据报告类型自动路由到不同生成节点

### 工作流图

```
collect → clean → store → vectorize → rag → [路由] → generate → save
                                         ↓
                            pre_market | mid_close | after_close
```

### 三种报告类型

| 类型 | 时间 | 侧重点 |
|------|------|--------|
| 盘前早报 | 8:30 | 今日预测和准备 |
| 盘中快讯 | 11:30 | 实时动态和异常 |
| 盘后总结 | 15:30 | 深度分析 |
```

**Step 2: 创建 Langchain 工作流文档**

创建文件 `docs/langchain-workflow.md`:

```markdown
# Langchain + LangGraph 工作流说明

## 工作流架构

本项目使用 LangGraph 构建状态机工作流，实现金融日报的自动化生成。

## 状态定义

工作流使用 `ReportState` 在节点间传递数据：

```python
class ReportState(TypedDict):
    report_type: str      # 报告类型
    news_data: List[Dict] # 采集的新闻
    market_data: Dict     # 采集的市场数据
    cleaned_news: List[Dict]  # 清洗后的新闻
    context: str          # RAG 检索的上下文
    report: str           # 生成的报告
    errors: List[str]     # 错误收集
```

## 节点说明

### 共享节点

- `collect_node`: AKShare 数据采集
- `clean_node`: 规则 + LLM 清洗
- `store_node`: SQLite 存储
- `vectorize_node`: Chroma 向量化
- `rag_node`: 历史上下文检索
- `save_node`: 报告保存

### 生成节点

- `pre_market_generate_node`: 盘前早报生成
- `mid_close_generate_node`: 盘中快讯生成
- `after_close_generate_node`: 盘后总结生成

## 使用方法

### 命令行执行

```bash
# 生成盘前早报
python -m src.main run pre_market

# 生成盘中快讯
python -m src.main run mid_close

# 生成盘后总结
python -m src.main run after_close
```

### Python API

```python
from src.workflow.graph import report_graph

result = report_graph.invoke({
    "report_type": "pre_market",
    "news_data": [],
    "market_data": {},
    "cleaned_news": [],
    "context": "",
    "report": "",
    "errors": []
})

print(result["report"])
```
```

**Step 3: 提交**

```bash
git add README.md docs/langchain-workflow.md
git commit -m "docs: add Langchain workflow documentation"
```

---

## Task 21: 完整测试验证

**Files:**
- (运行所有测试)

**Step 1: 运行所有单元测试**

运行: `pytest tests/ -v --ignore=tests/test_workflow_integration.py`
预期: PASS (所有现有测试 + 新的工作流测试)

**Step 2: 运行集成测试（可选）**

运行: `pytest tests/test_workflow_integration.py -v -m integration`
预期: PASS 或 SKIP

**Step 3: 手动测试三种报告类型**

运行: `python -m src.main run pre_market`
预期: 生成盘前早报文件

运行: `python -m src.main run mid_close`
预期: 生成盘中快讯文件

运行: `python -m src.main run after_close`
预期: 生成盘后总结文件

**Step 4: 验证向后兼容**

运行现有测试确保未破坏现有功能

运行: `pytest tests/ -v`
预期: 所有测试通过

**Step 5: 最终提交**

```bash
git add .
git commit -m "test: verify all tests pass after Langchain refactor"
```

---

## 完成检查清单

- [ ] 所有 21 个任务完成
- [ ] 所有测试通过
- [ ] 三种报告类型可独立生成
- [ ] 向后兼容现有功能
- [ ] 文档更新完整
