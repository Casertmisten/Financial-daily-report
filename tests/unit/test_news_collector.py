"""Unit tests for the news collector."""

import pytest

from src.collectors.news_collector import NewsCollector
from src.utils.exceptions import DataCollectionError


def test_news_collector_collect_returns_list():
    """Test that the news collector returns a list."""
    collector = NewsCollector()
    result = collector.collect()
    assert isinstance(result, list)


def test_news_collector_item_has_required_fields():
    """Test that each news item has required fields (title or content)."""
    collector = NewsCollector()
    result = collector.collect()
    if len(result) > 0:
        item = result[0]
        # AKShare returns Chinese field names like '标题', '摘要', etc.
        has_title_or_content = (
            "title" in item
            or "content" in item
            or "标题" in item
            or "摘要" in item
            or "内容" in item
        )
        assert has_title_or_content
