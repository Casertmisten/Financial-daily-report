"""状态定义模块

此模块定义 LangGraph 工作流中使用的数据结构和状态。
"""
from typing import TypedDict, List, Dict


class ReportState(TypedDict):
    """日报生成的状态对象"""
    report_type: str
    news_data: List[Dict]
    market_data: Dict
    cleaned_news: List[Dict]
    enriched_news: List[Dict]   # 新增：包含事件类型和标的关联的新闻
    context: str
    report: str
    errors: List[str]
