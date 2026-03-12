"""主程序入口，负责协调整个日报生成流程"""
from loguru import logger
from src.collectors.news_collector import NewsCollector
from src.collectors.market_collector import MarketCollector
from src.processors.cleaner import RuleCleaner, LLMCleaner
from src.rag.embeddings import embedding_generator
from src.rag.vector_store import vector_store
from src.rag.retriever import rag_retriever
from src.generators.report_gen import report_generator
from src.storage.database import database
from datetime import datetime
from pathlib import Path
from config.settings import config
from src.utils.exceptions import DataCollectionError, ReportGenerationError
from src.generators.llm_client import llm_client
import hashlib


def generate_daily_report(report_type: str = "after_close") -> str:
    """
    生成日报主流程

    Args:
        report_type: 报告类型 (pre_market/mid_close/after_close)

    Returns:
        生成的日报内容

    Raises:
        ReportGenerationError: 日报生成失败时抛出
    """
    logger.info(f"开始生成日报: {report_type}")

    # 步骤0: 测试LLM连通性
    logger.info("=== 步骤0: 测试LLM连通性 ===")
    connection_test = llm_client.test_connection()

    if not connection_test["all_ok"]:
        logger.error("LLM连通性测试失败！")
        if not connection_test["chat_model"]:
            logger.error(f"生成模型不通: {config.llm.chat_model}")
            logger.error("请检查 .env 中的 LLM_BASE_URL 和 LLM_API_KEY")
        if not connection_test["embedding_model"]:
            logger.error(f"嵌入模型不通: {config.embedding.embedding_model}")
            logger.error("请检查 .env 中的 EMBEDDING_BASE_URL")
        raise ReportGenerationError("LLM模型连通性测试失败，请检查配置")

    logger.success("✓ LLM连通性测试通过")

    try:
        # 1. 数据采集
        logger.info("=== 步骤1: 数据采集 ===")
        try:
            news_collector = NewsCollector()
            market_collector = MarketCollector()

            news_data = news_collector.collect()
            market_data = market_collector.collect()

            if not news_data:
                logger.warning("未采集到任何新闻数据")
        except Exception as e:
            logger.error(f"数据采集失败: {e}")
            raise DataCollectionError(f"数据采集失败: {e}") from e

        # 2. 规则清洗
        logger.info("=== 步骤2: 规则清洗 ===")
        rule_cleaner = RuleCleaner()
        news_data = rule_cleaner.clean(news_data)

        # 3. LLM智能清洗（可选）
        logger.info("=== 步骤3: LLM智能清洗 ===")
        try:
            llm_cleaner = LLMCleaner()
            news_data = llm_cleaner.clean(news_data)
        except Exception as e:
            logger.warning(f"LLM清洗失败，使用规则清洗结果: {e}")

        # 4. 存储新闻到SQLite
        logger.info("=== 步骤4: 存储新闻 ===")
        try:
            database.save_news(news_data)
        except Exception as e:
            logger.warning(f"新闻存储失败: {e}")

        # 5. 向量化并存储到Chroma
        logger.info("=== 步骤5: 向量化存储 ===")
        try:
            docs = []
            for item in news_data:
                # 生成唯一ID
                content_str = f"{item['title']}_{item.get('content', '')}"
                doc_id = hashlib.md5(content_str.encode()).hexdigest()

                docs.append({
                    'id': doc_id,
                    'text': f"{item['title']}\n{item.get('cleaned_content', item.get('content', ''))}",
                    'metadata': {
                        'source': item.get('source', ''),
                        'time': item.get('time', ''),
                        'title': item['title']
                    }
                })

            if docs:
                vector_store.add_documents(docs)
        except Exception as e:
            logger.warning(f"向量存储失败: {e}")

        # 6. RAG检索相关历史
        logger.info("=== 步骤6: RAG检索 ===")
        context = ""
        try:
            # 根据今日新闻关键词检索
            if news_data:
                # 使用第一条新闻的标题作为查询
                context = rag_retriever.retrieve(news_data[0]['title'])
        except Exception as e:
            logger.warning(f"RAG检索失败: {e}")

        # 7. 生成日报
        logger.info("=== 步骤7: 生成日报 ===")
        try:
            report = report_generator.generate(news_data, market_data, context)
        except Exception as e:
            logger.error(f"日报生成失败: {e}")
            raise ReportGenerationError(f"日报生成失败: {e}") from e

        # 8. 保存日报
        logger.info("=== 步骤8: 保存日报 ===")
        report_date = datetime.now().strftime("%Y-%m-%d")
        try:
            database.save_report(report_date, report_type, report)
        except Exception as e:
            logger.warning(f"日报保存到数据库失败: {e}")

        # 保存到文件
        try:
            output_file = config.output_dir / f"{report_date}_{report_type}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.success(f"日报已保存: {output_file}")
        except Exception as e:
            logger.warning(f"日报保存到文件失败: {e}")

        logger.success(f"日报生成完成: {report_type}")
        return report

    except DataCollectionError as e:
        logger.error(f"数据采集失败: {e}")
        raise ReportGenerationError("数据采集失败") from e
    except ReportGenerationError:
        raise
    except Exception as e:
        logger.critical(f"未预期错误: {e}")
        raise ReportGenerationError(f"日报生成失败: {e}") from e


def main():
    """主入口"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # 立即运行一次
        report_type = sys.argv[2] if len(sys.argv) > 2 else "after_close"
        try:
            generate_daily_report(report_type)
        except Exception as e:
            logger.error(f"日报生成失败: {e}")
            sys.exit(1)
    else:
        # 启动定时调度
        from src.scheduler.cron_scheduler import ReportScheduler
        scheduler = ReportScheduler()
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("程序退出")
            sys.exit(0)


if __name__ == "__main__":
    main()
