import os
from config.settings import config

def test_config_has_llm_settings():
    assert hasattr(config, 'llm')
    assert hasattr(config.llm, 'base_url')
    assert hasattr(config.llm, 'chat_model')

def test_config_has_embedding_settings():
    assert hasattr(config, 'embedding')
    assert hasattr(config.embedding, 'base_url')
    assert hasattr(config.embedding, 'embedding_model')

def test_config_has_schedule_settings():
    assert hasattr(config, 'schedule')
    assert config.schedule.pre_market == "08:30"

from src.utils import logger
from loguru import logger as loguru_logger

def test_logger_is_configured():
    # Logger should be configured after import
    assert len(loguru_logger._core.handlers) > 0
