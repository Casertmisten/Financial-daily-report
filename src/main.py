"""主程序入口，负责协调整个日报生成流程"""
from loguru import logger
from src.workflow.graph import report_graph
from src.generators.llm_client import llm_client
from src.utils.exceptions import ReportGenerationError
from config.settings import config
from datetime import datetime


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

    # 初始状态
    initial_state = {
        "report_type": report_type,
        "news_data": [],
        "market_data": {},
        "cleaned_news": [],
        "context": "",
        "report": "",
        "errors": []
    }

    try:
        # 执行工作流图
        result = report_graph.invoke(initial_state)

        logger.success(f"日报生成完成: {report_type}")
        return result["report"]

    except Exception as e:
        logger.critical(f"工作流执行失败: {e}")
        raise ReportGenerationError(f"日报生成失败: {e}") from e


def main():
    """主入口"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "run":
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
