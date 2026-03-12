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