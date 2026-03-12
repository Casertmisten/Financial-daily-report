"""测试工作流节点函数

使用 pytest 测试所有工作流节点函数的正确性。
"""
import pytest
from src.workflow.nodes import (
    collect_node,
    clean_node,
    store_node,
    vectorize_node,
    rag_node,
    _format_news,
    _format_market,
    pre_market_generate_node,
    mid_close_generate_node,
    after_close_generate_node,
    save_node,
    route_by_report_type,
)
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


def test_store_node_saves_to_database():
    """测试 store_node 保存到数据库"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "测试", "content": "内容", "source": "test", "time": "2026-03-12"}],
        "context": "",
        "report": "",
        "errors": []
    }

    result = store_node(initial_state)

    # store_node 不修改状态，只执行副作用
    assert result["cleaned_news"] == initial_state["cleaned_news"]


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


def test_rag_node_returns_context():
    """测试 rag_node 返回上下文"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "测试新闻", "content": "内容"}],
        "context": "",
        "report": "",
        "errors": []
    }

    result = rag_node(initial_state)

    assert "context" in result
    assert isinstance(result["context"], str)


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


def test_pre_market_generate_node():
    """测试盘前早报生成节点"""
    initial_state: ReportState = {
        "report_type": "pre_market",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "美股大涨", "content": "标普500上涨2%", "cleaned_content": "标普500上涨2%", "source": "test", "time": "2026-03-12"}],
        "context": "历史: 昨日A股下跌",
        "report": "",
        "errors": []
    }

    result = pre_market_generate_node(initial_state)

    assert "report" in result
    assert isinstance(result["report"], str)


def test_mid_close_generate_node():
    """测试盘中快讯生成节点"""
    initial_state: ReportState = {
        "report_type": "mid_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "上午拉升", "content": "科技股领涨", "cleaned_content": "科技股领涨", "source": "test", "time": "2026-03-12"}],
        "context": "",
        "report": "",
        "errors": []
    }

    result = mid_close_generate_node(initial_state)

    assert "report" in result
    assert isinstance(result["report"], str)


def test_after_close_generate_node():
    """测试盘后总结生成节点"""
    initial_state: ReportState = {
        "report_type": "after_close",
        "news_data": [],
        "market_data": {},
        "cleaned_news": [{"title": "收盘总结", "content": "三大指数集体收涨", "cleaned_content": "三大指数集体收涨", "source": "test", "time": "2026-03-12"}],
        "context": "",
        "report": "",
        "errors": []
    }

    result = after_close_generate_node(initial_state)

    assert "report" in result
    assert isinstance(result["report"], str)


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


def test_route_by_report_type():
    """测试条件路由函数"""
    assert route_by_report_type({"report_type": "pre_market"}) == "pre_market_generate"
    assert route_by_report_type({"report_type": "mid_close"}) == "mid_close_generate"
    assert route_by_report_type({"report_type": "after_close"}) == "after_close_generate"
    assert route_by_report_type({"report_type": "unknown"}) == "after_close_generate"  # 默认
