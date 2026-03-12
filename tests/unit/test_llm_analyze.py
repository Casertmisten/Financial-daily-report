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
