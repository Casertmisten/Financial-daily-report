from loguru import logger
from typing import List, Dict
import hashlib
from datetime import datetime
import re
import json

class RuleCleaner:
    def __init__(self):
        self.seen_hashes = set()

    def clean(self, news_list: List[Dict]) -> List[Dict]:
        cleaned = []

        for item in news_list:
            # 计算内容hash用于去重
            content_str = f"{item.get('title', '')}{item.get('content', '')}"
            content_hash = hashlib.md5(content_str.encode()).hexdigest()

            if content_hash in self.seen_hashes:
                continue

            self.seen_hashes.add(content_hash)

            # 清洗数据
            cleaned_item = {
                'title': self._clean_text(item.get('title', '')),
                'content': self._clean_text(item.get('content', '')),
                'source': item.get('source', ''),
                'time': self._normalize_time(item.get('time', '')),
            }

            if cleaned_item['title'] or cleaned_item['content']:
                cleaned.append(cleaned_item)

        logger.info(f"规则清洗: {len(news_list)} -> {len(cleaned)}")
        return cleaned

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', str(text))
        # 移除多余空白
        text = ' '.join(text.split())
        return text.strip()

    def _normalize_time(self, time_str: str) -> str:
        if not time_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 简单的时间标准化
        try:
            return str(time_str).strip()
        except:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class LLMCleaner:
    """基于LLM的智能清洗器，提取实体、情感、重要性等信息"""

    def __init__(self, batch_size: int = 10):
        """
        初始化LLM清洗器

        Args:
            batch_size: 批处理大小，默认10
        """
        from src.generators.llm_client import llm_client
        self.llm_client = llm_client
        self.batch_size = batch_size
        self.seen_hashes = set()

    def clean(self, news_list: List[Dict]) -> List[Dict]:
        """
        使用LLM清洗新闻列表

        Args:
            news_list: 新闻列表，每项包含title和content

        Returns:
            清洗后的新闻列表，包含实体、情感、重要性等字段
        """
        cleaned = []

        for i in range(0, len(news_list), self.batch_size):
            batch = news_list[i:i + self.batch_size]

            for item in batch:
                # 计算内容hash用于去重
                content_str = f"{item.get('title', '')}{item.get('content', '')}"
                content_hash = hashlib.md5(content_str.encode()).hexdigest()

                if content_hash in self.seen_hashes:
                    continue

                self.seen_hashes.add(content_hash)

                # 使用LLM清洗
                cleaned_item = self._clean_single_item(item)

                # 过滤垃圾信息
                if not cleaned_item.get('is_trash', False):
                    cleaned.append(cleaned_item)

        logger.info(f"LLM清洗: {len(news_list)} -> {len(cleaned)}")
        return cleaned

    def _clean_single_item(self, item: Dict) -> Dict:
        """
        清洗单个新闻项

        Args:
            item: 单个新闻项

        Returns:
            清洗后的新闻项
        """
        title = item.get('title', '')
        content = item.get('content', '')
        source = item.get('source', '')
        time_str = self._normalize_time(item.get('time', ''))

        # 组合标题和内容进行清洗
        text = f"标题: {title}\n内容: {content}"

        try:
            # 调用LLM进行清洗
            result = self.llm_client.clean(text)

            # 构建清洗后的结果
            cleaned_item = {
                'title': self._clean_text(title),
                'content': result.get('cleaned_content', self._clean_text(content)),
                'source': source,
                'time': time_str,
                'entities': result.get('entities', []),
                'sentiment': result.get('sentiment', 'neutral'),
                'importance': result.get('importance', 3),
                'tags': result.get('tags', []),
                'is_trash': result.get('is_trash', False),
            }

            logger.debug(f"LLM清洗成功: {title[:20]}... 实体={cleaned_item['entities']}")
            return cleaned_item

        except Exception as e:
            logger.warning(f"LLM清洗失败，回退到原始数据: {e}")

            # 回退到原始数据
            return {
                'title': self._clean_text(title),
                'content': self._clean_text(content),
                'source': source,
                'time': time_str,
                'entities': [],
                'sentiment': 'neutral',
                'importance': 3,
                'tags': [],
                'is_trash': False,
            }

    def _clean_text(self, text: str) -> str:
        """清洗文本，移除HTML标签和多余空白"""
        if not text:
            return ""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', str(text))
        # 移除多余空白
        text = ' '.join(text.split())
        return text.strip()

    def _normalize_time(self, time_str: str) -> str:
        """标准化时间格式"""
        if not time_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            return str(time_str).strip()
        except:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
