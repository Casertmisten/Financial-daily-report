"""新闻深度分析模块

负责对清洗后的新闻进行事件抽取、标的关联和智能聚合
"""
from loguru import logger
from typing import List, Dict
from src.generators.llm_client import llm_client


class HeavyAnalyzer:
    """深度分析器，对新闻进行事件抽取和标的关联"""

    def __init__(self, batch_size: int = 10):
        """
        初始化分析器

        Args:
            batch_size: 批处理大小，每批 N 条新闻进行一次 LLM 调用
        """
        self.llm_client = llm_client
        self.batch_size = batch_size

    def analyze(self, news_list: List[Dict]) -> List[Dict]:
        """
        对新闻列表进行深度分析

        流程：批量分析 → 智能合并 → 排序

        Args:
            news_list: 来自 LLMCleaner 的 cleaned_news

        Returns:
            enriched_news: 包含事件类型和标的关联的新闻列表
        """
        if not news_list:
            return []

        # 1. 批量调用 LLM 进行事件抽取和标的关联
        analyzed = self._batch_analyze(news_list)

        # 2. 智能合并同一标的的新闻
        merged = self._merge_by_stock(analyzed)

        # 3. 按重要性排序
        sorted_news = self._sort_by_importance(merged)

        return sorted_news

    def _batch_analyze(self, news_list: List[Dict]) -> List[Dict]:
        """批量调用 LLM 进行事件抽取和标的关联"""
        analyzed = []

        for news in news_list:
            try:
                # 构建分析文本
                text = f"标题: {news.get('title', '')}\n内容: {news.get('content', '')}"

                # 调用 LLM 分析
                analysis_result = self.llm_client.analyze(text)

                # 合并原始新闻和分析结果
                enriched = {
                    **news,
                    'event_type': analysis_result.get('event_type', '其他'),
                    'event_subtype': analysis_result.get('event_subtype', ''),
                    'related_stocks': analysis_result.get('related_stocks', {
                        'direct': [],
                        'indirect': [],
                        'concepts': []
                    })
                }
                analyzed.append(enriched)

            except Exception as e:
                logger.warning(f"深度分析失败，使用基础数据: {e}")
                # 回退到基础数据，添加默认的分析字段
                fallback = {
                    **news,
                    'event_type': '其他',
                    'event_subtype': '',
                    'related_stocks': {
                        'direct': [],
                        'indirect': [],
                        'concepts': []
                    }
                }
                analyzed.append(fallback)

        return analyzed

    def _merge_by_stock(self, news_list: List[Dict]) -> List[Dict]:
        """
        按直接标的分组，合并同一标的的多条新闻

        合并策略：
        - 按 direct_stocks 分组
        - 同一标的的多条新闻合并成一条
        - 综合情感判断（正面>50%→正面，负面>50%→负面）
        - 重要性取最高值
        - 列出所有事件类型
        - merged_news 保存原始新闻列表
        """
        # 按直接标的分组
        stock_groups = {}
        for news in news_list:
            direct_stocks = news.get('related_stocks', {}).get('direct', [])

            if not direct_stocks:
                # 无关联标的的新闻单独一组
                key = '_no_stock_'
            else:
                # 使用第一个直接标的作为分组键
                key = direct_stocks[0]

            if key not in stock_groups:
                stock_groups[key] = []
            stock_groups[key].append(news)

        # 合并每个组
        merged = []
        for stock, news_group in stock_groups.items():
            if len(news_group) == 1:
                # 单条新闻直接保留
                merged.append(news_group[0])
            else:
                # 多条新闻合并
                merged_item = self._merge_news_group(news_group)
                merged.append(merged_item)

        return merged

    def _merge_news_group(self, news_group: List[Dict]) -> Dict:
        """合并同一标的的多条新闻为一条"""
        # 提取标的信息
        first = news_group[0]
        stock_name = first.get('related_stocks', {}).get('direct', ['未知'])[0]

        # 综合情感
        sentiments = [n.get('sentiment', 'neutral') for n in news_group]
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')

        if positive_count > len(news_group) / 2:
            combined_sentiment = 'positive'
        elif negative_count > len(news_group) / 2:
            combined_sentiment = 'negative'
        else:
            combined_sentiment = 'neutral'

        # 收集所有事件类型
        event_types = set()
        for news in news_group:
            event_type = news.get('event_type', '其他')
            event_types.add(event_type)

        # 生成合并后的内容摘要
        content_parts = []
        for news in news_group:
            event_subtype = news.get('event_subtype', '')
            content_preview = news.get('content', '')[:50]
            content_parts.append(f"- {event_subtype}: {content_preview}")

        merged_content = '\n'.join(content_parts)

        return {
            'title': f"[{len(news_group)}条新闻] {stock_name}",
            'content': merged_content,
            'source': first.get('source', ''),
            'time': first.get('time', ''),
            'entities': list(set([e for n in news_group for e in n.get('entities', [])])),
            'sentiment': combined_sentiment,
            'importance': max([n.get('importance', 3) for n in news_group]),
            'tags': list(set([t for n in news_group for t in n.get('tags', [])])),
            'event_type': ', '.join(sorted(event_types)),
            'event_subtype': '',
            'related_stocks': first.get('related_stocks', {}),
            'merged_news': news_group  # 保留原始新闻
        }

    def _sort_by_importance(self, news_list: List[Dict]) -> List[Dict]:
        """
        按重要性和直接标的数量排序

        排序规则：
        1. 按重要性降序: importance 5 > 4 > 3 > 2 > 1
        2. 按直接标的数量: 有直接标的的优先
        """
        return sorted(
            news_list,
            key=lambda x: (
                -x.get('importance', 3),  # 重要性降序
                -len(x.get('related_stocks', {}).get('direct', []))  # 直接标的数量降序
            )
        )