"""定时调度器模块，负责定时生成日报"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from config.settings import config
from datetime import datetime


class ReportScheduler:
    """日报定时调度器，使用APScheduler实现定时任务"""

    def __init__(self):
        """初始化调度器"""
        self.scheduler = BlockingScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """设置定时任务"""
        # 解析配置中的时间
        pre_market_time = config.schedule.pre_market.split(":")
        mid_close_time = config.schedule.mid_close.split(":")
        after_close_time = config.schedule.after_close.split(":")

        # 开盘前任务 (8:30)
        self.scheduler.add_job(
            self._pre_market_task,
            trigger=CronTrigger(hour=int(pre_market_time[0]), minute=int(pre_market_time[1])),
            id="pre_market",
            name="开盘前日报"
        )

        # 中午收盘任务 (11:30)
        self.scheduler.add_job(
            self._mid_close_task,
            trigger=CronTrigger(hour=int(mid_close_time[0]), minute=int(mid_close_time[1])),
            id="mid_close",
            name="午间日报"
        )

        # 晚间收盘任务 (15:30)
        self.scheduler.add_job(
            self._after_close_task,
            trigger=CronTrigger(hour=int(after_close_time[0]), minute=int(after_close_time[1])),
            id="after_close",
            name="收盘日报"
        )

        logger.info("定时任务配置完成")

    def _pre_market_task(self):
        """开盘前任务"""
        logger.info(f"[{datetime.now()}] 执行开盘前任务")
        self._generate_report("pre_market")

    def _mid_close_task(self):
        """中午收盘任务"""
        logger.info(f"[{datetime.now()}] 执行中午收盘任务")
        self._generate_report("mid_close")

    def _after_close_task(self):
        """晚间收盘任务"""
        logger.info(f"[{datetime.now()}] 执行晚间收盘任务")
        self._generate_report("after_close")

    def _generate_report(self, report_type: str):
        """
        生成日报

        Args:
            report_type: 报告类型 (pre_market/mid_close/after_close)
        """
        try:
            # 延迟导入避免循环依赖
            from src.main import generate_daily_report
            generate_daily_report(report_type)
        except Exception as e:
            logger.error(f"日报生成失败: {e}")

    def start(self):
        """启动调度器"""
        logger.info("调度器启动，等待定时任务...")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("调度器停止")

    def run_now(self, task_type: str = "after_close"):
        """
        立即运行指定任务

        Args:
            task_type: 任务类型 (pre_market/mid_close/after_close)
        """
        task_map = {
            "pre_market": self._pre_market_task,
            "mid_close": self._mid_close_task,
            "after_close": self._after_close_task,
        }
        if task_type in task_map:
            logger.info(f"立即执行任务: {task_type}")
            task_map[task_type]()
        else:
            logger.error(f"未知任务类型: {task_type}")
