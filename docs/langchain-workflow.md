# LangGraph 工作流文档

本文档详细说明了金融日报生成系统的 LangGraph 工作流实现。

## 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [状态定义](#状态定义)
- [工作流节点](#工作流节点)
- [工作流图](#工作流图)
- [报告类型](#报告类型)
- [配置说明](#配置说明)
- [扩展指南](#扩展指南)

## 概述

金融日报生成系统使用 LangGraph 实现了可编排的工作流。LangGraph 是一个基于状态图的工作流框架，它允许我们以声明的方式定义复杂的数据处理流程。

### 主要优势

1. **可视化**：工作流图可以被可视化和调试
2. **可测试性**：每个节点可以独立测试
3. **可扩展性**：轻松添加新的节点或路由逻辑
4. **状态管理**：自动管理节点间的状态传递
5. **条件路由**：支持基于状态的条件分支

### 工作流概述

```
数据采集 → 数据清洗 → 存储数据库 → 向量化 → RAG检索 → [条件路由] → 生成报告 → 保存文件
```

## 架构设计

### 模块结构

```
src/workflow/
├── __init__.py       # 模块初始化
├── state.py          # 状态定义
├── nodes.py          # 节点实现
└── graph.py          # 工作流图构建
```

### 设计原则

1. **单一职责**：每个节点只负责一个特定的任务
2. **不可变性**：节点不修改输入状态，而是返回新的状态
3. **错误处理**：每个节点都处理自己的错误，不中断整个流程
4. **日志记录**：每个节点都记录关键操作

## 状态定义

`ReportState` 是工作流中传递的数据结构，定义在 `src/workflow/state.py`：

```python
from typing import TypedDict, List, Dict

class ReportState(TypedDict):
    """日报生成的状态对象"""
    report_type: str           # 报告类型: pre_market/mid_close/after_close
    news_data: List[Dict]      # 原始新闻数据
    market_data: Dict          # 原始市场数据
    cleaned_news: List[Dict]   # 清洗后的新闻
    context: str               # RAG检索的上下文
    report: str                # 生成的报告
    errors: List[str]          # 错误列表
```

### 状态流转

1. **初始状态**：只包含 `report_type`
2. **采集后**：添加 `news_data` 和 `market_data`
3. **清洗后**：添加 `cleaned_news`
4. **RAG后**：添加 `context`
5. **生成后**：添加 `report`
6. **保存后**：状态完整

## 工作流节点

### 1. collect_node (数据采集节点)

**功能**：从 AKShare 采集新闻和市场数据

**输入**：
- `report_type`: 报告类型

**输出**：
- `news_data`: 新闻数据列表
- `market_data`: 市场数据字典

**实现细节**：
- 使用 `NewsCollector` 采集新闻
- 使用 `MarketCollector` 采集市场数据
- 统计并记录采集结果

**错误处理**：记录错误但不中断流程

### 2. clean_node (数据清洗节点)

**功能**：使用规则和 LLM 清洗新闻数据

**输入**：
- `news_data`: 原始新闻数据

**输出**：
- `cleaned_news`: 清洗后的新闻

**实现细节**：
- 先使用 `RuleCleaner` 进行规则清洗
- 再使用 `LLMCleaner` 进行智能清洗
- 如果 LLM 清洗失败，使用规则清洗结果

**错误处理**：LLM 清洗失败时回退到规则清洗

### 3. store_node (存储节点)

**功能**：将清洗后的新闻保存到 SQLite

**输入**：
- `cleaned_news`: 清洗后的新闻

**输出**：
- 无（状态不变）

**实现细节**：
- 使用 `database.save_news()` 保存
- 记录保存的新闻数量

**错误处理**：记录错误但不中断流程

### 4. vectorize_node (向量化节点)

**功能**：将新闻向量化并存储到 Chroma

**输入**：
- `cleaned_news`: 清洗后的新闻

**输出**：
- 无（状态不变）

**实现细节**：
- 为每条新闻生成唯一 ID（MD5）
- 使用标题和内容构建文档文本
- 添加元数据（来源、时间、标题）
- 使用 `vector_store.add_documents()` 存储

**错误处理**：记录错误但不中断流程

### 5. rag_node (RAG检索节点)

**功能**：从向量数据库检索相关历史新闻

**输入**：
- `cleaned_news`: 清洗后的新闻

**输出**：
- `context`: 检索到的历史上下文

**实现细节**：
- 使用第一条新闻标题作为查询
- 调用 `rag_retriever.retrieve()` 检索
- 如果没有新闻或检索失败，返回空字符串

**错误处理**：检索失败时返回 "无相关历史信息"

### 6. pre_market_generate_node (盘前早报生成节点)

**功能**：生成盘前早报，关注今日预测

**输入**：
- `cleaned_news`: 清洗后的新闻
- `market_data`: 市场数据
- `context`: RAG上下文

**输出**：
- `report`: 生成的盘前早报

**实现细节**：
- 格式化新闻（限制20条）
- 格式化市场数据
- 使用 `PRE_MARKET_PROMPT` 模板
- 设置系统消息为早上8:30的金融分析师

**错误处理**：生成失败时返回包含数据的错误报告

### 7. mid_close_generate_node (盘中快讯生成节点)

**功能**：生成盘中快讯，关注实时动态

**输入**：
- `cleaned_news`: 清洗后的新闻
- `market_data`: 市场数据
- `context`: RAG上下文

**输出**：
- `report`: 生成的盘中快讯

**实现细节**：
- 格式化新闻（限制15条）
- 格式化市场数据
- 使用 `MID_CLOSE_PROMPT` 模板
- 设置系统消息为中午11:30的金融分析师

**错误处理**：生成失败时返回包含数据的错误报告

### 8. after_close_generate_node (盘后总结生成节点)

**功能**：生成盘后深度总结，关注深度分析

**输入**：
- `cleaned_news`: 清洗后的新闻
- `market_data`: 市场数据
- `context`: RAG上下文

**输出**：
- `report`: 生成的盘后总结

**实现细节**：
- 格式化新闻（限制20条）
- 格式化市场数据
- 使用 `AFTER_CLOSE_PROMPT` 模板
- 设置系统消息为下午15:30的金融分析师

**错误处理**：生成失败时返回包含数据的错误报告

### 9. save_node (保存节点)

**功能**：将报告保存到数据库和文件

**输入**：
- `report`: 生成的报告
- `report_type`: 报告类型

**输出**：
- 无（状态不变）

**实现细节**：
- 保存到 SQLite 数据库
- 保存到 Markdown 文件（格式：YYYY-MM-DD_{type}.md）
- 记录保存路径

**错误处理**：记录错误但不中断流程

### 10. route_by_report_type (条件路由函数)

**功能**：根据报告类型路由到不同的生成节点

**输入**：
- `report_type`: 报告类型

**输出**：
- 目标节点名称

**路由规则**：
- `pre_market` → `pre_market_generate`
- `mid_close` → `mid_close_generate`
- `after_close` → `after_close_generate`
- 其他 → `after_close_generate` (默认)

## 工作流图

工作流图定义在 `src/workflow/graph.py`：

```python
from langgraph.graph import StateGraph, END
from src.workflow.state import ReportState
from src.workflow.nodes import (
    collect_node, clean_node, store_node, vectorize_node, rag_node,
    pre_market_generate_node, mid_close_generate_node, after_close_generate_node,
    save_node, route_by_report_type
)

def create_report_graph() -> StateGraph:
    """创建日报生成工作流图"""
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

    # 构建线性流程
    builder.add_edge("collect", "clean")
    builder.add_edge("clean", "store")
    builder.add_edge("store", "vectorize")
    builder.add_edge("vectorize", "rag")

    # 条件路由
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

    builder.add_edge("save", END)

    return builder.compile()

# 全局图实例
report_graph = create_report_graph()
```

### 工作流可视化

```
┌─────────────────────────────────────────────────────────────────┐
│                        工作流执行流程                            │
└─────────────────────────────────────────────────────────────────┘

开始
  │
  ▼
┌──────────────┐
│   collect    │  数据采集节点
│  (采集数据)   │  输出: news_data, market_data
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    clean     │  数据清洗节点
│  (清洗数据)   │  输出: cleaned_news
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    store     │  存储节点
│ (存入数据库)  │  输出: (无)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  vectorize   │  向量化节点
│  (向量化)     │  输出: (无)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     rag      │  RAG检索节点
│  (检索上下文)  │  输出: context
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│       route_by_report_type           │
│     (根据report_type路由)            │
│  pre_market → pre_market_generate   │
│  mid_close → mid_close_generate     │
│  after_close → after_close_generate │
└──────┬───────────────────────────────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│pre_market_   │  │mid_close_    │  │after_close_  │
│  generate    │  │  generate    │  │  generate    │
│(盘前早报)     │  │(盘中快讯)     │  │(盘后总结)     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                  ┌──────────────┐
                  │    save      │  保存节点
                  │  (保存报告)   │  输出: 文件 + 数据库
                  └──────┬───────┘
                         │
                         ▼
                        END
```

## 报告类型

系统支持三种报告类型，每种报告有不同的关注点和生成策略：

### 1. 盘前早报 (pre_market)

**生成时间**：开盘前 8:30

**关注点**：
- 今日市场预测
- 美股隔夜回顾
- A股开盘预测
- 重要事件前瞻

**新闻数量**：20条

**系统消息**：
```
你是专业中国金融分析师。现在是早上8:30，请生成盘前早报，
重点关注今日预测、美股隔夜回顾、A股开盘预测。用中文输出。
```

**输出文件**：`YYYY-MM-DD_pre_market.md`

### 2. 盘中快讯 (mid_close)

**生成时间**：中午收盘 11:30

**关注点**：
- 上午走势总结
- 行业资金流向
- 概念板块异动
- 实时热点追踪

**新闻数量**：15条

**系统消息**：
```
你是专业中国金融分析师。现在是中午11:30，请生成盘中快讯，
重点关注上午走势总结、行业资金流向、概念板块异动。用中文输出。
```

**输出文件**：`YYYY-MM-DD_mid_close.md`

### 3. 盘后总结 (after_close)

**生成时间**：晚间收盘 15:30

**关注点**：
- 全日行情回顾
- 资金面深度分析
- 市场深度解读
- 明日展望

**新闻数量**：20条

**系统消息**：
```
你是专业中国金融分析师。现在是下午15:30，请生成盘后深度总结，
重点关注全日行情回顾、资金面分析、深度市场解读。用中文输出。
```

**输出文件**：`YYYY-MM-DD_after_close.md`

## 配置说明

### Prompt 配置

Prompt 模板定义在 `config/prompts.py`：

```python
PRE_MARKET_PROMPT = """
当前日期: {current_date}

## 新闻数据
{news_data}

## 市场数据
{market_data}

## 历史上下文
{historical_context}

请根据以上信息，生成盘前早报，重点关注：
1. 今日市场预测
2. 美股隔夜回顾
3. A股开盘预测
4. 重要事件前瞻
"""

MID_CLOSE_PROMPT = """
当前日期: {current_date}

## 新闻数据
{news_data}

## 市场数据
{market_data}

## 历史上下文
{historical_context}

请根据以上信息，生成盘中快讯，重点关注：
1. 上午走势总结
2. 行业资金流向
3. 概念板块异动
4. 实时热点追踪
"""

AFTER_CLOSE_PROMPT = """
当前日期: {current_date}

## 新闻数据
{news_data}

## 市场数据
{market_data}

## 历史上下文
{historical_context}

请根据以上信息，生成盘后深度总结，重点关注：
1. 全日行情回顾
2. 资金面深度分析
3. 市场深度解读
4. 明日展望
"""
```

### 设置配置

配置定义在 `config/settings.py`：

```python
class Settings(BaseSettings):
    # LLM 配置
    llm: LLMConfig

    # Embedding 配置
    embedding: EmbeddingConfig

    # 调度配置
    pre_market_time: str = "08:30"
    mid_close_time: str = "11:30"
    after_close_time: str = "15:30"

    # 输出配置
    output_dir: Path = Path("outputs")

    # 日志配置
    log_level: str = "INFO"
```

## 扩展指南

### 添加新的报告类型

1. 在 `config/prompts.py` 添加新的 Prompt 模板
2. 在 `src/workflow/nodes.py` 添加新的生成节点
3. 在 `src/workflow/nodes.py` 更新 `route_by_report_type` 函数
4. 在 `src/workflow/graph.py` 添加新节点到工作流图
5. 在 `config/settings.py` 添加调度时间配置

### 添加新的工作流节点

1. 在 `src/workflow/nodes.py` 定义节点函数
2. 在 `src/workflow/graph.py` 添加节点到工作流图
3. 使用 `builder.add_edge()` 或 `builder.add_conditional_edges()` 连接节点

### 修改状态结构

1. 在 `src/workflow/state.py` 修改 `ReportState` 定义
2. 更新所有使用该状态的节点函数
3. 更新测试用例

### 自定义错误处理

每个节点都应该处理自己的错误：

```python
def my_node(state: ReportState) -> ReportState:
    try:
        # 节点逻辑
        result = do_something()
        return {**state, "new_field": result}
    except Exception as e:
        logger.error(f"节点执行失败: {e}")
        # 可以选择：
        # 1. 返回原始状态（让流程继续）
        # 2. 添加错误信息到 errors 列表
        # 3. 抛出异常（中断流程）
        return state
```

## 测试

### 单元测试

工作流组件的单元测试位于：
- `tests/test_workflow_state.py`: 状态定义测试
- `tests/test_workflow_nodes.py`: 节点函数测试
- `tests/test_workflow_graph.py`: 工作流图测试

### 集成测试

完整工作流的集成测试位于 `tests/test_workflow_integration.py`：

```bash
# 运行集成测试
pytest tests/test_workflow_integration.py -v -m integration

# 运行特定测试
pytest tests/test_workflow_integration.py::test_full_workflow_pre_market -v
```

### 测试覆盖

集成测试覆盖：
- 三种报告类型的完整流程
- 空数据处理
- 错误处理
- 状态验证

## 最佳实践

1. **保持节点简单**：每个节点只做一件事
2. **记录详细日志**：使用 `logger.info` 记录关键操作
3. **优雅处理错误**：不要让单个节点失败影响整个流程
4. **使用类型提示**：使用 TypedDict 定义状态结构
5. **编写测试**：为每个节点编写单元测试
6. **文档化**：为复杂逻辑添加注释

## 故障排查

### 工作流卡住

检查日志中是否有节点执行错误，使用 `logger.debug` 输出更多调试信息。

### 状态丢失

确保节点返回新的状态字典，而不是修改输入状态。

### 路由错误

检查 `route_by_report_type` 函数返回的节点名称是否与实际节点名称匹配。

### 性能问题

考虑使用异步节点或并行执行某些独立节点。

## 参考资源

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [LangChain 文档](https://python.langchain.com/)
- [项目 README](../README.md)
