"""重试装饰器模块，提供失败重试功能"""
from functools import wraps
import time
from loguru import logger


def retry_on_failure(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    失败重试装饰器

    Args:
        max_retries: 最大重试次数，默认3次
        delay: 初始延迟时间（秒），默认1秒
        backoff: 退避系数，每次重试后延迟时间乘以该系数，默认2
        exceptions: 需要重试的异常类型元组，默认所有Exception

    Returns:
        装饰器函数
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"{func.__name__} 失败，已重试 {max_retries} 次: {e}")
                        raise

                    logger.warning(
                        f"{func.__name__} 失败 ({retries}/{max_retries}): {e}, "
                        f"{current_delay}秒后重试..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator
