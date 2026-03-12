"""Tests for the retry decorator module."""
from src.utils.retry import retry_on_failure
from src.utils.exceptions import DataCollectionError
import pytest


def test_retry_on_failure_succeeds_on_first_try():
    """Test that retry decorator succeeds on first try."""
    call_count = 0

    @retry_on_failure(max_retries=3, delay=0.01)
    def test_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = test_func()
    assert result == "success"
    assert call_count == 1


def test_retry_on_failure_retries_on_exception():
    """Test that retry decorator retries on exception."""
    call_count = 0

    @retry_on_failure(max_retries=3, delay=0.01, exceptions=(ValueError,))
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Test error")
        return "success"

    result = test_func()
    assert result == "success"
    assert call_count == 2


def test_retry_on_failure_fails_after_max_retries():
    """Test that retry decorator fails after max retries."""
    call_count = 0

    @retry_on_failure(max_retries=2, delay=0.01, exceptions=(ValueError,))
    def test_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        test_func()

    assert call_count == 2


def test_retry_on_failure_does_not_retry_other_exceptions():
    """Test that retry decorator does not retry on other exceptions."""
    call_count = 0

    @retry_on_failure(max_retries=3, delay=0.01, exceptions=(ValueError,))
    def test_func():
        nonlocal call_count
        call_count += 1
        raise TypeError("Different error")

    with pytest.raises(TypeError, match="Different error"):
        test_func()

    assert call_count == 1


def test_retry_on_failure_with_custom_exception():
    """Test that retry decorator works with custom exceptions."""
    call_count = 0

    @retry_on_failure(max_retries=3, delay=0.01, exceptions=(DataCollectionError,))
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise DataCollectionError("Collection failed")
        return "success"

    result = test_func()
    assert result == "success"
    assert call_count == 2
