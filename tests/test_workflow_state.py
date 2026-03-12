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
