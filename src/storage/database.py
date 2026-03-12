"""数据库模块，负责SQLite数据存储"""
import sqlite3
from pathlib import Path
from loguru import logger
from typing import List, Dict
from datetime import datetime


class Database:
    """数据库类，负责SQLite数据存储"""

    def __init__(self, db_path: Path = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        from config.settings import config
        self.db_path = db_path or config.database.sqlite_path
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_tables()

    def _create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()

        # 新闻表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                source TEXT,
                publish_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 日报表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT,
                report_type TEXT,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()
        logger.debug("数据库表创建完成")

    def save_news(self, news_list: List[Dict]):
        """
        保存新闻到数据库

        Args:
            news_list: 新闻列表，每项包含title, content, source, time等字段
        """
        if not news_list:
            logger.warning("新闻列表为空，跳过保存")
            return

        cursor = self.conn.cursor()
        for news in news_list:
            cursor.execute("""
                INSERT INTO news (title, content, source, publish_time)
                VALUES (?, ?, ?, ?)
            """, (
                news.get('title', ''),
                news.get('content', '') or news.get('cleaned_content', ''),
                news.get('source', ''),
                news.get('time', '')
            ))
        self.conn.commit()
        logger.info(f"保存新闻: {len(news_list)} 条")

    def save_report(self, report_date: str, report_type: str, content: str):
        """
        保存日报到数据库

        Args:
            report_date: 报告日期 (YYYY-MM-DD)
            report_type: 报告类型 (pre_market/mid_close/after_close)
            content: 报告内容
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reports (report_date, report_type, content)
            VALUES (?, ?, ?)
        """, (report_date, report_type, content))
        self.conn.commit()
        logger.info(f"保存日报: {report_date} - {report_type}")

    def get_news_count(self) -> int:
        """
        获取新闻总数

        Returns:
            新闻总数
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM news")
        return cursor.fetchone()[0]

    def get_reports_count(self) -> int:
        """
        获取日报总数

        Returns:
            日报总数
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reports")
        return cursor.fetchone()[0]

    def get_latest_report(self, report_type: str = None) -> Dict:
        """
        获取最新的日报

        Args:
            report_type: 报告类型，如果为None则获取所有类型中最新的一份

        Returns:
            包含报告信息的字典
        """
        cursor = self.conn.cursor()

        if report_type:
            cursor.execute("""
                SELECT report_date, report_type, content, created_at
                FROM reports
                WHERE report_type = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (report_type,))
        else:
            cursor.execute("""
                SELECT report_date, report_type, content, created_at
                FROM reports
                ORDER BY created_at DESC
                LIMIT 1
            """)

        result = cursor.fetchone()
        if result:
            return {
                'report_date': result[0],
                'report_type': result[1],
                'content': result[2],
                'created_at': result[3]
            }
        return None

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        logger.debug("数据库连接已关闭")


# 全局数据库实例
database = Database()
