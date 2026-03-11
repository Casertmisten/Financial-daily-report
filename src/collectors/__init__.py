"""Data collectors for the financial daily report system."""

from src.collectors.base import BaseCollector
from src.collectors.news_collector import NewsCollector

__all__ = ["BaseCollector", "NewsCollector"]
