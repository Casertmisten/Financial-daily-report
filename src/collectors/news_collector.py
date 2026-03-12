"""News collector using AKShare API.

This module collects financial news from multiple sources via AKShare.
"""

import akshare as ak
from loguru import logger

from src.collectors.base import BaseCollector
from src.utils.exceptions import DataCollectionError
from src.utils.retry import retry_on_failure


class NewsCollector(BaseCollector):
    """Collector for financial news from multiple sources.

    Collects news from 6 different sources via AKShare:
    1. 财经早餐 - 东财 (stock_info_cjzc_em)
    2. 全球财经快讯 - 东财 (stock_info_global_em)
    3. 全球财经快讯 - 新浪 (stock_info_global_sina)
    4. 快讯 - 富途 (stock_info_global_futu)
    5. 全球财经直播 - 同花顺 (stock_info_global_ths)
    6. 电报 - 财联社 (stock_info_global_cls)
    """

    def __init__(self):
        """Initialize the news collector."""
        super().__init__(name="NewsCollector")

    def collect(self) -> list[dict]:
        """Collect news from all configured sources.
·        返回值：
            一个新闻条目列表，其中每个条目是一个包含新闻数据的字典，
            包含 'title'、'content'、'time' 等键。

        注意：
            如果所有数据源都失败，返回空列表而不是抛出异常。
            这样即使没有数据，系统也能生成简单的报告。
        """
        all_news = []

        # Source 1: 财经早餐 - 东财
        self._collect_from_cjzc_em(all_news)

        # Source 2: 全球财经快讯 - 东财
        self._collect_from_global_em(all_news)

        # Source 3: 全球财经快讯 - 新浪
        self._collect_from_global_sina(all_news)

        # Source 4: 快讯 - 富途
        self._collect_from_global_futu(all_news)

        # Source 5: 全球财经直播 - 同花顺
        self._collect_from_global_ths(all_news)

        # Source 6: 电报 - 财联社
        self._collect_from_global_cls(all_news)

        if not all_news:
            logger.warning("所有新闻源采集失败，将生成空日报")
            return []

        logger.info(f"✓ 新闻采集完成，共获取 {len(all_news)} 条")
        return all_news

    def _normalize_news_item(self, item: dict, source: str) -> dict:
        """标准化新闻条目的字段名

        将中文列名映射到英文列名

        Args:
            item: 原始新闻条目
            source: 数据源名称

        Returns:
            标准化后的新闻条目
        """
        # 中文到英文的字段名映射
        field_mapping = {
            '标题': 'title',
            '摘要': 'content',
            '发布时间': 'time',
            '时间': 'time',
            '链接': 'link',
            '内容': 'content',
        }

        normalized = {}
        for key, value in item.items():
            # 如果是中文字段名，映射到英文
            english_key = field_mapping.get(key, key)
            normalized[english_key] = value

        normalized['source'] = source
        return normalized

    def _collect_from_cjzc_em(self, all_news: list[dict]) -> None:
        """Collect news from 财经早餐 - 东财.

        Args:
            all_news: List to append collected news to.
        """
        try:
            logger.info("Collecting news from 财经早餐 - 东财...")
            df = ak.stock_info_cjzc_em()
            if df is not None and not df.empty:
                news_items = df.to_dict("records")
                for item in news_items:
                    normalized = self._normalize_news_item(item, "财经早餐-东财")
                    all_news.append(normalized)
                logger.info(f"Collected {len(news_items)} items from 财经早餐 - 东财")
        except Exception as e:
            logger.error(f"Failed to collect from 财经早餐 - 东财: {e}")

    def _collect_from_global_em(self, all_news: list[dict]) -> None:
        """Collect news from 全球财经快讯 - 东财.

        Args:
            all_news: List to append collected news to.
        """
        try:
            logger.info("Collecting news from 全球财经快讯 - 东财...")
            df = ak.stock_info_global_em()
            if df is not None and not df.empty:
                news_items = df.to_dict("records")
                for item in news_items:
                    normalized = self._normalize_news_item(item, "全球财经快讯-东财")
                    all_news.append(normalized)
                logger.info(f"Collected {len(news_items)} items from 全球财经快讯 - 东财")
        except Exception as e:
            logger.error(f"Failed to collect from 全球财经快讯 - 东财: {e}")

    def _collect_from_global_sina(self, all_news: list[dict]) -> None:
        """Collect news from 全球财经快讯 - 新浪.

        Args:
            all_news: List to append collected news to.
        """
        try:
            logger.info("Collecting news from 全球财经快讯 - 新浪...")
            df = ak.stock_info_global_sina()
            if df is not None and not df.empty:
                news_items = df.to_dict("records")
                for item in news_items:
                    normalized = self._normalize_news_item(item, "全球财经快讯-新浪")
                    all_news.append(normalized)
                logger.info(f"Collected {len(news_items)} items from 全球财经快讯 - 新浪")
        except Exception as e:
            logger.error(f"Failed to collect from 全球财经快讯 - 新浪: {e}")

    def _collect_from_global_futu(self, all_news: list[dict]) -> None:
        """Collect news from 快讯 - 富途.

        Args:
            all_news: List to append collected news to.
        """
        try:
            logger.info("Collecting news from 快讯 - 富途...")
            df = ak.stock_info_global_futu()
            if df is not None and not df.empty:
                news_items = df.to_dict("records")
                for item in news_items:
                    normalized = self._normalize_news_item(item, "快讯-富途")
                    all_news.append(normalized)
                logger.info(f"Collected {len(news_items)} items from 快讯 - 富途")
        except Exception as e:
            logger.error(f"Failed to collect from 快讯 - 富途: {e}")

    def _collect_from_global_ths(self, all_news: list[dict]) -> None:
        """Collect news from 全球财经直播 - 同花顺.

        Args:
            all_news: List to append collected news to.
        """
        try:
            logger.info("Collecting news from 全球财经直播 - 同花顺...")
            df = ak.stock_info_global_ths()
            if df is not None and not df.empty:
                news_items = df.to_dict("records")
                for item in news_items:
                    normalized = self._normalize_news_item(item, "全球财经直播-同花顺")
                    all_news.append(normalized)
                logger.info(f"Collected {len(news_items)} items from 全球财经直播 - 同花顺")
        except Exception as e:
            logger.error(f"Failed to collect from 全球财经直播 - 同花顺: {e}")

    def _collect_from_global_cls(self, all_news: list[dict]) -> None:
        """Collect news from 电报 - 财联社.

        Args:
            all_news: List to append collected news to.
        """
        try:
            logger.info("Collecting news from 电报 - 财联社...")
            df = ak.stock_info_global_cls()
            if df is not None and not df.empty:
                news_items = df.to_dict("records")
                for item in news_items:
                    normalized = self._normalize_news_item(item, "电报-财联社")
                    all_news.append(normalized)
                logger.info(f"Collected {len(news_items)} items from 电报 - 财联社")
        except Exception as e:
            logger.error(f"Failed to collect from 电报 - 财联社: {e}")
