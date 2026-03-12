"""数据库模块，负责SQLite数据存储"""
import sqlite3
import json
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

        # 新闻分析表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER,
                event_type TEXT,
                event_subtype TEXT,
                direct_stocks TEXT,
                indirect_stocks TEXT,
                concepts TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (news_id) REFERENCES news(id)
            )
        """)

        self.conn.commit()
        logger.debug("数据库表创建完成")

    def save_news(self, news_list: List[Dict]) -> List[int]:
        """
        保存新闻到数据库

        Args:
            news_list: 新闻列表，每项包含title, content, source, time等字段

        Returns:
            插入的新闻 ID 列表
        """
        if not news_list:
            logger.warning("新闻列表为空，跳过保存")
            return []

        cursor = self.conn.cursor()
        news_ids = []
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
            news_ids.append(cursor.lastrowid)
        self.conn.commit()
        logger.info(f"保存新闻: {len(news_list)} 条")
        return news_ids

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

    def save_news_analysis(self, analysis_list: List[Dict]) -> List[int]:
        """
        保存新闻分析结果到数据库

        Args:
            analysis_list: 分析结果列表，每项必须包含 news_id 字段

        Returns:
            插入的分析记录 ID 列表

        注意：
            analysis_list 中的每一项必须包含 'news_id' 字段，
            该 ID 应该来自 save_news() 方法的返回值
        """
        if not analysis_list:
            logger.warning("分析列表为空，跳过保存")
            return []

        cursor = self.conn.cursor()
        analysis_ids = []

        for analysis in analysis_list:
            # 验证 news_id 存在
            if 'news_id' not in analysis:
                logger.warning(f"分析记录缺少 news_id，跳过: {analysis.get('title', '未知')}")
                continue

            # 将列表转换为 JSON 字符串存储
            direct_stocks = json.dumps(analysis.get('related_stocks', {}).get('direct', []), ensure_ascii=False)
            indirect_stocks = json.dumps(analysis.get('related_stocks', {}).get('indirect', []), ensure_ascii=False)
            concepts = json.dumps(analysis.get('related_stocks', {}).get('concepts', []), ensure_ascii=False)

            cursor.execute("""
                INSERT INTO news_analysis (news_id, event_type, event_subtype, direct_stocks, indirect_stocks, concepts)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                analysis.get('news_id'),
                analysis.get('event_type', ''),
                analysis.get('event_subtype', ''),
                direct_stocks,
                indirect_stocks,
                concepts
            ))
            analysis_ids.append(cursor.lastrowid)

        self.conn.commit()
        logger.info(f"保存新闻分析: {len(analysis_ids)} 条")
        return analysis_ids

    def save_enriched_news(self, news_list: List[Dict], analysis_list: List[Dict]) -> Dict[str, List[int]]:
        """
        保存新闻和分析结果（完整流程）

        Args:
            news_list: 新闻列表（来自 cleaned_news）
            analysis_list: 分析结果列表（来自 enriched_news）

        Returns:
            {
                'news_ids': [插入的新闻 ID 列表],
                'analysis_ids': [插入的分析 ID 列表]
            }

        注意：
            news_list 和 analysis_list 应该长度相同且一一对应
            自动将 news_id 关联到 analysis_list 中的对应项
        """
        # 先保存新闻
        news_ids = self.save_news(news_list)

        # 将 news_id 添加到分析结果中
        for i, analysis in enumerate(analysis_list):
            if i < len(news_ids):
                analysis['news_id'] = news_ids[i]

        # 保存分析结果
        analysis_ids = self.save_news_analysis(analysis_list)

        return {
            'news_ids': news_ids,
            'analysis_ids': analysis_ids
        }

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
