from src.processors.cleaner import RuleCleaner

def test_rule_cleaner_removes_duplicates():
    cleaner = RuleCleaner()
    news = [
        {'title': '新闻A', 'content': '内容A'},
        {'title': '新闻A', 'content': '内容A'},
        {'title': '新闻B', 'content': '内容B'},
    ]
    result = cleaner.clean(news)
    assert len(result) == 2

def test_rule_cleaner_normalizes_time():
    cleaner = RuleCleaner()
    news = [
        {'title': '新闻', 'content': '内容', 'time': '2024-03-11 08:30'},
    ]
    result = cleaner.clean(news)
    assert 'time' in result[0]

from unittest.mock import Mock, patch

def test_llm_cleaner_extracts_entities(monkeypatch):
    # Mock LLM response
    mock_response = {
        "cleaned_content": "贵州茅台发布年报",
        "entities": ["贵州茅台"],
        "sentiment": "neutral",
        "importance": 3,
        "tags": ["白酒"],
        "is_trash": False
    }

    mock_client = Mock()
    mock_client.clean.return_value = mock_response

    from src.processors.cleaner import LLMCleaner
    cleaner = LLMCleaner()
    cleaner.llm_client = mock_client

    news = [{'title': '贵州茅台', 'content': '发布年报'}]
    result = cleaner.clean(news)

    assert len(result) == 1
    assert result[0]['entities'] == ["贵州茅台"]
