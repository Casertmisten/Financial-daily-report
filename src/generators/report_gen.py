"""日报生成器模块，负责生成结构化的金融日报"""
from loguru import logger
from src.generators.llm_client import llm_client
from config.prompts import DAILY_REPORT_PROMPT
from datetime import datetime
from typing import List, Dict


class ReportGenerator:
    """日报生成器，使用LLM生成结构化的金融日报"""

    def __init__(self):
        """初始化日报生成器"""
        self.client = llm_client

    def generate(self, news_data: List[Dict], market_data: Dict, context: str) -> str:
        """
        生成日报

        Args:
            news_data: 新闻数据列表
            market_data: 市场数据字典
            context: 历史参考上下文

        Returns:
            生成的Markdown格式日报文本

        Raises:
            ReportGenerationError: 日报生成失败时抛出
        """
        news_summary = self._format_news(news_data)
        market_summary = self._format_market(market_data)

        prompt = DAILY_REPORT_PROMPT.format(
            news_data=news_summary,
            market_data=market_summary,
            historical_context=context
        )

        try:
            report = self.client.chat(
                messages=[
                    {"role": "system", "content": "你是一位专业的中国金融分析师。请务必用中文回复所有内容，包括标题、分析、数据说明等。不要使用英文输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            logger.success("日报生成完成")
            return report
        except Exception as e:
            logger.error(f"日报生成失败: {e}")
            from src.utils.exceptions import ReportGenerationError
            raise ReportGenerationError(f"日报生成失败: {e}") from e

    def _format_news(self, news_data: List[Dict]) -> str:
        """
        格式化新闻数据

        Args:
            news_data: 新闻数据列表

        Returns:
            格式化的新闻文本
        """
        if not news_data:
            return "暂无新闻数据"

        formatted = []
        for item in news_data[:20]:  # 限制数量
            title = item.get('title', '')
            content = item.get('cleaned_content', '') or item.get('content', '')
            formatted.append(f"- {title}: {content[:100]}")

        return "\n".join(formatted)

    def _format_market(self, market_data: Dict) -> str:
        """
        格式化市场数据

        Args:
            market_data: 市场数据字典

        Returns:
            格式化的市场数据文本
        """
        if not market_data:
            return "暂无市场数据"

        formatted = []

        if market_data.get('industry_flow'):
            formatted.append("行业资金流:")
            for item in market_data['industry_flow'][:5]:
                formatted.append(f"  - {item}")

        if market_data.get('main_flow'):
            formatted.append("主力资金流:")
            for item in market_data['main_flow'][:5]:
                formatted.append(f"  - {item}")

        return "\n".join(formatted)


# 全局日报生成器实例
report_generator = ReportGenerator()
