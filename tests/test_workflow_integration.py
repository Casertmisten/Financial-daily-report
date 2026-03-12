"""LangGraph 工作流集成测试

此模块包含完整工作流的集成测试，涵盖三种报告类型：
- 盘前早报 (pre_market)
- 盡中快讯 (mid_close)
- 盅后总结 (after_close)

运行方式：
    pytest tests/test_workflow_integration.py -v -m integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime


# 检查 LLM 是否已配置
llm_configured = False
try:
    from src.generators.llm_client import llm_client
    from config.settings import config
    if config.llm.api_key and config.llm.api_key != "your-api-key-here":
        llm_configured = True
except Exception:
    pass


def mock_collect_news():
    """Mock 新闻采集"""
    return [
        {
            'title': '央行降准释放流动性',
            'content': '中国人民银行宣布降准0.25个百分点，释放长期资金约5000亿元。',
            'source': '央行官网',
            'time': '2026-03-12 09:00:00'
        },
        {
            'title': '科技板块全线大涨',
            'content': '受人工智能概念推动，科技股今日表现强劲，多只个股涨停。',
            'source': '财经快讯',
            'time': '2026-03-12 10:30:00'
        },
        {
            'title': '新能源汽车销量创新高',
            'content': '2月新能源汽车销量同比增长35%，多家车企交付量创历史新高。',
            'source': '汽车之家',
            'time': '2026-03-12 11:00:00'
        }
    ]


def mock_collect_market():
    """Mock 市场数据采集"""
    return {
        'industry_flow': [
            {'name': '计算机', 'net_amount': 1560000000},
            {'name': '电子', 'net_amount': 1230000000},
            {'name': '通信', 'net_amount': 890000000}
        ],
        'main_flow': [
            {'name': '北向资金', 'net_amount': 8500000000},
            {'name': '融资客', 'net_amount': 3200000000}
        ],
        'concept_flow': [
            {'name': '人工智能', 'net_amount': 780000000},
            {'name': '新能源汽车', 'net_amount': 560000000}
        ],
        'index_data': {
            '上证指数': {'close': 3050.25, 'change': 1.25},
            '深证成指': {'close': 9850.30, 'change': 1.45},
            '创业板指': {'close': 1920.15, 'change': 1.65}
        },
        'market_sentiment': '偏多'
    }


def mock_llm_chat(messages, **kwargs):
    """Mock LLM 响应"""
    return """# 日报报告

## 一、市场概览
今日市场表现强劲，主要指数全线上涨。上证指数收于3050.25点，上涨1.25%；深证成指收于9850.30点，上涨1.45%；创业板指收于1920.15点，上涨1.65%。

## 二、资金动向
- 北向资金净流入85亿元
- 融资客净买入32亿元
- 行业资金流：计算机(+15.6亿)、电子(+12.3亿)、通信(+8.9亿)

## 三、板块聚焦
**科技板块**：受人工智能概念推动，科技股今日表现强劲，多只个股涨停。
**新能源**：新能源汽车销量创新高，2月同比增长35%。

## 四、要闻解读
1. **央行降准**：中国人民银行宣布降准0.25个百分点，释放长期资金约5000亿元。
2. **科技板块**：人工智能概念持续火热，带动相关产业链表现亮眼。

## 五、策略参考
- 重点关注人工智能产业链投资机会
- 关注降准受益的金融板块
- 新能源汽车产业链持续景气

## 六、风险提示
- 关注外部市场波动风险
- 注意短期获利回吐压力
"""


@pytest.mark.integration
def test_full_workflow_pre_market(monkeypatch):
    """测试盘前早报完整工作流

    测试从数据采集到报告生成的完整流程，验证：
    - 数据采集节点正常工作
    - 数据清洗节点正常工作
    - 存储节点正常工作
    - 向量化节点正常工作
    - RAG检索节点正常工作
    - 盘前早报生成节点正常工作
    - 保存节点正常工作
    """
    # Mock 所有外部依赖
    monkeypatch.setattr('src.collectors.news_collector.NewsCollector.collect', lambda self: mock_collect_news())
    monkeypatch.setattr('src.collectors.market_collector.MarketCollector.collect', lambda self: mock_collect_market())
    monkeypatch.setattr('src.generators.llm_client.llm_client.chat', mock_llm_chat)
    monkeypatch.setattr('src.rag.vector_store.vector_store.add_documents', lambda docs: None)
    monkeypatch.setattr('src.rag.retriever.rag_retriever.retrieve', lambda query: "历史上下文信息")
    monkeypatch.setattr('src.storage.database.database.save_news', lambda news: None)
    monkeypatch.setattr('src.storage.database.database.save_report', lambda date, type, report: None)

    # 导入并执行工作流
    from src.workflow.graph import report_graph
    from src.workflow.state import ReportState

    initial_state = ReportState(
        report_type="pre_market",
        news_data=[],
        market_data={},
        cleaned_news=[],
        context="",
        report="",
        errors=[]
    )

    result = report_graph.invoke(initial_state)

    # 验证结果
    assert result["report_type"] == "pre_market"
    assert len(result["report"]) > 0
    assert "市场概览" in result["report"]
    assert "资金动向" in result["report"]
    assert isinstance(result["news_data"], list)
    assert isinstance(result["market_data"], dict)
    assert isinstance(result["cleaned_news"], list)
    assert isinstance(result["context"], str)


@pytest.mark.integration
def test_full_workflow_mid_close(monkeypatch):
    """测试盘中快讯完整工作流

    测试从数据采集到报告生成的完整流程，验证：
    - 数据采集节点正常工作
    - 数据清洗节点正常工作
    - 存储节点正常工作
    - 向量化节点正常工作
    - RAG检索节点正常工作
    - 盘中快讯生成节点正常工作
    - 保存节点正常工作
    """
    # Mock 所有外部依赖
    monkeypatch.setattr('src.collectors.news_collector.NewsCollector.collect', lambda self: mock_collect_news())
    monkeypatch.setattr('src.collectors.market_collector.MarketCollector.collect', lambda self: mock_collect_market())
    monkeypatch.setattr('src.generators.llm_client.llm_client.chat', mock_llm_chat)
    monkeypatch.setattr('src.rag.vector_store.vector_store.add_documents', lambda docs: None)
    monkeypatch.setattr('src.rag.retriever.rag_retriever.retrieve', lambda query: "历史上下文信息")
    monkeypatch.setattr('src.storage.database.database.save_news', lambda news: None)
    monkeypatch.setattr('src.storage.database.database.save_report', lambda date, type, report: None)

    # 导入并执行工作流
    from src.workflow.graph import report_graph
    from src.workflow.state import ReportState

    initial_state = ReportState(
        report_type="mid_close",
        news_data=[],
        market_data={},
        cleaned_news=[],
        context="",
        report="",
        errors=[]
    )

    result = report_graph.invoke(initial_state)

    # 验证结果
    assert result["report_type"] == "mid_close"
    assert len(result["report"]) > 0
    assert "市场概览" in result["report"]
    assert "资金动向" in result["report"]
    assert isinstance(result["news_data"], list)
    assert isinstance(result["market_data"], dict)
    assert isinstance(result["cleaned_news"], list)
    assert isinstance(result["context"], str)


@pytest.mark.integration
def test_full_workflow_after_close(monkeypatch):
    """测试盘后总结完整工作流

    测试从数据采集到报告生成的完整流程，验证：
    - 数据采集节点正常工作
    - 数据清洗节点正常工作
    - 存储节点正常工作
    - 向量化节点正常工作
    - RAG检索节点正常工作
    - 盘后总结生成节点正常工作
    - 保存节点正常工作
    """
    # Mock 所有外部依赖
    monkeypatch.setattr('src.collectors.news_collector.NewsCollector.collect', lambda self: mock_collect_news())
    monkeypatch.setattr('src.collectors.market_collector.MarketCollector.collect', lambda self: mock_collect_market())
    monkeypatch.setattr('src.generators.llm_client.llm_client.chat', mock_llm_chat)
    monkeypatch.setattr('src.rag.vector_store.vector_store.add_documents', lambda docs: None)
    monkeypatch.setattr('src.rag.retriever.rag_retriever.retrieve', lambda query: "历史上下文信息")
    monkeypatch.setattr('src.storage.database.database.save_news', lambda news: None)
    monkeypatch.setattr('src.storage.database.database.save_report', lambda date, type, report: None)

    # 导入并执行工作流
    from src.workflow.graph import report_graph
    from src.workflow.state import ReportState

    initial_state = ReportState(
        report_type="after_close",
        news_data=[],
        market_data={},
        cleaned_news=[],
        context="",
        report="",
        errors=[]
    )

    result = report_graph.invoke(initial_state)

    # 验证结果
    assert result["report_type"] == "after_close"
    assert len(result["report"]) > 0
    assert "市场概览" in result["report"]
    assert "资金动向" in result["report"]
    assert isinstance(result["news_data"], list)
    assert isinstance(result["market_data"], dict)
    assert isinstance(result["cleaned_news"], list)
    assert isinstance(result["context"], str)


@pytest.mark.integration
def test_workflow_handles_empty_data(monkeypatch):
    """测试工作流处理空数据的情况

    验证工作流在数据采集为空时能够正常处理
    """
    # Mock 空数据
    def mock_empty_news():
        return []

    def mock_empty_market():
        return {}

    monkeypatch.setattr('src.collectors.news_collector.NewsCollector.collect', lambda self: mock_empty_news())
    monkeypatch.setattr('src.collectors.market_collector.MarketCollector.collect', lambda self: mock_empty_market())

    def mock_llm_empty(messages, **kwargs):
        return "# 日报\n\n暂无数据\n"

    monkeypatch.setattr('src.generators.llm_client.llm_client.chat', mock_llm_empty)
    monkeypatch.setattr('src.rag.vector_store.vector_store.add_documents', lambda docs: None)
    monkeypatch.setattr('src.rag.retriever.rag_retriever.retrieve', lambda query: "")
    monkeypatch.setattr('src.storage.database.database.save_news', lambda news: None)
    monkeypatch.setattr('src.storage.database.database.save_report', lambda date, type, report: None)

    # 导入并执行工作流
    from src.workflow.graph import report_graph
    from src.workflow.state import ReportState

    initial_state = ReportState(
        report_type="after_close",
        news_data=[],
        market_data={},
        cleaned_news=[],
        context="",
        report="",
        errors=[]
    )

    result = report_graph.invoke(initial_state)

    # 验证结果 - 即使没有数据，工作流也应该完成
    assert result["report_type"] == "after_close"
    assert len(result["report"]) > 0
    assert result["cleaned_news"] == []


@pytest.mark.integration
def test_workflow_handles_collection_errors(monkeypatch):
    """测试工作流处理采集错误的情况

    验证工作流在数据采集失败时能够抛出异常
    """
    # Mock 采集错误
    def mock_error_news():
        raise Exception("网络错误")

    def mock_error_market():
        raise Exception("API超时")

    monkeypatch.setattr('src.collectors.news_collector.NewsCollector.collect', lambda self: mock_error_news())
    monkeypatch.setattr('src.collectors.market_collector.MarketCollector.collect', lambda self: mock_error_market())

    def mock_llm_error(messages, **kwargs):
        return "# 日报\n\n数据采集失败，请稍后重试\n"

    monkeypatch.setattr('src.generators.llm_client.llm_client.chat', mock_llm_error)
    monkeypatch.setattr('src.rag.vector_store.vector_store.add_documents', lambda docs: None)
    monkeypatch.setattr('src.rag.retriever.rag_retriever.retrieve', lambda query: "")
    monkeypatch.setattr('src.storage.database.database.save_news', lambda news: None)
    monkeypatch.setattr('src.storage.database.database.save_report', lambda date, type, report: None)

    # 导入并执行工作流
    from src.workflow.graph import report_graph
    from src.workflow.state import ReportState

    initial_state = ReportState(
        report_type="after_close",
        news_data=[],
        market_data={},
        cleaned_news=[],
        context="",
        report="",
        errors=[]
    )

    # 工作流应该在数据采集失败时抛出异常
    with pytest.raises(Exception, match="网络错误"):
        result = report_graph.invoke(initial_state)
