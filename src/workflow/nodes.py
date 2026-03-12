"""LangGraph 工作流节点

此模块定义 LangGraph 工作流中的各个节点函数。
"""
from loguru import logger
from typing import List, Dict, Optional
from src.workflow.state import ReportState
from src.collectors.news_collector import NewsCollector
from src.collectors.market_collector import MarketCollector
from src.processors.cleaner import RuleCleaner, LLMCleaner
from src.storage.database import database
from src.rag.vector_store import vector_store
from src.rag.retriever import rag_retriever
from src.generators.llm_client import llm_client
from config.prompts import PRE_MARKET_PROMPT, MID_CLOSE_PROMPT, AFTER_CLOSE_PROMPT
from config.settings import config
from pathlib import Path
from datetime import datetime
import hashlib


def collect_node(state: ReportState) -> ReportState:
    """数据采集节点

    从 AKShare 采集新闻和市场数据

    Args:
        state: 当前状态

    Returns:
        更新后的状态，包含 news_data 和 market_data
    """
    logger.info("=== 数据采集 ===")

    news_collector = NewsCollector()
    market_collector = MarketCollector()

    news_data = news_collector.collect()
    market_data = market_collector.collect()

    # 统计成功采集的数据
    market_count = sum(1 for v in market_data.values() if v)
    logger.info(f"✓ 采集完成 (新闻: {len(news_data)}, 市场: {market_count}/5)")

    return {**state, "news_data": news_data, "market_data": market_data}


def clean_node(state: ReportState) -> ReportState:
    """数据清洗节点（规则 + LLM）

    先用规则清洗，再用 LLM 智能清洗

    Args:
        state: 当前状态，包含 news_data

    Returns:
        更新后的状态，包含 cleaned_news
    """
    logger.info("=== 数据清洗 ===")

    rule_cleaner = RuleCleaner()
    cleaned = rule_cleaner.clean(state["news_data"])

    # 智能跳过LLM清洗：当新闻数量过多时，跳过LLM清洗以节省时间和token
    LLM_CLEAN_LIMIT = 50  # 最多LLM清洗50条新闻

    if cleaned and len(cleaned) <= LLM_CLEAN_LIMIT:
        try:
            llm_cleaner = LLMCleaner()
            cleaned = llm_cleaner.clean(cleaned)
            logger.info(f"LLM智能清洗完成")
        except Exception as e:
            logger.warning(f"LLM清洗失败，使用规则清洗结果: {e}")
    elif cleaned and len(cleaned) > LLM_CLEAN_LIMIT:
        logger.info(f"新闻数量过多 ({len(cleaned)} 条 > {LLM_CLEAN_LIMIT} 条)，跳过LLM清洗以提升性能")
        logger.info(f"提示：规则清洗已完成，新闻可直接用于深度分析")

    logger.info(f"✓ 清洗完成，保留 {len(cleaned)} 条")

    return {**state, "cleaned_news": cleaned}


def analyze_node(state: ReportState) -> ReportState:
    """深度分析节点

    对清洗后的新闻进行事件抽取、标的关联、智能合并

    Args:
        state: 当前状态，包含 cleaned_news

    Returns:
        更新后的状态，包含 enriched_news
    """
    logger.info("=== 深度分析 ===")

    if not state["cleaned_news"]:
        logger.info("无新闻需要分析")
        return {**state, "enriched_news": []}

    # 检查数据库，只分析新新闻
    from src.storage.database import database
    import hashlib

    new_news = []
    skipped_count = 0

    # 获取数据库中已有的新闻标题hash
    cursor = database.conn.cursor()
    cursor.execute("SELECT title, content FROM news")
    existing_hashes = set()
    for row in cursor.fetchall():
        title, content = row
        content_str = f"{title}{content or ''}"
        content_hash = hashlib.md5(content_str.encode()).hexdigest()
        existing_hashes.add(content_hash)

    # 过滤掉已存在的新闻
    for news in state["cleaned_news"]:
        content_str = f"{news.get('title', '')}{news.get('content', '')}"
        content_hash = hashlib.md5(content_str.encode()).hexdigest()

        if content_hash in existing_hashes:
            skipped_count += 1
        else:
            new_news.append(news)

    if skipped_count > 0:
        logger.info(f"跳过 {skipped_count} 条已存在的新闻，只分析 {len(new_news)} 条新新闻")

    if not new_news:
        logger.info("没有新新闻需要分析")
        # 所有新闻都已存在，返回空列表（避免重复分析）
        return {**state, "enriched_news": []}

    try:
        from src.processors.analyzer import HeavyAnalyzer
        analyzer = HeavyAnalyzer()
        enriched = analyzer.analyze(new_news)
        logger.info(f"✓ 深度分析完成，保留 {len(enriched)} 条")

        # 打印统计信息
        event_types = {}
        for news in enriched:
            et = news.get('event_type', '其他')
            event_types[et] = event_types.get(et, 0) + 1
        logger.info(f"事件类型分布: {event_types}")

        return {**state, "enriched_news": enriched}

    except Exception as e:
        logger.error(f"深度分析失败，使用 cleaned_news: {e}")
        # 回退：将 cleaned_news 作为 enriched_news 返回
        # 添加默认的分析字段
        fallback = [
            {
                **news,
                'event_type': '其他',
                'event_subtype': '',
                'related_stocks': {'direct': [], 'indirect': [], 'concepts': []}
            }
            for news in new_news  # 只对新新闻添加默认字段
        ]
        return {**state, "enriched_news": fallback}


def store_node(state: ReportState) -> ReportState:
    """存储到 SQLite

    将清洗后的新闻和分析结果保存到数据库

    Args:
        state: 当前状态，包含 cleaned_news 和 enriched_news

    Returns:
        未修改的状态
    """
    logger.info("=== 存储新闻 ===")

    if not state["cleaned_news"]:
        logger.info("无新闻需要存储")
        return state

    try:
        # 如果有 enriched_news，使用 save_enriched_news 同时保存新闻和分析结果
        if state.get("enriched_news"):
            result = database.save_enriched_news(state["cleaned_news"], state["enriched_news"])
            logger.info(f"✓ 保存新闻: {len(result['news_ids'])} 条, 分析: {len(result['analysis_ids'])} 条")
        else:
            # 向后兼容：只保存基础新闻
            database.save_news(state["cleaned_news"])
            logger.info(f"✓ 保存 {len(state['cleaned_news'])} 条")
    except Exception as e:
        logger.error(f"保存新闻失败: {e}")
        # 不中断流程，继续执行

    return state


def vectorize_node(state: ReportState) -> ReportState:
    """向量化并存储到 Chroma

    将清洗后的新闻向量化并存储到向量数据库

    Args:
        state: 当前状态，包含 cleaned_news

    Returns:
        未修改的状态
    """
    logger.info("=== 向量化存储 ===")

    if not state["cleaned_news"]:
        logger.info("无新闻需要向量化")
        return state

    docs = []
    for item in state["cleaned_news"]:
        content_str = f"{item['title']}_{item.get('content', '')}"
        doc_id = hashlib.md5(content_str.encode()).hexdigest()

        # 优先使用清洗后的内容
        content = item.get('cleaned_content') or item.get('content', '')
        docs.append({
            'id': doc_id,
            'text': f"{item['title']}\n{content}",
            'metadata': {
                'source': item.get('source', ''),
                'time': item.get('time', ''),
                'title': item['title']
            }
        })

    if docs:
        try:
            vector_store.add_documents(docs)
            logger.info(f"✓ 向量化 {len(docs)} 条")
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            # 不中断流程，继续执行

    return state


def rag_node(state: ReportState) -> ReportState:
    """RAG 检索历史上下文

    从向量数据库检索相关历史新闻

    Args:
        state: 当前状态，包含 cleaned_news

    Returns:
        更新后的状态，包含 context
    """
    logger.info("=== RAG 检索 ===")

    context = ""
    if state["cleaned_news"]:
        try:
            # 使用第一条新闻的标题作为查询
            query = state["cleaned_news"][0].get('title', '')
            context = rag_retriever.retrieve(query)
            logger.info("✓ RAG 检索完成")
        except Exception as e:
            logger.warning(f"RAG检索失败: {e}")
            context = "无相关历史信息"

    return {**state, "context": context}


def _format_news(news_data: List[Dict], focus: str = "analysis") -> str:
    """格式化新闻数据

    Args:
        news_data: 新闻数据列表
        focus: 关注点 (prediction/intraday/analysis)

    Returns:
        格式化的新闻文本
    """
    if not news_data:
        return "暂无新闻数据"

    formatted = []
    # 根据关注点限制数量
    limit = 20 if focus == "analysis" else 15

    for item in news_data[:limit]:
        title = item.get('title', '')
        # 优先使用清洗后的内容
        content = item.get('cleaned_content', '') or item.get('content', '')

        # 截断过长的内容
        if len(content) > 100:
            content = content[:100] + "..."

        formatted.append(f"- {title}: {content}")

    return "\n".join(formatted)


def _format_news_enriched(news_data: List[Dict], focus: str = "analysis") -> str:
    """
    格式化增强后的新闻数据（包含事件类型和标的）

    Args:
        news_data: enriched_news 列表
        focus: 关注点，决定显示的新闻数量

    Returns:
        格式化的新闻文本，包含事件和标的信息
    """
    if not news_data:
        return "暂无新闻数据"

    formatted = []
    limit = 20 if focus == "analysis" else 15

    for item in news_data[:limit]:
        title = item.get('title', '')
        event_type = item.get('event_type', '其他')
        sentiment = item.get('sentiment', 'neutral')
        importance = item.get('importance', 3)

        # 标的信息
        stocks = item.get('related_stocks', {})
        direct = stocks.get('direct', [])
        concepts = stocks.get('concepts', [])

        # 情感图标
        sentiment_icon = {'positive': '📈', 'neutral': '➡️', 'negative': '📉'}

        # 构建格式化输出
        stock_info = ''
        if direct:
            stock_info = f" [{', '.join(direct)}]"

        line = f"- [{event_type}]{sentiment_icon.get(sentiment, '')} {title}{stock_info}"
        formatted.append(line)
        formatted.append(f"  重要性: {importance}/5")

        if concepts:
            formatted.append(f"  相关概念: {', '.join(concepts[:3])}")

    return '\n'.join(formatted)


def _format_market(market_data: Dict, focus: str = "deep") -> str:
    """格式化市场数据

    Args:
        market_data: 市场数据字典
        focus: 关注点 (pre_market/realtime/deep)

    Returns:
        格式化的市场数据文本
    """
    if not market_data:
        return "暂无市场数据"

    formatted = []

    # 格式化行业资金流
    if market_data.get('industry_flow'):
        formatted.append("行业资金流:")
        for item in market_data['industry_flow'][:5]:
            # 尝试获取有用的字段
            name = item.get('name', item.get('行业', '未知'))
            net_amount = item.get('net_amount', item.get('净流入', 'N/A'))
            formatted.append(f"  - {name}: {net_amount}")

    # 格式化主力资金流
    if market_data.get('main_flow'):
        formatted.append("主力资金流:")
        for item in market_data['main_flow'][:5]:
            name = item.get('name', item.get('名称', '未知'))
            net_amount = item.get('net_amount', item.get('净流入', 'N/A'))
            formatted.append(f"  - {name}: {net_amount}")

    # 格式化概念资金流
    if market_data.get('concept_flow'):
        formatted.append("概念资金流:")
        for item in market_data['concept_flow'][:5]:
            name = item.get('name', item.get('概念', '未知'))
            net_amount = item.get('net_amount', item.get('净流入', 'N/A'))
            formatted.append(f"  - {name}: {net_amount}")

    return "\n".join(formatted) if formatted else "暂无市场数据"


def pre_market_generate_node(state: ReportState) -> ReportState:
    """盘前早报生成节点

    生成侧重今日预测和准备的盘前早报

    Args:
        state: 当前状态

    Returns:
        更新后的状态，包含 report
    """
    logger.info("=== 生成盘前早报 ===")

    # Use enriched_news if available, otherwise fall back to cleaned_news
    news_data = state.get("enriched_news") or state.get("cleaned_news", [])
    news_summary = _format_news_enriched(news_data, focus="prediction")
    market_summary = _format_market(state["market_data"], focus="pre_market")

    # 使用当前时间
    current_date = datetime.now().strftime("%Y-%m-%d")

    prompt = PRE_MARKET_PROMPT.format(
        current_date=current_date,
        news_data=news_summary,
        market_data=market_summary,
        historical_context=state["context"]
    )

    try:
        report = llm_client.chat([
            {"role": "system", "content": "你是专业中国金融分析师。现在是早上8:30，请生成盘前早报，重点关注今日预测、美股隔夜回顾、A股开盘预测。用中文输出。"},
            {"role": "user", "content": prompt}
        ])
        logger.success("✓ 盘前早报生成完成")
    except Exception as e:
        logger.error(f"盘前早报生成失败: {e}")
        report = f"# 盘前早报生成失败\n\n错误: {str(e)}\n\n## 新闻数据\n{news_summary}\n\n## 市场数据\n{market_summary}"

    return {**state, "report": report}


def mid_close_generate_node(state: ReportState) -> ReportState:
    """盘中快讯生成节点

    生成侧重实时动态和异常的盘中快讯

    Args:
        state: 当前状态

    Returns:
        更新后的状态，包含 report
    """
    logger.info("=== 生成盘中快讯 ===")

    # Use enriched_news if available, otherwise fall back to cleaned_news
    news_data = state.get("enriched_news") or state.get("cleaned_news", [])
    news_summary = _format_news_enriched(news_data, focus="intraday")
    market_summary = _format_market(state["market_data"], focus="realtime")

    # 使用当前时间
    current_date = datetime.now().strftime("%Y-%m-%d")

    prompt = MID_CLOSE_PROMPT.format(
        current_date=current_date,
        news_data=news_summary,
        market_data=market_summary,
        historical_context=state["context"]
    )

    try:
        report = llm_client.chat([
            {"role": "system", "content": "你是专业中国金融分析师。现在是中午11:30，请生成盘中快讯，重点关注上午走势总结、行业资金流向、概念板块异动。用中文输出。"},
            {"role": "user", "content": prompt}
        ])
        logger.success("✓ 盘中快讯生成完成")
    except Exception as e:
        logger.error(f"盘中快讯生成失败: {e}")
        report = f"# 盘中快讯生成失败\n\n错误: {str(e)}\n\n## 新闻数据\n{news_summary}\n\n## 市场数据\n{market_summary}"

    return {**state, "report": report}


def after_close_generate_node(state: ReportState) -> ReportState:
    """盘后总结生成节点

    生成侧重深度分析的盘后总结

    Args:
        state: 当前状态

    Returns:
        更新后的状态，包含 report
    """
    logger.info("=== 生成盘后总结 ===")

    # Use enriched_news if available, otherwise fall back to cleaned_news
    news_data = state.get("enriched_news") or state.get("cleaned_news", [])
    news_summary = _format_news_enriched(news_data, focus="analysis")
    market_summary = _format_market(state["market_data"], focus="deep")

    # 使用当前时间
    current_date = datetime.now().strftime("%Y-%m-%d")

    prompt = AFTER_CLOSE_PROMPT.format(
        current_date=current_date,
        news_data=news_summary,
        market_data=market_summary,
        historical_context=state["context"]
    )

    try:
        report = llm_client.chat([
            {"role": "system", "content": "你是专业中国金融分析师。现在是下午15:30，请生成盘后深度总结，重点关注全日行情回顾、资金面分析、深度市场解读。用中文输出。"},
            {"role": "user", "content": prompt}
        ])
        logger.success("✓ 盘后总结生成完成")
    except Exception as e:
        logger.error(f"盘后总结生成失败: {e}")
        report = f"# 盘后总结生成失败\n\n错误: {str(e)}\n\n## 新闻数据\n{news_summary}\n\n## 市场数据\n{market_summary}"

    return {**state, "report": report}


def save_node(state: ReportState) -> ReportState:
    """保存日报

    将生成的日报保存到数据库和文件

    Args:
        state: 当前状态，包含 report 和 report_type

    Returns:
        未修改的状态
    """
    logger.info("=== 保存日报 ===")

    report_date = datetime.now().strftime("%Y-%m-%d")

    # 保存到数据库
    try:
        database.save_report(report_date, state["report_type"], state["report"])
        logger.info(f"✓ 保存到数据库: {report_date} - {state['report_type']}")
    except Exception as e:
        logger.error(f"保存到数据库失败: {e}")
        # 不中断流程

    # 保存到文件
    try:
        output_file = config.output_dir / f"{report_date}_{state['report_type']}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(state["report"])
        logger.success(f"✓ 日报已保存到文件: {output_file}")
    except Exception as e:
        logger.error(f"保存到文件失败: {e}")
        # 不中断流程

    return state


def route_by_report_type(state: ReportState) -> str:
    """根据报告类型路由到不同生成节点

    Args:
        state: 当前状态，包含 report_type

    Returns:
        目标节点名称
    """
    route_map = {
        "pre_market": "pre_market_generate",
        "mid_close": "mid_close_generate",
        "after_close": "after_close_generate"
    }
    return route_map.get(state["report_type"], "after_close_generate")
