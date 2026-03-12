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

**类接口定义**:
```python
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

        Raises:
            不抛出异常，失败时返回带默认字段的数据
        """

    def _batch_analyze(self, news_list: List[Dict]) -> List[Dict]:
        """批量调用 LLM 进行事件抽取和标的关联"""

    def _merge_by_stock(self, news_list: List[Dict]) -> List[Dict]:
        """按直接标的分组，合并同一标的的多条新闻"""

    def _merge_news_group(self, news_group: List[Dict]) -> Dict:
        """合并同一标的的多条新闻为一条"""

    def _sort_by_importance(self, news_list: List[Dict]) -> List[Dict]:
        """按重要性和直接标的数量排序"""
```

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
        'direct': ['600519.SH:贵州茅台'],      # 直接标的，格式：代码:名称
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

**股票代码格式规范**:
- 格式: `{代码}.{市场}:{名称}`，例如：`600519.SH:贵州茅台`
- 市场代码: SH（上交所）、SZ（深交所）、BJ（北交所）
- 如果只有公司名称没有代码: `{公司名称}`，例如：`贵州茅台`
- 空列表表示无法识别标的

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

### LLMClient.analyze() 方法接口

在 `src/generators/llm_client.py` 新增方法：

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

    Raises:
        不抛出异常，失败时返回默认值
    """
```

### 新增 `_format_news_enriched` 函数

在 `src/workflow/nodes.py` 新增函数（与 `_format_news` 并存）：

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

**格式化输出示例**:
```
- [财报类]📈 [3条新闻] 600519.SH:贵州茅台
  重要性: 5/5
  相关概念: 白酒概念, 消费龙头
- [政策影响类]➡️ 新能源汽车补贴政策延续
  重要性: 4/5
  相关概念: 新能源汽车, 消费刺激
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

**事件类型验证**:
```python
VALID_EVENT_TYPES = ['财报类', '重组并购类', '政策影响类', '经营类', '风险类', '其他']

def _validate_and_fix_event_type(self, result: Dict) -> Dict:
    """验证和修正事件类型"""
    event_type = result.get('event_type', '其他')

    if event_type not in VALID_EVENT_TYPES:
        logger.warning(f"无效事件类型 '{event_type}'，使用默认值 '其他'")
        result['event_type'] = '其他'

    return result
```

**标的结构验证**:
```python
def _validate_and_fix_stocks(self, result: Dict) -> Dict:
    """验证和修正标的结构"""
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
```

**JSON 解析失败处理**:
1. 记录错误日志
2. 返回默认值：`event_type='其他'`, `related_stocks` 为空结构
3. 不中断流程，继续处理下一条新闻

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
- `src/storage/database.py` - 扩展 Database 类，新增 `news_analysis` 表创建和存储方法

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

### 数据流兼容

**analyze_node 失败时的降级策略**:
```python
def analyze_node(state: ReportState) -> ReportState:
    try:
        from src.processors.analyzer import HeavyAnalyzer
        analyzer = HeavyAnalyzer()
        enriched = analyzer.analyze(state["cleaned_news"])
        return {**state, "enriched_news": enriched}
    except Exception as e:
        logger.error(f"深度分析失败，使用 cleaned_news: {e}")
        # 降级：将 cleaned_news 作为 enriched_news 返回
        # 添加默认的分析字段
        fallback = [
            {**news, 'event_type': '其他', 'related_stocks': {'direct': [], 'indirect': [], 'concepts': []}}
            for news in state["cleaned_news"]
        ]
        return {**state, "enriched_news": fallback}
```

**生成节点兼容性**:
- 优先使用 `enriched_news`
- 如果 `enriched_news` 为空或不存在，回退到 `cleaned_news`
- 使用统一的 `_format_news_enriched` 函数，该函数能处理两种数据格式

### 数据库存储

**存储策略**:
- `news` 表保持不变，继续存储 `cleaned_news` 的基础字段
- 新增 `news_analysis` 表存储深度分析结果：

```sql
CREATE TABLE IF NOT EXISTS news_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER,              -- 关联 news 表的 id
    event_type TEXT,
    event_subtype TEXT,
    direct_stocks TEXT,           -- JSON 格式
    indirect_stocks TEXT,         -- JSON 格式
    concepts TEXT,                -- JSON 格式
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (news_id) REFERENCES news(id)
);
```

**存储时机**:
- 在 `store_node` 之后存储基础新闻到 `news` 表
- 在 `analyze_node` 完成后存储分析结果到 `news_analysis` 表
- 如果分析失败，不影响基础新闻的存储

### 测试兼容性

- 现有集成测试继续运行，Mock `analyze_node` 返回空 `enriched_news`
- 新增测试覆盖完整流程（包含深度分析）
- 单元测试独立测试 `HeavyAnalyzer` 和 `analyze_node`

## 后续优化方向

1. **标的识别增强**: 使用股票数据库提高标的识别准确率
2. **事件图谱**: 构建事件关联图谱，发现事件间的因果关系
3. **历史对比**: 与历史事件对比，识别趋势和异常
4. **个性化**: 根据用户关注的股票/行业定制分析策略
