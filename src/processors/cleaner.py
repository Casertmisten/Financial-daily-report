from loguru import logger
from typing import List, Dict
import hashlib
from datetime import datetime
import re

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
