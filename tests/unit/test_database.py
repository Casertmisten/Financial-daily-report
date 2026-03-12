"""Tests for the database module."""
import tempfile
from pathlib import Path
from src.storage.database import Database


def test_database_creates_tables():
    """Test that database creates required tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)

        # 检查表是否存在
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert 'news' in tables
        assert 'reports' in tables
        db.close()


def test_database_saves_news():
    """Test that database can save news."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)

        news = [
            {'title': '测试新闻1', 'content': '内容1', 'source': 'test', 'time': '2024-01-01'},
            {'title': '测试新闻2', 'content': '内容2', 'source': 'test', 'time': '2024-01-02'},
        ]
        db.save_news(news)

        count = db.get_news_count()
        assert count >= 2
        db.close()


def test_database_saves_report():
    """Test that database can save reports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)

        report_date = "2024-01-01"
        report_type = "after_close"
        content = "# 测试日报\n\n这是测试内容"

        db.save_report(report_date, report_type, content)

        # 验证报告已保存
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE report_date = ? AND report_type = ?",
                      (report_date, report_type))
        result = cursor.fetchone()

        assert result is not None
        assert result[1] == report_date
        assert result[2] == report_type
        assert result[3] == content
        db.close()


def test_database_handles_empty_news_list():
    """Test that database handles empty news list gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)

        db.save_news([])

        count = db.get_news_count()
        assert count == 0
        db.close()


def test_database_handles_missing_fields():
    """Test that database handles news with missing fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)

        news = [
            {'title': '测试'},  # 缺少其他字段
        ]
        db.save_news(news)

        count = db.get_news_count()
        assert count >= 1
        db.close()
