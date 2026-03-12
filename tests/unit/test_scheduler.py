"""Tests for the scheduler module."""
from unittest.mock import Mock
from src.scheduler.cron_scheduler import ReportScheduler


def test_scheduler_initializes():
    """Test that scheduler initializes properly."""
    scheduler = ReportScheduler()
    assert scheduler.scheduler is not None


def test_scheduler_has_jobs():
    """Test that scheduler has the required number of jobs."""
    scheduler = ReportScheduler()
    jobs = scheduler.scheduler.get_jobs()
    assert len(jobs) == 3


def test_scheduler_job_ids():
    """Test that scheduler has correct job IDs."""
    scheduler = ReportScheduler()
    jobs = scheduler.scheduler.get_jobs()
    job_ids = {job.id for job in jobs}

    assert 'pre_market' in job_ids
    assert 'mid_close' in job_ids
    assert 'after_close' in job_ids


def test_scheduler_run_now_pre_market():
    """Test that scheduler can run pre_market task immediately."""
    scheduler = ReportScheduler()

    # Mock the task function
    original_task = scheduler._pre_market_task
    scheduler._pre_market_task = Mock()

    scheduler.run_now("pre_market")

    scheduler._pre_market_task.assert_called_once()

    # Restore original
    scheduler._pre_market_task = original_task


def test_scheduler_run_now_mid_close():
    """Test that scheduler can run mid_close task immediately."""
    scheduler = ReportScheduler()

    # Mock the task function
    original_task = scheduler._mid_close_task
    scheduler._mid_close_task = Mock()

    scheduler.run_now("mid_close")

    scheduler._mid_close_task.assert_called_once()

    # Restore original
    scheduler._mid_close_task = original_task


def test_scheduler_run_now_after_close():
    """Test that scheduler can run after_close task immediately."""
    scheduler = ReportScheduler()

    # Mock the task function
    original_task = scheduler._after_close_task
    scheduler._after_close_task = Mock()

    scheduler.run_now("after_close")

    scheduler._after_close_task.assert_called_once()

    # Restore original
    scheduler._after_close_task = original_task


def test_scheduler_run_now_invalid_type():
    """Test that scheduler handles invalid task type gracefully."""
    scheduler = ReportScheduler()

    # Should not raise exception
    scheduler.run_now("invalid_type")


def test_scheduler_task_names():
    """Test that scheduler tasks have correct names."""
    scheduler = ReportScheduler()
    jobs = scheduler.scheduler.get_jobs()

    job_names = {job.name for job in jobs}

    assert '开盘前日报' in job_names
    assert '午间日报' in job_names
    assert '收盘日报' in job_names
