"""Tests for the report generator module."""
from unittest.mock import Mock
from src.generators.report_gen import ReportGenerator


def test_report_generator_generates_markdown(monkeypatch):
    """Test that report generator generates markdown output."""
    mock_client = Mock()
    mock_client.chat.return_value = """# 测试日报

## 1. 市场概览
测试内容
"""

    from src.generators.llm_client import llm_client
    monkeypatch.setattr(llm_client, 'chat', mock_client.chat)

    generator = ReportGenerator()
    news_data = []
    market_data = {}
    context = ""
    result = generator.generate(news_data, market_data, context)

    assert isinstance(result, str)
    assert "市场概览" in result


def test_report_generator_formats_empty_data(monkeypatch):
    """Test that report generator handles empty data gracefully."""
    mock_client = Mock()
    mock_client.chat.return_value = "# 日报\n\n暂无数据"

    from src.generators.llm_client import llm_client
    monkeypatch.setattr(llm_client, 'chat', mock_client.chat)

    generator = ReportGenerator()
    news_data = []
    market_data = {}
    context = ""
    result = generator.generate(news_data, market_data, context)

    assert isinstance(result, str)


def test_report_generator_formats_news_data():
    """Test that report generator formats news data correctly."""
    generator = ReportGenerator()

    news_data = [
        {'title': '测试新闻1', 'cleaned_content': '测试内容1', 'content': '原始内容1'},
        {'title': '测试新闻2', 'content': '测试内容2'},
    ]

    formatted = generator._format_news(news_data)
    assert '测试新闻1' in formatted
    assert '测试新闻2' in formatted


def test_report_generator_formats_market_data():
    """Test that report generator formats market data correctly."""
    generator = ReportGenerator()

    market_data = {
        'industry_flow': ['行业1: +100亿', '行业2: +50亿'],
        'main_flow': ['主力1: +200亿'],
    }

    formatted = generator._format_market(market_data)
    assert '行业1' in formatted
    assert '主力1' in formatted


def test_report_generator_handles_empty_news():
    """Test that report generator handles empty news list."""
    generator = ReportGenerator()
    formatted = generator._format_news([])
    assert formatted == "暂无新闻数据"


def test_report_generator_handles_empty_market():
    """Test that report generator handles empty market data."""
    generator = ReportGenerator()
    formatted = generator._format_market({})
    assert formatted == "暂无市场数据"
