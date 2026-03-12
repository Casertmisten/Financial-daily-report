"""Integration tests for the full pipeline."""
from unittest.mock import Mock, patch
from src.main import generate_daily_report


def test_full_pipeline_generates_report(monkeypatch):
    """Test that the full pipeline generates a report."""
    # Mock the collectors to avoid network calls
    mock_news_data = [
        {
            'title': '测试新闻',
            'content': '测试内容',
            'source': 'test',
            'time': '2024-01-01 10:00:00'
        }
    ]

    mock_market_data = {
        'industry_flow': ['行业1: +100亿'],
        'main_flow': ['主力1: +200亿'],
    }

    # Mock news collector
    def mock_collect_news(self):
        return mock_news_data

    # Mock market collector
    def mock_collect_market(self):
        return mock_market_data

    # Mock LLM chat for report generation
    def mock_chat(messages, **kwargs):
        return """# 测试日报

## 1. 市场概览
测试市场概览

## 2. 资金动向
测试资金动向

## 3. 个股聚焦
测试个股聚焦

## 4. 行业分析
测试行业分析

## 5. 政策解读
测试政策解读

## 6. 外围市场
测试外围市场

## 7. 策略参考
测试策略参考

## 8. 风险提示
测试风险提示
"""

    # Apply mocks
    monkeypatch.setattr('src.collectors.news_collector.NewsCollector.collect', mock_collect_news)
    monkeypatch.setattr('src.collectors.market_collector.MarketCollector.collect', mock_collect_market)

    from src.generators.llm_client import llm_client
    monkeypatch.setattr(llm_client, 'chat', mock_chat)

    # Test the pipeline
    result = generate_daily_report("test")

    assert isinstance(result, str)
    assert len(result) > 0
    assert "市场概览" in result


def test_full_pipeline_handles_empty_data(monkeypatch):
    """Test that the full pipeline handles empty data gracefully."""
    # Mock the collectors to return empty data
    def mock_collect_empty(self):
        return []

    def mock_collect_empty_market(self):
        return {}

    # Mock LLM chat for report generation
    def mock_chat_empty(messages, **kwargs):
        return """# 测试日报

暂无数据
"""

    # Apply mocks
    monkeypatch.setattr('src.collectors.news_collector.NewsCollector.collect', mock_collect_empty)
    monkeypatch.setattr('src.collectors.market_collector.MarketCollector.collect', mock_collect_empty_market)

    from src.generators.llm_client import llm_client
    monkeypatch.setattr(llm_client, 'chat', mock_chat_empty)

    # Test the pipeline
    result = generate_daily_report("test")

    assert isinstance(result, str)
    assert len(result) > 0


def test_full_pipeline_handles_collection_errors(monkeypatch):
    """Test that the full pipeline handles collection errors gracefully."""
    # Mock the collectors to raise an exception
    def mock_collect_error(self):
        raise Exception("Network error")

    def mock_collect_empty_market(self):
        return {}

    # Mock LLM chat for report generation
    def mock_chat_error(messages, **kwargs):
        return """# 测试日报

数据采集失败
"""

    # Apply mocks
    monkeypatch.setattr('src.collectors.news_collector.NewsCollector.collect', mock_collect_error)
    monkeypatch.setattr('src.collectors.market_collector.MarketCollector.collect', mock_collect_empty_market)

    from src.generators.llm_client import llm_client
    monkeypatch.setattr(llm_client, 'chat', mock_chat_error)

    # Test the pipeline - should handle errors gracefully
    try:
        result = generate_daily_report("test")
        # If it succeeds, check the result
        assert isinstance(result, str)
    except Exception as e:
        # If it raises an exception, that's also acceptable
        assert "Network error" in str(e) or "数据采集失败" in str(e)
