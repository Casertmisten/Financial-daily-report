# 新闻信息抽取与利用实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在金融日报生成系统中新增深度分析节点，实现事件抽取、标的关联和智能新闻聚合

**Architecture:** 在现有 LangGraph 工作流的 clean_node 之后新增 analyze_node，使用 HeavyAnalyzer 类对新闻进行深度分析（事件类型识别、标的关联），智能合并同一标的的多条新闻，生成包含丰富元数据的 enriched_news 供报告生成使用

**Tech Stack:** Python 3.10+, LangGraph, OpenAI-compatible LLM API, SQLite

---

## 文件结构映射

### 新增文件
- `src/processors/analyzer.py` - HeavyAnalyzer 类，负责深度分析和新闻聚合
- `tests/unit/test_analyzer.py` - HeavyAnalyzer 单元测试

### 修改文件
- `src/workflow/state.py` - 扩展 ReportState，添加 enriched_news 字段
- `src/workflow/nodes.py` - 新增 analyze_node，新增 _format_news_enriched 函数
- `src/workflow/graph.py` - 将 analyze_node 添加到工作流图中
- `src/generators/llm_client.py` - 新增 analyze() 方法用于深度分析
- `src/storage/database.py` - 扩展 Database 类，新增 news_analysis 表和存储方法
- `tests/test_workflow_nodes.py` - 新增 analyze_node 测试
- `tests/test_workflow_integration.py` - 扩展集成测试

---

## Chunk 1: 扩展 ReportState 和 LLMClient

### Task 1: 扩展 ReportState

**Files:**
- Modify: `src/workflow/state.py`

- [ ] **Step 1: 查看当前 ReportState 定义**

```bash
cat src/workflow/state.py
```

- [ ] **Step 2: 添加 enriched_news 字段到 ReportState**

在 ReportState TypedDict 中添加新字段：

```python
class ReportState(TypedDict):
    """日报生成的状态对象"""
    report_type: str
    news_data: List[Dict]
    market_data: Dict
    cleaned_news: List[Dict]
    enriched_news: List[Dict]   # 新增：包含事件类型和标的关联的新闻
    context: str
    report: str
    errors: List[str]
```

- [ ] **Step 3: 验证语法正确性**

```bash
python -c "from src.workflow.state import ReportState; print('✓ ReportState 导入成功')"
```

预期输出: ✓ ReportState 导入成功

- [ ] **Step 4: 运行现有测试确保没有破坏**

```bash
uv run pytest tests/test_workflow_state.py -v
```

预期: 所有测试通过

- [ ] **Step 5: 提交更改**

```bash
git add src/workflow/state.py
git commit -m "feat: extend ReportState with enriched_news field"
```

### Task 2: 扩展 LLMClient 新增 analyze() 方法

**Files:**
- Modify: `src/generators/llm_client.py`

- [ ] **Step 1: 编写 analyze() 方法的测试先创建测试文件**

创建测试文件 `tests/unit/test_llm_analyze.py`:

```python
import pytest
from unittest.mock import Mock, patch
from src.generators.llm_client import LLMClient

def test_analyze_returns_valid_structure():
    """测试 analyze 方法返回正确的数据结构"""
    client = LLMClient()

    # Mock LLM 响应
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '''{
        "event_type": "财报类",
        "event_subtype": "财报发布",
        "related_stocks": {
            "direct": ["600519.SH:贵州茅台"],
            "indirect": ["白酒行业"],
            "concepts": ["白酒概念"]
        }
    }'''

    with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
        result = client.analyze("贵州茅台发布财报")

    assert result["event_type"] == "财报类"
    assert result["event_subtype"] == "财报发布"
    assert "600519.SH:贵州茅台" in result["related_stocks"]["direct"]

def test_analyze_handles_json_parse_error():
    """测试 analyze 方法处理 JSON 解析错误"""
    client = LLMClient()

    # Mock 返回无效 JSON
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "invalid json"

    with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
        result = client.analyze("测试新闻")

    # 应该返回默认值
    assert result["event_type"] == "其他"
    assert result["related_stocks"]["direct"] == []

def test_analyze_handles_llm_error():
    """测试 analyze 方法处理 LLM 调用错误"""
    client = LLMClient()

    with patch.object(client.client.chat.completions, 'create', side_effect=Exception("LLM error")):
        result = client.analyze("测试新闻")

    # 应该返回默认值
    assert result["event_type"] == "其他"
    assert result["related_stocks"]["direct"] == []
```

- [ ] **Step 2: 运行测试验证失败（方法尚未实现）**

```bash
uv run pytest tests/unit/test_llm_analyze.py -v
```

预期: FAIL - analyze 方法不存在

- [ ] **Step 3: 在 LLMClient 类中实现 analyze() 方法和辅助方法**

在 `src/generators/llm_client.py` 的 LLMClient 类末尾添加：

```python
def analyze(
    self,
    text: str,
    model: Optional[str] = None,
    temperature: float = 0.3,
    **kwargs
) -> Dict:
    """
    深度分析接口，提取事件类型和标的关联

    Args:
        text: 待分析的文本，格式：标题 + 内容
        model: 使用的模型，默认使用 clean_model
        temperature: 温度参数，使用较低温度保证稳定性

    Returns:
        分析结果字典：
        {
            "event_type": "事件类型（从预定义列表选择）",
            "event_subtype": "具体子类型",
            "related_stocks": {
                "direct": ["代码:名称", ...],
                "indirect": ["行业", ...],
                "concepts": ["概念", ...]
            }
    }
    """
    model = model or self.clean_model

    system_prompt = """你是专业的金融新闻分析助手。请分析以下新闻，提取事件类型和关联标的。

## 预定义事件类型
- 财报类：业绩预告、财报发布、业绩修正、分红预案、送转方案
- 重组并购类：收购、兼并、资产重组、股权转让、借壳上市
- 政策影响类：行业政策、监管变化、税收政策、产业规划、地方政策
- 经营类：重大合同、产品发布、产能扩张、战略合作、业务调整
- 风险类：诉讼、处罚、停产、退市风险、债务违约
- 其他：高管变更、股东变动、股份回购、其他

## 标的关联规则
- 直接标的：新闻明确提到的股票代码或公司名称，格式：代码:名称
- 间接标的：通过公司所属行业推断
- 概念标的：相关的概念板块

请严格按照 JSON 格式返回：
{
    "event_type": "事件类型（从预定义列表中选择）",
    "event_subtype": "具体子类型",
    "related_stocks": {
        "direct": ["股票代码:公司名称"],
        "indirect": ["相关行业"],
        "concepts": ["相关概念板块"]
    }
}"""

    try:
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

        # 验证和修正结果
        result = self._validate_analysis_result(result)
        logger.debug(f"LLM analyze 成功")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"LLM analyze JSON 解析失败: {e}")
        return self._get_default_analysis_result()
    except Exception as e:
        logger.error(f"LLM analyze 失败: {e}")
        return self._get_default_analysis_result()

def _validate_analysis_result(self, result: Dict) -> Dict:
    """验证和修正分析结果"""
    valid_event_types = [
        '财报类', '重组并购类', '政策影响类',
        '经营类', '风险类', '其他'
    ]

    # 验证事件类型
    if result.get('event_type') not in valid_event_types:
        logger.warning(f"无效事件类型 '{result.get('event_type')}'，使用默认值 '其他'")
        result['event_type'] = '其他'

    # 验证 related_stocks 结构
    if 'related_stocks' not in result:
        result['related_stocks'] = {}

    stocks = result['related_stocks']
    for key in ['direct', 'indirect', 'concepts']:
        if key not in stocks:
            stocks[key] = []
        if not isinstance(stocks[key], list):
            logger.warning(f"related_stocks.{key} 应为列表，已修正")
            stocks[key] = []

    return result

def _get_default_analysis_result(self) -> Dict:
    """返回默认的分析结果"""
    return {
        "event_type": "其他",
        "event_subtype": "",
        "related_stocks": {
            "direct": [],
            "indirect": [],
            "concepts": []
        }
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_llm_analyze.py -v
```

预期: PASS - 所有测试通过

- [ ] **Step 5: 提交更改**

```bash
git add src/generators/llm_client.py tests/unit/test_llm_analyze.py
git commit -m "feat: add analyze() method to LLMClient for news deep analysis"
```

---

## Chunk 2: 实现 HeavyAnalyzer 类

### Task 3: 创建 HeavyAnalyzer 类框架和测试

**Files:**
- Create: `src/processors/analyzer.py`
- Create: `tests/unit/test_analyzer.py`

- [ ] **Step 1: 创建测试文件并编写基础测试**

创建 `tests/unit/test_analyzer.py`:

```python
import pytest
from unittest.mock import Mock, patch
from src.processors.analyzer import HeavyAnalyzer

def test_analyzer_init():
    """测试 HeavyAnalyzer 初始化"""
    analyzer = HeavyAnalyzer(batch_size=5)
    assert analyzer.batch_size == 5
    assert analyzer.llm_client is not None

def test_analyze_empty_list():
    """测试分析空列表"""
    analyzer = HeavyAnalyzer()
    result = analyzer.analyze([])
    assert result == []

def test_analyze_single_news_with_mock():
    """测试分析单条新闻（使用 mock）"""
    analyzer = HeavyAnalyzer()

    # Mock LLM 返回
    mock_llm_result = {
        'event_type': '财报类',
        'event_subtype': '财报发布',
        'related_stocks': {
            'direct': ['600519.SH:贵州茅台'],
            'indirect': ['白酒行业'],
            'concepts': ['白酒概念']
        }
    }

    news = [{
        'title': '贵州茅台发布财报',
        'content': '营收增长20%',
        'sentiment': 'positive',
        'importance': 5,
        'source': 'test',
        'time': '2024-01-01'
    }]

    with patch.object(analyzer.llm_client, 'analyze', return_value=mock_llm_result):
        result = analyzer.analyze(news)

    assert len(result) == 1
    assert result[0]['event_type'] == '财报类'
    assert result[0]['related_stocks']['direct'] == ['600519.SH:贵州茅台']

def test_merge_same_stock_news():
    """测试合并同一标的的多条新闻"""
    analyzer = HeavyAnalyzer()

    news = [
        {
            'title': '茅台新闻1',
            'content': '内容1',
            'sentiment': 'positive',
            'importance': 4,
            'source': 'test',
            'time': '2024-01-01',
            'event_type': '财报类',
            'related_stocks': {
                'direct': ['600519.SH:贵州茅台'],
                'indirect': [],
                'concepts': []
            }
        },
        {
            'title': '茅台新闻2',
            'content': '内容2',
            'sentiment': 'positive',
            'importance': 3,
            'source': 'test',
            'time': '2024-01-01',
            'event_type': '经营类',
            'related_stocks': {
                'direct': ['600519.SH:贵州茅台'],
                'indirect': [],
                'concepts': []
            }
        }
    ]

    result = analyzer._merge_by_stock(news)

    # 应该合并成一条
    assert len(result) == 1
    assert '[2条新闻]' in result[0]['title']
    assert result[0]['importance'] == 4  # 取最高值

def test_sort_by_importance():
    """测试按重要性排序"""
    analyzer = HeavyAnalyzer()

    news = [
        {'title': '低重要性', 'importance': 2, 'related_stocks': {'direct': []}},
        {'title': '高重要性', 'importance': 5, 'related_stocks': {'direct': []}},
        {'title': '中重要性', 'importance': 3, 'related_stocks': {'direct': []}}
    ]

    result = analyzer._sort_by_importance(news)

    assert result[0]['title'] == '高重要性'
    assert result[1]['title'] == '中重要性'
    assert result[2]['title'] == '低重要性'

def test_analyze_llm_failure_fallback():
    """测试 LLM 调用失败时的回退逻辑"""
    analyzer = HeavyAnalyzer()

    news = [{'title': '测试', 'content': '内容'}]

    with patch.object(analyzer.llm_client, 'analyze', side_effect=Exception('LLM error')):
        result = analyzer.analyze(news)

    # 应该回退到基础数据
    assert len(result) == 1
    assert result[0]['event_type'] == '其他'
    assert result[0]['related_stocks']['direct'] == []
```

- [ ] **Step 2: 运行测试验证失败（类尚未创建）**

```bash
uv run pytest tests/unit/test_analyzer.py -v
```

预期: FAIL - HeavyAnalyzer 不存在

- [ ] **Step 3: 创建 HeavyAnalyzer 类框架**

创建 `src/processors/analyzer.py`:

```python
"""新闻深度分析模块

负责对清洗后的新闻进行事件抽取、标的关联和智能聚合
"""
from loguru import logger
from typing import List, Dict
from src.generators.llm_client import llm_client


class HeavyAnalyzer:
    """深度分析器，对新闻进行事件抽取和标的关联"""

    def __init__(self, batch_size: int = 10):
        """
        初始化分析器

        Args:
            batch_size: 批处理大小，每批 N 条新闻进行一次 LLM 调用
        """
        self.llm_client = llm_client
        self.batch_size = batch_size

    def analyze(self, news_list: List[Dict]) -> List[Dict]:
        """
        对新闻列表进行深度分析

        流程：批量分析 → 智能合并 → 排序

        Args:
            news_list: 来自 LLMCleaner 的 cleaned_news

        Returns:
            enriched_news: 包含事件类型和标的关联的新闻列表
        """
        if not news_list:
            return []

        # 1. 批量调用 LLM 进行事件抽取和标的关联
        analyzed = self._batch_analyze(news_list)

        # 2. 智能合并同一标的的新闻
        merged = self._merge_by_stock(analyzed)

        # 3. 按重要性排序
        sorted_news = self._sort_by_importance(merged)

        return sorted_news

    def _batch_analyze(self, news_list: List[Dict]) -> List[Dict]:
        """批量调用 LLM 进行事件抽取和标的关联"""
        analyzed = []

        for news in news_list:
            try:
                # 构建分析文本
                text = f"标题: {news.get('title', '')}\n内容: {news.get('content', '')}"

                # 调用 LLM 分析
                analysis_result = self.llm_client.analyze(text)

                # 合并原始新闻和分析结果
                enriched = {
                    **news,
                    'event_type': analysis_result.get('event_type', '其他'),
                    'event_subtype': analysis_result.get('event_subtype', ''),
                    'related_stocks': analysis_result.get('related_stocks', {
                        'direct': [],
                        'indirect': [],
                        'concepts': []
                    })
                }
                analyzed.append(enriched)

            except Exception as e:
                logger.warning(f"深度分析失败，使用基础数据: {e}")
                # 回退到基础数据，添加默认的分析字段
                fallback = {
                    **news,
                    'event_type': '其他',
                    'event_subtype': '',
                    'related_stocks': {
                        'direct': [],
                        'indirect': [],
                        'concepts': []
                    }
                }
                analyzed.append(fallback)

        return analyzed

    def _merge_by_stock(self, news_list: List[Dict]) -> List[Dict]:
        """
        按直接标的分组，合并同一标的的多条新闻

        合并策略：
        - 按 direct_stocks 分组
        - 同一标的的多条新闻合并成一条
        - 综合情感判断（正面>50%→正面，负面>50%→负面）
        - 重要性取最高值
        - 列出所有事件类型
        - merged_news 保存原始新闻列表
        """
        # 按直接标的分组
        stock_groups = {}
        for news in news_list:
            direct_stocks = news.get('related_stocks', {}).get('direct', [])

            if not direct_stocks:
                # 无关联标的的新闻单独一组
                key = '_no_stock_'
            else:
                # 使用第一个直接标的作为分组键
                key = direct_stocks[0]

            if key not in stock_groups:
                stock_groups[key] = []
            stock_groups[key].append(news)

        # 合并每个组
        merged = []
        for stock, news_group in stock_groups.items():
            if len(news_group) == 1:
                # 单条新闻直接保留
                merged.append(news_group[0])
            else:
                # 多条新闻合并
                merged_item = self._merge_news_group(news_group)
                merged.append(merged_item)

        return merged

    def _merge_news_group(self, news_group: List[Dict]) -> Dict:
        """合并同一标的的多条新闻为一条"""
        # 提取标的信息
        first = news_group[0]
        stock_name = first.get('related_stocks', {}).get('direct', ['未知'])[0]

        # 综合情感
        sentiments = [n.get('sentiment', 'neutral') for n in news_group]
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')

        if positive_count > len(news_group) / 2:
            combined_sentiment = 'positive'
        elif negative_count > len(news_group) / 2:
            combined_sentiment = 'negative'
        else:
            combined_sentiment = 'neutral'

        # 收集所有事件类型
        event_types = set()
        for news in news_group:
            event_type = news.get('event_type', '其他')
            event_types.add(event_type)

        # 生成合并后的内容摘要
        content_parts = []
        for news in news_group:
            event_subtype = news.get('event_subtype', '')
            content_preview = news.get('content', '')[:50]
            content_parts.append(f"- {event_subtype}: {content_preview}")

        merged_content = '\n'.join(content_parts)

        return {
            'title': f"[{len(news_group)}条新闻] {stock_name}",
            'content': merged_content,
            'source': first.get('source', ''),
            'time': first.get('time', ''),
            'entities': list(set([e for n in news_group for e in n.get('entities', [])])),
            'sentiment': combined_sentiment,
            'importance': max([n.get('importance', 3) for n in news_group]),
            'tags': list(set([t for n in news_group for t in n.get('tags', [])])),
            'event_type': ', '.join(sorted(event_types)),
            'event_subtype': '',
            'related_stocks': first.get('related_stocks', {}),
            'merged_news': news_group  # 保留原始新闻
        }

    def _sort_by_importance(self, news_list: List[Dict]) -> List[Dict]:
        """
        按重要性和直接标的数量排序

        排序规则：
        1. 按重要性降序: importance 5 > 4 > 3 > 2 > 1
        2. 按直接标的数量: 有直接标的的优先
        """
        return sorted(
            news_list,
            key=lambda x: (
                -x.get('importance', 3),  # 重要性降序
                -len(x.get('related_stocks', {}).get('direct', []))  # 直接标的数量降序
            )
        )
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_analyzer.py -v
```

预期: PASS - 所有测试通过

- [ ] **Step 5: 提交更改**

```bash
git add src/processors/analyzer.py tests/unit/test_analyzer.py
git commit -m "feat: implement HeavyAnalyzer for news deep analysis and merging"
```

---

## Chunk 3: 实现工作流节点集成

### Task 4: 实现 analyze_node

**Files:**
- Modify: `src/workflow/nodes.py`

- [ ] **Step 1: 编写 analyze_node 的测试**

在 `tests/test_workflow_nodes.py` 中添加：

```python
def test_analyze_node_with_news():
    """测试 analyze_node 处理新闻"""
    from src.workflow.nodes import analyze_node

    cleaned_news = [
        {
            'title': '测试新闻',
            'content': '测试内容',
            'sentiment': 'neutral',
            'importance': 3,
            'source': 'test',
            'time': '2024-01-01'
        }
    ]

    state = {
        'report_type': 'after_close',
        'news_data': [],
        'market_data': {},
        'cleaned_news': cleaned_news,
        'enriched_news': [],
        'context': '',
        'report': '',
        'errors': []
    }

    # Mock HeavyAnalyzer
    with patch('src.workflow.nodes.HeavyAnalyzer') as mock_analyzer_class:
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = [
            {
                'title': '测试新闻',
                'event_type': '其他',
                'related_stocks': {'direct': [], 'indirect': [], 'concepts': []}
            }
        ]
        mock_analyzer_class.return_value = mock_analyzer

        result = analyze_node(state)

    assert 'enriched_news' in result
    assert len(result['enriched_news']) == 1

def test_analyze_node_empty_news():
    """测试 analyze_node 处理空新闻"""
    from src.workflow.nodes import analyze_node

    state = {
        'report_type': 'after_close',
        'news_data': [],
        'market_data': {},
        'cleaned_news': [],
        'enriched_news': [],
        'context': '',
        'report': '',
        'errors': []
    }

    result = analyze_node(state)

    assert result['enriched_news'] == []

def test_analyze_node_failure_fallback():
    """测试 analyze_node 失败时回退到 cleaned_news"""
    from src.workflow.nodes import analyze_node

    cleaned_news = [
        {
            'title': '测试新闻',
            'content': '测试内容',
            'sentiment': 'neutral',
            'importance': 3
        }
    ]

    state = {
        'report_type': 'after_close',
        'news_data': [],
        'market_data': {},
        'cleaned_news': cleaned_news,
        'enriched_news': [],
        'context': '',
        'report': '',
        'errors': []
    }

    # Mock HeavyAnalyzer 抛出异常
    with patch('src.workflow.nodes.HeavyAnalyzer', side_effect=Exception('Analysis failed')):
        result = analyze_node(state)

    # 应该回退到 cleaned_news 并添加默认字段
    assert 'enriched_news' in result
    assert len(result['enriched_news']) == 1
    assert result['enriched_news'][0]['event_type'] == '其他'
```

- [ ] **Step 2: 运行测试验证失败（节点尚未实现）**

```bash
uv run pytest tests/test_workflow_nodes.py::test_analyze_node_with_news -v
```

预期: FAIL - analyze_node 不存在

- [ ] **Step 3: 在 nodes.py 中实现 analyze_node**

在 `src/workflow/nodes.py` 中添加：

```python
def analyze_node(state: ReportState) -> ReportState:
    """深度分析节点

    对清洗后的新闻进行事件抽取、标的关联、智能合并

    Args:
        state: 当前状态，包含 cleaned_news

    Returns:
        更新后的状态，包含 enriched_news
    """
    logger.info("=== 深度分析 ===")

    if not state["cleaned_news"]:
        logger.info("无新闻需要分析")
        return {**state, "enriched_news": []}

    try:
        from src.processors.analyzer import HeavyAnalyzer
        analyzer = HeavyAnalyzer()
        enriched = analyzer.analyze(state["cleaned_news"])
        logger.info(f"✓ 深度分析完成，保留 {len(enriched)} 条")

        # 打印统计信息
        event_types = {}
        for news in enriched:
            et = news.get('event_type', '其他')
            event_types[et] = event_types.get(et, 0) + 1
        logger.info(f"事件类型分布: {event_types}")

        return {**state, "enriched_news": enriched}

    except Exception as e:
        logger.error(f"深度分析失败，使用 cleaned_news: {e}")
        # 回退：将 cleaned_news 作为 enriched_news 返回
        # 添加默认的分析字段
        fallback = [
            {
                **news,
                'event_type': '其他',
                'event_subtype': '',
                'related_stocks': {'direct': [], 'indirect': [], 'concepts': []}
            }
            for news in state["cleaned_news"]
        ]
        return {**state, "enriched_news": fallback}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_workflow_nodes.py::test_analyze_node_with_news -v
uv run pytest tests/test_workflow_nodes.py::test_analyze_node_empty_news -v
uv run pytest tests/test_workflow_nodes.py::test_analyze_node_failure_fallback -v
```

预期: PASS - 所有测试通过

- [ ] **Step 5: 提交更改**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: add analyze_node for news deep analysis in workflow"
```

### Task 5: 实现 _format_news_enriched 函数

**Files:**
- Modify: `src/workflow/nodes.py`

- [ ] **Step 1: 编写 _format_news_enriched 测试**

在 `tests/test_workflow_nodes.py` 中添加：

```python
def test_format_news_enriched():
    """测试格式化增强后的新闻"""
    from src.workflow.nodes import _format_news_enriched

    enriched_news = [
        {
            'title': '[3条新闻] 600519.SH:贵州茅台',
            'event_type': '财报类',
            'sentiment': 'positive',
            'importance': 5,
            'related_stocks': {
                'direct': ['600519.SH:贵州茅台'],
                'concepts': ['白酒概念', '消费龙头']
            }
        }
    ]

    result = _format_news_enriched(enriched_news, focus="analysis")

    assert '[财报类]' in result
    assert '📈' in result
    assert '600519.SH:贵州茅台' in result
    assert '重要性: 5/5' in result
    assert '白酒概念' in result

def test_format_news_enriched_empty():
    """测试格式化空新闻列表"""
    from src.workflow.nodes import _format_news_enriched

    result = _format_news_enriched([])

    assert result == "暂无新闻数据"

def test_format_news_enriched_respects_limit():
    """测试格式化遵守数量限制"""
    from src.workflow.nodes import _format_news_enriched

    # 创建 25 条新闻
    enriched_news = [
        {
            'title': f'新闻{i}',
            'event_type': '其他',
            'sentiment': 'neutral',
            'importance': 3,
            'related_stocks': {'direct': [], 'concepts': []}
        }
        for i in range(25)
    ]

    result = _format_news_enriched(enriched_news, focus="analysis")
    lines = result.split('\n')

    # focus="analysis" 应该限制为 20 条
    # 每条新闻 2 行（标题行 + 重要性行）
    assert len([l for l in lines if l.startswith('-')]) <= 20
```

- [ ] **Step 2: 运行测试验证失败（函数尚未实现）**

```bash
uv run pytest tests/test_workflow_nodes.py::test_format_news_enriched -v
```

预期: FAIL - _format_news_enriched 不存在

- [ ] **Step 3: 在 nodes.py 中实现 _format_news_enriched**

在 `src/workflow/nodes.py` 中添加（与 `_format_news` 函数并列）：

```python
def _format_news_enriched(news_data: List[Dict], focus: str = "analysis") -> str:
    """
    格式化增强后的新闻数据（包含事件类型和标的）

    Args:
        news_data: enriched_news 列表
        focus: 关注点，决定显示的新闻数量

    Returns:
        格式化的新闻文本，包含事件和标的信息
    """
    if not news_data:
        return "暂无新闻数据"

    formatted = []
    limit = 20 if focus == "analysis" else 15

    for item in news_data[:limit]:
        title = item.get('title', '')
        event_type = item.get('event_type', '其他')
        sentiment = item.get('sentiment', 'neutral')
        importance = item.get('importance', 3)

        # 标的信息
        stocks = item.get('related_stocks', {})
        direct = stocks.get('direct', [])
        concepts = stocks.get('concepts', [])

        # 情感图标
        sentiment_icon = {'positive': '📈', 'neutral': '➡️', 'negative': '📉'}

        # 构建格式化输出
        stock_info = ''
        if direct:
            stock_info = f" [{', '.join(direct)}]"

        line = f"- [{event_type}]{sentiment_icon.get(sentiment, '')} {title}{stock_info}"
        formatted.append(line)
        formatted.append(f"  重要性: {importance}/5")

        if concepts:
            formatted.append(f"  相关概念: {', '.join(concepts[:3])}")

    return '\n'.join(formatted)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_workflow_nodes.py::test_format_news_enriched -v
uv run pytest tests/test_workflow_nodes.py::test_format_news_enriched_empty -v
uv run pytest tests/test_workflow_nodes.py::test_format_news_enriched_respects_limit -v
```

预期: PASS - 所有测试通过

- [ ] **Step 5: 提交更改**

```bash
git add src/workflow/nodes.py tests/test_workflow_nodes.py
git commit -m "feat: add _format_news_enriched function for enhanced news formatting"
```

### Task 6: 更新生成节点使用 enriched_news

**Files:**
- Modify: `src/workflow/nodes.py`

- [ ] **Step 1: 更新 pre_market_generate_node 使用 enriched_news**

在 `src/workflow/nodes.py` 中找到 `pre_market_generate_node` 函数（约第247行），找到：

```python
def pre_market_generate_node(state: ReportState) -> ReportState:
    """盘前早报生成节点"""
    logger.info("=== 生成盘前早报 ===")

    news_summary = _format_news(state["cleaned_news"], focus="prediction")
    market_summary = _format_market(state["market_data"], focus="pre_market")
```

将 `_format_news(state["cleaned_news"], focus="prediction")` 改为 `_format_news_enriched(state["enriched_news"], focus="prediction")`

修改后：
```python
def pre_market_generate_node(state: ReportState) -> ReportState:
    """盘前早报生成节点"""
    logger.info("=== 生成盘前早报 ===")

    news_summary = _format_news_enriched(state["enriched_news"], focus="prediction")
    market_summary = _format_market(state["market_data"], focus="pre_market")
```

- [ ] **Step 2: 更新 mid_close_generate_node 使用 enriched_news**

在 `src/workflow/nodes.py` 中找到 `mid_close_generate_node` 函数（约第286行），找到：

```python
def mid_close_generate_node(state: ReportState) -> ReportState:
    """盘中快讯生成节点"""
    logger.info("=== 生成盘中快讯 ===")

    news_summary = _format_news(state["cleaned_news"], focus="intraday")
```

将 `_format_news(state["cleaned_news"], focus="intraday")` 改为 `_format_news_enriched(state["enriched_news"], focus="intraday")`

修改后：
```python
def mid_close_generate_node(state: ReportState) -> ReportState:
    """盘中快讯生成节点"""
    logger.info("=== 生成盘中快讯 ===")

    news_summary = _format_news_enriched(state["enriched_news"], focus="intraday")
```

- [ ] **Step 3: 更新 after_close_generate_node 使用 enriched_news**

在 `src/workflow/nodes.py` 中找到 `after_close_generate_node` 函数（约第325行），找到：

```python
def after_close_generate_node(state: ReportState) -> ReportState:
    """盘后总结生成节点"""
    logger.info("=== 生成盘后总结 ===")

    news_summary = _format_news(state["cleaned_news"], focus="analysis")
```

将 `_format_news(state["cleaned_news"], focus="analysis")` 改为 `_format_news_enriched(state["enriched_news"], focus="analysis")`

修改后：
```python
def after_close_generate_node(state: ReportState) -> ReportState:
    """盘后总结生成节点"""
    logger.info("=== 生成盘后总结 ===")

    news_summary = _format_news_enriched(state["enriched_news"], focus="analysis")
```

- [ ] **Step 4: 运行工作流测试确保没有破坏**

```bash
uv run pytest tests/test_workflow_integration.py -v
```

预期: PASS - 所有集成测试通过

- [ ] **Step 5: 提交更改**

```bash
git add src/workflow/nodes.py
git commit -m "refactor: update generate nodes to use enriched_news"
```

---

## Chunk 4: 更新工作流图

### Task 7: 在工作流图中添加 analyze_node

**Files:**
- Modify: `src/workflow/graph.py`

- [ ] **Step 1: 查看当前工作流图定义**

```bash
cat src/workflow/graph.py
```

- [ ] **Step 2: 在 imports 中添加 analyze_node**

在 `from src.workflow.nodes import ...` 中添加 `analyze_node`：

```python
from src.workflow.nodes import (
    collect_node, clean_node, store_node, vectorize_node, rag_node,
    pre_market_generate_node, mid_close_generate_node, after_close_generate_node,
    save_node, route_by_report_type, analyze_node  # 新增 analyze_node
)
```

- [ ] **Step 3: 在 builder 中添加 analyze_node**

在 `builder.add_node("clean", clean_node)` 后添加：

```python
builder.add_node("analyze", analyze_node)
```

- [ ] **Step 4: 更新工作流边连接**

将 `builder.add_edge("clean", "store")` 改为：

```python
builder.add_edge("clean", "analyze")
builder.add_edge("analyze", "store")
```

- [ ] **Step 5: 验证工作流图正确性**

```bash
uv run python -c "
from src.workflow.graph import report_graph
print('✓ 工作流图加载成功')
# 打印节点列表
print('节点:', list(report_graph.nodes.keys()))
"
```

预期输出: ✓ 工作流图加载成功
预期节点包含: collect, clean, analyze, store, vectorize, rag, ...

- [ ] **Step 6: 运行工作流图测试**

```bash
uv run pytest tests/test_workflow_graph.py -v
```

预期: PASS - 所有测试通过

- [ ] **Step 7: 提交更改**

```bash
git add src/workflow/graph.py
git commit -m "feat: add analyze_node to workflow graph"
```

---

## Chunk 5: 扩展数据库存储

### Task 8: 扩展 Database 类新增 news_analysis 表

**Files:**
- Modify: `src/storage/database.py`

- [ ] **Step 1: 查看当前数据库定义**

```bash
cat src/storage/database.py
```

- [ ] **Step 2: 修改 save_news 方法返回 news_id 列表**

首先需要修改 `save_news` 方法，使其返回插入的新闻 ID 列表。找到 `save_news` 方法（约第54行）：

```python
def save_news(self, news_list: List[Dict]):
    """
    保存新闻到数据库

    Args:
        news_list: 新闻列表，每项包含title, content, source, time等字段
    """
    if not news_list:
        logger.warning("新闻列表为空，跳过保存")
        return

    cursor = self.conn.cursor()
    for news in news_list:
        cursor.execute("""
            INSERT INTO news (title, content, source, publish_time)
            VALUES (?, ?, ?, ?)
        """, (
            news.get('title', ''),
            news.get('content', '') or news.get('cleaned_content', ''),
            news.get('source', ''),
            news.get('time', '')
        ))
    self.conn.commit()
    logger.info(f"保存新闻: {len(news_list)} 条")
```

修改为返回插入的 ID 列表：

```python
def save_news(self, news_list: List[Dict]) -> List[int]:
    """
    保存新闻到数据库

    Args:
        news_list: 新闻列表，每项包含title, content, source, time等字段

    Returns:
        插入的新闻 ID 列表
    """
    if not news_list:
        logger.warning("新闻列表为空，跳过保存")
        return []

    cursor = self.conn.cursor()
    news_ids = []
    for news in news_list:
        cursor.execute("""
            INSERT INTO news (title, content, source, publish_time)
            VALUES (?, ?, ?, ?)
        """, (
            news.get('title', ''),
            news.get('content', '') or news.get('cleaned_content', ''),
            news.get('source', ''),
            news.get('time', '')
        ))
        news_ids.append(cursor.lastrowid)
    self.conn.commit()
    logger.info(f"保存新闻: {len(news_list)} 条")
    return news_ids
```

- [ ] **Step 3: 在 _create_tables 方法中添加 news_analysis 表**

在创建 `reports` 表后添加：

```python
# 新闻分析表
cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_id INTEGER,
        event_type TEXT,
        event_subtype TEXT,
        direct_stocks TEXT,
        indirect_stocks TEXT,
        concepts TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (news_id) REFERENCES news(id)
    )
""")
```

- [ ] **Step 4: 添加 save_news_analysis 方法**

在 Database 类中添加（需要先在文件顶部添加 `import json`）：

```python
def save_news_analysis(self, analysis_list: List[Dict]) -> List[int]:
    """
    保存新闻分析结果到数据库

    Args:
        analysis_list: 分析结果列表，每项必须包含 news_id 字段

    Returns:
        插入的分析记录 ID 列表

    注意：
        analysis_list 中的每一项必须包含 'news_id' 字段，
        该 ID 应该来自 save_news() 方法的返回值
    """
    if not analysis_list:
        logger.warning("分析列表为空，跳过保存")
        return []

    cursor = self.conn.cursor()
    analysis_ids = []

    for analysis in analysis_list:
        # 验证 news_id 存在
        if 'news_id' not in analysis:
            logger.warning(f"分析记录缺少 news_id，跳过: {analysis.get('title', '未知')}")
            continue

        # 将列表转换为 JSON 字符串存储
        direct_stocks = json.dumps(analysis.get('related_stocks', {}).get('direct', []), ensure_ascii=False)
        indirect_stocks = json.dumps(analysis.get('related_stocks', {}).get('indirect', []), ensure_ascii=False)
        concepts = json.dumps(analysis.get('related_stocks', {}).get('concepts', []), ensure_ascii=False)

        cursor.execute("""
            INSERT INTO news_analysis (news_id, event_type, event_subtype, direct_stocks, indirect_stocks, concepts)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            analysis.get('news_id'),
            analysis.get('event_type', ''),
            analysis.get('event_subtype', ''),
            direct_stocks,
            indirect_stocks,
            concepts
        ))
        analysis_ids.append(cursor.lastrowid)

    self.conn.commit()
    logger.info(f"保存新闻分析: {len(analysis_ids)} 条")
    return analysis_ids
```

- [ ] **Step 5: 添加 save_enriched_news 方法保存完整流程**

为了方便使用，添加一个方法来同时保存新闻和分析结果：

```python
def save_enriched_news(self, news_list: List[Dict], analysis_list: List[Dict]) -> Dict[str, List[int]]:
    """
    保存新闻和分析结果（完整流程）

    Args:
        news_list: 新闻列表（来自 cleaned_news）
        analysis_list: 分析结果列表（来自 enriched_news）

    Returns:
        {
            'news_ids': [插入的新闻 ID 列表],
            'analysis_ids': [插入的分析 ID 列表]
        }

    注意：
        news_list 和 analysis_list 应该长度相同且一一对应
        自动将 news_id 关联到 analysis_list 中的对应项
    """
    # 先保存新闻
    news_ids = self.save_news(news_list)

    # 将 news_id 添加到分析结果中
    for i, analysis in enumerate(analysis_list):
        if i < len(news_ids):
            analysis['news_id'] = news_ids[i]

    # 保存分析结果
    analysis_ids = self.save_news_analysis(analysis_list)

    return {
        'news_ids': news_ids,
        'analysis_ids': analysis_ids
    }
```
```

- [ ] **Step 4: 验证数据库创建正确**

```bash
uv run python -c "
from src.storage.database import database
import sqlite3
# 检查表是否存在
cursor = database.conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='news_analysis'\")
result = cursor.fetchone()
if result:
    print('✓ news_analysis 表已创建')
else:
    print('✗ news_analysis 表未创建')
"
```

预期: ✓ news_analysis 表已创建

- [ ] **Step 6: 添加 save_enriched_news 方法保存完整流程**

为了方便使用，添加一个方法来同时保存新闻和分析结果（需要先在文件顶部添加 `import json`）：

```python
def save_enriched_news(self, news_list: List[Dict], analysis_list: List[Dict]) -> Dict[str, List[int]]:
    """
    保存新闻和分析结果（完整流程）

    Args:
        news_list: 新闻列表（来自 cleaned_news）
        analysis_list: 分析结果列表（来自 enriched_news）

    Returns:
        {
            'news_ids': [插入的新闻 ID 列表],
            'analysis_ids': [插入的分析 ID 列表]
        }

    注意：
        news_list 和 analysis_list 应该长度相同且一一对应
        自动将 news_id 关联到 analysis_list 中的对应项
    """
    # 先保存新闻
    news_ids = self.save_news(news_list)

    # 将 news_id 添加到分析结果中
    for i, analysis in enumerate(analysis_list):
        if i < len(news_ids):
            analysis['news_id'] = news_ids[i]

    # 保存分析结果
    analysis_ids = self.save_news_analysis(analysis_list)

    return {
        'news_ids': news_ids,
        'analysis_ids': analysis_ids
    }
```

- [ ] **Step 7: 验证数据库创建正确**

```bash
uv run python -c "
from src.storage.database import database
import sqlite3
# 检查表是否存在
cursor = database.conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='news_analysis'\")
result = cursor.fetchone()
if result:
    print('✓ news_analysis 表已创建')
else:
    print('✗ news_analysis 表未创建')
"
```

预期: ✓ news_analysis 表已创建

- [ ] **Step 8: 提交更改**

```bash
git add src/storage/database.py
git commit -m "feat: add news_analysis table and save_enriched_news method"
```

---

## Chunk 6: 集成测试和文档更新

### Task 9: 扩展集成测试

**Files:**
- Modify: `tests/test_workflow_integration.py`

- [ ] **Step 1: 添加包含深度分析的完整工作流测试**

在 `tests/test_workflow_integration.py` 中添加：

```python
def test_full_workflow_with_deep_analysis(mocker):
    """测试包含深度分析的完整工作流（after_close）"""
    from src.workflow.graph import report_graph

    # Mock 数据采集
    mock_news = [
        {'title': '新闻1', 'content': '内容1', 'source': 'test', 'time': '2024-01-01'},
        {'title': '新闻2', 'content': '内容2', 'source': 'test', 'time': '2024-01-01'}
    ]
    mocker.patch('src.collectors.news_collector.ak.stock_info_cjzc_em')
    mocker.patch('src.collectors.news_collector.ak.stock_info_global_em')
    mocker.patch('src.collectors.news_collector.ak.stock_info_global_sina')
    mocker.patch('src.collectors.news_collector.ak.stock_info_global_futu')
    mocker.patch('src.collectors.news_collector.ak.stock_info_global_ths')
    mocker.patch('src.collectors.news_collector.ak.stock_info_global_cls')
    mocker.patch('src.collectors.market_collector.ak.stock_zh_a_spot_em')
    mocker.patch('src.collectors.market_collector.ak.stock_individual_fund_flow_rank')
    mocker.patch('src.collectors.market_collector.ak.stock_sector_fund_flow_rank')
    mocker.patch('src.collectors.market_collector.ak.stock_concept_fund_flow_rank')
    mocker.patch('src.collectors.market_collector.ak.stock_zh_a_daily')
    mocker.patch('src.collectors.news_collector.NewsCollector.collect', return_value=mock_news)
    mocker.patch('src.collectors.market_collector.MarketCollector.collect', return_value={})

    # Mock HeavyAnalyzer 返回增强数据
    mock_enriched = [
        {
            'title': '新闻1',
            'content': '内容1',
            'event_type': '财报类',
            'sentiment': 'positive',
            'importance': 5,
            'related_stocks': {'direct': ['600519.SH:贵州茅台'], 'indirect': [], 'concepts': []},
            'source': 'test',
            'time': '2024-01-01'
        }
    ]

    # 正确的 mock 方式：patch HeavyAnalyzer 类
    mock_heavy_analyzer_class = mocker.patch('src.processors.analyzer.HeavyAnalyzer')
    mock_analyzer_instance = mock_heavy_analyzer_class.return_value
    mock_analyzer_instance.analyze.return_value = mock_enriched

    # Mock LLM 生成报告
    mocker.patch('src.generators.llm_client.llm_client.chat', return_value='# 测试报告\n\n内容')

    # 执行工作流
    result = report_graph.invoke({
        'report_type': 'after_close',
        'news_data': [],
        'market_data': {},
        'cleaned_news': [],
        'enriched_news': [],
        'context': '',
        'report': '',
        'errors': []
    })

    # 验证
    assert 'enriched_news' in result
    assert len(result['enriched_news']) > 0
    assert result['enriched_news'][0]['event_type'] == '财报类'
    assert result['report'] != ''
```

- [ ] **Step 2: 运行集成测试**

```bash
uv run pytest tests/test_workflow_integration.py::test_full_workflow_with_deep_analysis -v
```

预期: PASS - 测试通过

- [ ] **Step 3: 运行所有集成测试确保没有破坏**

```bash
uv run pytest tests/test_workflow_integration.py -v
```

预期: PASS - 所有集成测试通过

- [ ] **Step 4: 提交更改**

```bash
git add tests/test_workflow_integration.py
git commit -m "test: add integration test for workflow with deep analysis"
```

### Task 10: 更新文档

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 更新 CLAUDE.md 添加新组件说明**

在 CLAUDE.md 中的 "Architecture Overview" 部分，更新工作流描述：

找到：
```
The workflow is defined in `src/workflow/graph.py`:
`collect → clean → store → vectorize → rag → [route] → generate → save`
```

改为：
```
The workflow is defined in `src/workflow/graph.py`:
`collect → clean → analyze → store → vectorize → rag → [route] → generate → save`
```

添加新组件说明：

```markdown
### News Processing Pipeline

**Collection** (`src/collectors/`):
- 6 sources via AKShare API: 东财, 新浪, 富途, 同花顺, 财联社

**Cleaning** (`src/processors/cleaner.py`):
1. `RuleCleaner`: HTML removal, deduplication (MD5 hash)
2. `LLMCleaner`: Entity extraction, sentiment analysis, importance scoring (1-5), tagging

**Deep Analysis** (`src/processors/analyzer.py`):
- `HeavyAnalyzer`: Event extraction (6 predefined types), stock association (direct/indirect/concepts), intelligent merging of same-stock news
- Adds `event_type`, `event_subtype`, `related_stocks` fields to enriched_news
- Merges multiple news about same stock into single entry
- Sorts by importance and stock relevance
```

- [ ] **Step 2: 更新报告生成部分说明**

在 "Architecture Overview" 中找到报告生成部分，更新说明：

```markdown
### Report Generation (`src/workflow/nodes.py`)

Generation nodes now use `_format_news_enriched()` which includes:
- Event type badges (e.g., [财报类], [政策影响类])
- Sentiment icons (📈 positive, ➡️ neutral, 📉 negative)
- Stock information (direct targets with codes)
- Importance ratings (1-5)
- Related concepts

The enriched data provides deeper context for LLM to generate more insightful reports.
```

- [ ] **Step 3: 提交文档更新**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with deep analysis workflow"
```

### Task 11: 最终验证和端到端测试

- [ ] **Step 1: 运行所有测试**

```bash
uv run pytest -v
```

预期: 所有测试通过

- [ ] **Step 2: 手动端到端测试（可选，需要配置 LLM）**

如果有 LLM 配置：

```bash
# 设置环境变量
export LLM_BASE_URL="your_llm_url"
export LLM_API_KEY="your_api_key"

# 运行一次报告生成
uv run python src/main.py run after_close

# 检查生成的报告
cat outputs/$(date +%Y-%m-%d)_after_close.md
```

验证报告包含事件类型和标的信息

- [ ] **Step 3: 最终提交**

```bash
git add .
git commit -m "chore: final cleanup and documentation for news information extraction feature"
```

---

## 实施完成检查清单

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 工作流图包含 analyze_node
- [ ] ReportState 包含 enriched_news 字段
- [ ] LLMClient.analyze() 方法实现并测试
- [ ] HeavyAnalyzer 类实现并测试
- [ ] analyze_node 实现并测试
- [ ] _format_news_enriched 函数实现并测试
- [ ] 生成节点使用 enriched_news
- [ ] 数据库包含 news_analysis 表
- [ ] 文档已更新

---

**实施完成后，系统将具备：**

1. ✅ 事件抽取能力 - 自动识别 6 大类金融事件
2. ✅ 标的关联能力 - 分层关联直接标的、间接标的、概念板块
3. ✅ 智能聚合能力 - 同一标的的多条新闻自动合并
4. ✅ 结构化输出 - enriched_news 包含丰富的元数据供报告生成使用

**预期效果：**

- 报告质量提升：更准确的事件分类和标的识别
- 信息密度提升：智能合并减少重复，突出重要信息
- 可追溯性增强：完整的事件和标的元数据可追溯查询
