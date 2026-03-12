# 新闻信息抽取与利用设计文档

**日期**: 2025-03-12
**状态**: 设计阶段
**作者**: Claude Code

## 概述

本设计旨在增强金融日报生成系统对新闻信源的利用。当前系统虽然通过 LLMCleaner 提取了实体、情感、重要性等信息，但这些信息在报告生成时未被充分利用。本设计通过引入深度分析节点，实现事件抽取、标的关联和智能合并，让报告生成能够基于更丰富的结构化信息。

## 目标

1. **事件抽取** - 从新闻中识别预定义的事件类型（财报类、重组并购类、政策影响类、经营类、风险类）
2. **标的关联** - 识别新闻相关的直接标的、间接标的和概念板块
3. **智能聚合** - 合并同一标的的多条新闻，避免信息重复
4. **结构化输出** - 将分析结果结构化存储，供报告生成使用

## 架构设计

### 工作流变化

**原有流程**:
```
collect → clean → store → vectorize → rag → generate → save
```

**新流程**:
```
collect → clean → analyze → store → vectorize → rag → generate → save
```

### 新增组件

#### 1. HeavyAnalyzer 类 (`src/processors/analyzer.py`)

负责对清洗后的新闻进行深度分析：

- **事件抽取**: 识别新闻所属的事件类型和子类型
- **标的关联**: 识别直接标的（明确提到的股票）、间接标的（行业）、概念板块
- **智能合并**: 合并同一标的的多条新闻
- **智能排序**: 按重要性和标的相关性排序

#### 2. analyze_node (`src/workflow/nodes.py`)

LangGraph 工作流节点，调用 HeavyAnalyzer 进行深度分析。

#### 3. 扩展 ReportState (`src/workflow/state.py`)

新增字段:
```python
enriched_news: List[Dict]  # 包含完整分析结果的结构化新闻
```

## 数据结构

### 预定义事件类型

```python
EVENT_TYPES = {
    '财报类': ['业绩预告', '财报发布', '业绩修正', '分红预案', '送转方案'],
    '重组并购类': ['收购', '兼并', '资产重组', '股权转让', '借壳上市'],
    '政策影响类': ['行业政策', '监管变化', '税收政策', '产业规划', '地方政策'],
    '经营类': ['重大合同', '产品发布', '产能扩张', '战略合作', '业务调整'],
    '风险类': ['诉讼', '处罚', '停产', '退市风险', '债务违约'],
    '其他': ['高管变更', '股东变动', '股份回购', '其他']
}
```

### enriched_news 结构

```python
{
    # 基础字段（继承自 cleaned_news）
    'title': '新闻标题',
    'content': '清洗后的内容',
    'source': '来源',
    'time': '时间',
    'entities': ['实体列表'],
    'sentiment': 'positive/neutral/negative',
    'importance': 1-5,
    'tags': ['标签列表'],

    # 新增字段
    'event_type': '事件类型（财报类/重组并购类/政策影响类/经营类/风险类/其他）',
    'event_subtype': '具体子类型（如：财报发布）',

    'related_stocks': {
        'direct': ['600519.SH:贵州茅台'],      # 直接标的
        'indirect': ['白酒行业'],                # 间接标的（行业）
        'concepts': ['白酒概念', '消费龙头']     # 概念板块
    },

    # 合并相关
    'merged_news': [  # 如果是合并的新闻，保留原始列表
        {'title': '相关新闻1', 'content': '...'},
        {'title': '相关新闻2', 'content': '...'}
    ]
}
```

## 核心逻辑

### 智能合并策略

1. **分组**: 按 `direct_stocks` 分组，同一标的的新闻归为一组
2. **合并标题**: `[N条新闻] 标的名称`
3. **综合情感**:
   - 正面新闻 > 50% → 正面
   - 负面新闻 > 50% → 负面
   - 否则 → 中性
4. **重要性**: 取最高值
5. **事件类型**: 列出所有事件类型
6. **保留原始**: merged_news 字段保存原始新闻列表

### 排序规则

1. **按重要性降序**: importance 5 > 4 > 3 > 2 > 1
2. **按直接标的数量**: 有直接标的的优先

## LLM 提示词设计

### HeavyAnalyzer 使用

```
你是专业的金融新闻分析助手。请分析以下新闻，提取事件类型和关联标的。

## 预定义事件类型
- 财报类：业绩预告、财报发布、业绩修正、分红预案、送转方案
- 重组并购类：收购、兼并、资产重组、股权转让、借壳上市
- 政策影响类：行业政策、监管变化、税收政策、产业规划、地方政策
- 经营类：重大合同、产品发布、产能扩张、战略合作、业务调整
- 风险类：诉讼、处罚、停产、退市风险、债务违约
- 其他：高管变更、股东变动、股份回购、其他

## 标的关联规则
- 直接标的：新闻明确提到的股票代码或公司名称
- 间接标的：通过公司所属行业推断
- 概念标的：相关的概念板块

## 新闻内容
{news_content}

请返回 JSON 格式：
{
    "event_type": "事件类型",
    "event_subtype": "具体子类型",
    "related_stocks": {
        "direct": ["600519.SH:贵州茅台"],
        "indirect": ["白酒行业"],
        "concepts": ["白酒概念", "消费龙头"]
    }
}
```

## 报告生成集成

### 更新 `_format_news_enriched` 函数

格式化输出包含事件类型、情感图标、标的信息：

```
- [财报类]📈 [3条新闻] 600519.SH:贵州茅台
  重要性: 5/5
  相关概念: 白酒概念, 消费龙头
```

### 生成节点更新

- `pre_market_generate_node`: 使用 `enriched_news`
- `mid_close_generate_node`: 使用 `enriched_news`
- `after_close_generate_node`: 使用 `enriched_news`

## 错误处理

### LLM 调用失败

1. **重试机制**: 最多重试 2 次
2. **回退策略**: 使用基础数据 + 默认分析字段
3. **日志记录**: 记录失败原因

### 数据验证

- 验证 `event_type` 是否在预定义列表中
- 确保 `related_stocks` 结构完整
- 处理缺失字段

## 性能考虑

- **批量处理**: 每批 10 条新闻
- **失败不影响整体**: 单条新闻分析失败不影响其他新闻
- **可选降级**: 如果分析失败，可使用 `cleaned_news` 继续流程

## 测试策略

### 单元测试

1. `test_analyze_single_news` - 测试单条新闻分析
2. `test_merge_same_stock_news` - 测试同标的新闻合并
3. `test_sort_by_importance` - 测试重要性排序
4. `test_llm_failure_fallback` - 测试 LLM 失败回退

### 集成测试

1. `test_full_workflow_with_analysis` - 测试完整工作流
2. `test_analyze_node` - 测试 analyze_node

## 实现文件清单

### 新增文件

- `src/processors/analyzer.py` - HeavyAnalyzer 类
- `tests/unit/test_analyzer.py` - HeavyAnalyzer 单元测试

### 修改文件

- `src/workflow/state.py` - 扩展 ReportState
- `src/workflow/nodes.py` - 新增 analyze_node，更新生成节点
- `src/workflow/graph.py` - 更新工作流图
- `src/generators/llm_client.py` - 新增 analyze() 方法
- `tests/test_workflow_nodes.py` - 新增 analyze_node 测试
- `tests/test_workflow_integration.py` - 扩展集成测试

## 配置变化

无需新增配置项，使用现有的 LLM 配置。

## 向后兼容性

- `cleaned_news` 字段保持不变
- 如果 `enriched_news` 为空，可回退使用 `cleaned_news`
- 现有测试可继续运行

## 后续优化方向

1. **标的识别增强**: 使用股票数据库提高标的识别准确率
2. **事件图谱**: 构建事件关联图谱，发现事件间的因果关系
3. **历史对比**: 与历史事件对比，识别趋势和异常
4. **个性化**: 根据用户关注的股票/行业定制分析策略
