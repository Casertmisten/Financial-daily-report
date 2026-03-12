# 金融日报机器人实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 构建一个基于LLM和RAG的自动金融日报生成系统，定时采集新闻和市场数据，智能分析并生成结构化Markdown日报。

**架构：** Python脚本 + APScheduler定时任务，使用AKShare获取数据，OpenAI兼容API进行LLM处理和向量化，Chroma存储向量，SQLite存储元数据，最终输出Markdown日报。

**技术栈：** Python, uv, AKShare, OpenAI API, ChromaDB, APScheduler, Loguru, SQLite

---

## Phase 1: 项目初始化与基础设施

### Task 1: 初始化uv项目

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: 初始化uv项目**

Run: `cd /home/caser/文档/code/Financial-daily-report && uv init --no-readme`

**Step 2: 创建 pyproject.toml**

```toml
[project]
name = "financial-daily-report"
version = "0.1.0"
description = "基于LLM和RAG的金融日报生成系统"
requires-python = ">=3.10"
dependencies = [
    "akshare>=1.12.0",
    "openai>=1.12.0",
    "chromadb>=0.4.0",
    "apscheduler>=3.10.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]
```

**Step 3: 创建 .env.example**

```bash
# ===== LLM生成模型配置 =====
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_api_key
CHAT_MODEL=gpt-4o
CLEAN_MODEL=gpt-4o-mini

# ===== Embedding模型配置 =====
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small

# ===== 定时任务时间 =====
PRE_MARKET_TIME=08:30
MID_CLOSE_TIME=11:30
AFTER_CLOSE_TIME=15:30

# ===== 日志配置 =====
LOG_LEVEL=INFO
```

**Step 4: 创建 .gitignore**

```
.env
__pycache__/
*.pyc
.venv/
data/
outputs/
*.log
.pytest_cache/
```

**Step 5: 创建 README.md**

```markdown
# 金融日报机器人

基于LLM和RAG技术的智能金融日报生成系统。

## 功能特性

- 自动定时采集财经新闻和市场数据
- LLM智能清洗和分析数据
- RAG技术增强内容关联
- 生成结构化Markdown日报

## 快速开始

\`\`\`bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入API密钥

# 运行
uv run python src/main.py
\`\`\`

## 定时任务

- 开盘前 8:30：财经早餐
- 中午收盘 11:30：午间快讯
- 晚间收盘 15:30：收盘总结
```

**Step 6: 安装依赖**

Run: `uv sync`

**Step 7: Commit**

```bash
git add pyproject.toml .env.example .gitignore README.md
git commit -m "feat: initialize project with uv and dependencies"
```

---

### Task 2: 创建项目目录结构

**Files:**
- Create: `config/__init__.py`, `config/settings.py`, `config/prompts.py`
- Create: `src/__init__.py`, `src/main.py`
- Create: `src/collectors/__init__.py`
- Create: `src/processors/__init__.py`
- Create: `src/rag/__init__.py`
- Create: `src/generators/__init__.py`
- Create: `src/storage/__init__.py`
- Create: `src/scheduler/__init__.py`
- Create: `src/utils/__init__.py`
- Create: `data/`, `outputs/`, `tests/`

**Step 1: 创建目录结构**

Run: `mkdir -p config src/collectors src/processors src/rag src/generators src/storage src/scheduler src/utils data outputs tests/unit tests/integration`

**Step 2: 创建所有 __init__.py 文件**

Run: `touch config/__init__.py src/__init__.py src/collectors/__init__.py src/processors/__init__.py src/rag/__init__.py src/generators/__init__.py src/storage/__init__.py src/scheduler/__init__.py src/utils/__init__.py tests/__init__.py`

**Step 3: 创建占位文件**

Run: `touch config/settings.py config/prompts.py src/main.py`

**Step 4: Verify structure**

Run: `tree -L 2 -I '__pycache__|*.pyc'`
Expected: 显示完整目录结构

**Step 5: Commit**

```bash
git add .
git commit -m "feat: create project directory structure"
```

---

### Task 3: 实现配置管理模块

**Files:**
- Create: `config/settings.py`
- Create: `src/utils/logger.py`

**Step 1: Write the failing test**

Create `tests/test_config.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with "module 'config.settings' has no attribute 'config'"

**Step 3: Implement config/settings.py**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LLMConfig:
    base_url: str
    api_key: str
    chat_model: str
    clean_model: str

@dataclass
class EmbeddingConfig:
    base_url: str
    api_key: str
    embedding_model: str

@dataclass
class ScheduleConfig:
    pre_market: str = "08:30"
    mid_close: str = "11:30"
    after_close: str = "15:30"

@dataclass
class DatabaseConfig:
    sqlite_path: Path = Path("data/financial.db")
    chroma_path: Path = Path("data/chroma_db")

@dataclass
class NewsSourceConfig:
    sources: List[str] = None
    enabled_sources: List[str] = None

    def __post_init__(self):
        self.sources = [
            "cjzc_em", "global_em", "global_sina",
            "global_futu", "global_ths", "global_cls",
        ]
        self.enabled_sources = self.sources

@dataclass
class Config:
    llm: LLMConfig
    embedding: EmbeddingConfig
    schedule: ScheduleConfig = ScheduleConfig()
    database: DatabaseConfig = DatabaseConfig()
    news: NewsSourceConfig = NewsSourceConfig()

    output_dir: Path = Path("outputs")
    log_dir: Path = Path("data/logs")

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.database.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.database.chroma_path.mkdir(parents=True, exist_ok=True)

config = Config(
    llm=LLMConfig(
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("LLM_API_KEY", ""),
        chat_model=os.getenv("CHAT_MODEL", "gpt-4o"),
        clean_model=os.getenv("CLEAN_MODEL", "gpt-4o-mini"),
    ),
    embedding=EmbeddingConfig(
        base_url=os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("EMBEDDING_API_KEY", ""),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
    )
)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Implement logger in src/utils/logger.py**

```python
from loguru import logger
import sys
from config.settings import config

def setup_logger():
    logger.remove()

    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
        colorize=True,
    )

    logger.add(
        config.log_dir / "all_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="00:00",
        retention="30 days",
    )

    logger.add(
        config.log_dir / "error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="00:00",
        retention="90 days",
    )

    return logger

setup_logger()
```

**Step 6: Update test to check logger**

```python
from src.utils import logger
from loguru import logger as loguru_logger

def test_logger_is_configured():
    # Logger should be configured after import
    assert len(loguru_logger._core.handlers) > 0
```

**Step 7: Run tests**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add config/settings.py src/utils/logger.py tests/test_config.py
git commit -m "feat: implement config management and logger"
```

---

## Phase 2: 数据采集模块

### Task 4: 实现新闻采集器

**Files:**
- Create: `src/collectors/news_collector.py`
- Create: `tests/unit/test_news_collector.py`

**Step 1: Write the failing test**

Create `tests/unit/test_news_collector.py`:

```python
import pytest
from src.collectors.news_collector import NewsCollector
from src.utils.exceptions import DataCollectionError

def test_news_collector_collect_returns_list():
    collector = NewsCollector()
    result = collector.collect()
    assert isinstance(result, list)

def test_news_collector_item_has_required_fields():
    collector = NewsCollector()
    result = collector.collect()
    if len(result) > 0:
        item = result[0]
        assert 'title' in item or 'content' in item
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_news_collector.py -v`
Expected: FAIL with "cannot import 'NewsCollector'"

**Step 3: Create base collector class**

Create `src/collectors/base.py`:

```python
from abc import ABC, abstractmethod
from loguru import logger

class BaseCollector(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def collect(self):
        pass
```

**Step 4: Implement news collector**

Create `src/collectors/news_collector.py`:

```python
import akshare as ak
from loguru import logger
from src.collectors.base import BaseCollector
from typing import List, Dict

class NewsCollector(BaseCollector):
    def __init__(self):
        super().__init__("NewsCollector")

    def collect(self) -> List[Dict]:
        news_list = []

        # 财经早餐 - 东财
        try:
            df = ak.stock_info_cjzc_em()
            for _, row in df.iterrows():
                news_list.append({
                    'source': 'cjzc_em',
                    'title': row.get('标题', ''),
                    'content': row.get('内容', ''),
                    'time': row.get('时间', ''),
                })
            logger.info(f"财经早餐: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"财经早餐采集失败: {e}")

        # 全球财经快讯 - 东财
        try:
            df = ak.stock_info_global_em()
            for _, row in df.iterrows():
                news_list.append({
                    'source': 'global_em',
                    'title': row.get('标题', ''),
                    'content': row.get('内容', ''),
                    'time': row.get('时间', ''),
                })
            logger.info(f"东财全球: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"东财全球采集失败: {e}")

        # 全球财经快讯 - 新浪
        try:
            df = ak.stock_info_global_sina()
            for _, row in df.iterrows():
                news_list.append({
                    'source': 'global_sina',
                    'title': row.get('title', ''),
                    'content': row.get('content', ''),
                    'time': row.get('time', ''),
                })
            logger.info(f"新浪财经: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"新浪财经采集失败: {e}")

        # 快讯 - 富途
        try:
            df = ak.stock_info_global_futu()
            for _, row in df.iterrows():
                news_list.append({
                    'source': 'global_futu',
                    'title': row.get('title', ''),
                    'content': row.get('content', ''),
                    'time': row.get('time', ''),
                })
            logger.info(f"富途牛牛: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"富途牛牛采集失败: {e}")

        # 全球财经直播 - 同花顺
        try:
            df = ak.stock_info_global_ths()
            for _, row in df.iterrows():
                news_list.append({
                    'source': 'global_ths',
                    'title': row.get('title', ''),
                    'content': row.get('content', ''),
                    'time': row.get('time', ''),
                })
            logger.info(f"同花顺: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"同花顺采集失败: {e}")

        # 电报 - 财联社
        try:
            df = ak.stock_info_global_cls(symbol="全部")
            for _, row in df.iterrows():
                news_list.append({
                    'source': 'global_cls',
                    'title': row.get('标题', ''),
                    'content': row.get('内容', ''),
                    'time': row.get('时间', ''),
                })
            logger.info(f"财联社: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"财联社采集失败: {e}")

        logger.success(f"新闻采集完成，共获取 {len(news_list)} 条")
        return news_list
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_news_collector.py -v -s`
Expected: PASS (可能需要网络连接)

**Step 6: Commit**

```bash
git add src/collectors/ tests/unit/test_news_collector.py
git commit -m "feat: implement news collector with multiple sources"
```

---

### Task 5: 实现市场数据采集器

**Files:**
- Create: `src/collectors/market_collector.py`
- Create: `tests/unit/test_market_collector.py`

**Step 1: Write the failing test**

Create `tests/unit/test_market_collector.py`:

```python
from src.collectors.market_collector import MarketCollector

def test_market_collector_collect_returns_dict():
    collector = MarketCollector()
    result = collector.collect()
    assert isinstance(result, dict)

def test_market_collector_has_stocks_data():
    collector = MarketCollector()
    result = collector.collect()
    assert 'stocks' in result
    assert 'industry_flow' in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_market_collector.py -v`
Expected: FAIL with "cannot import 'MarketCollector'"

**Step 3: Implement market collector**

Create `src/collectors/market_collector.py`:

```python
import akshare as ak
from loguru import logger
from src.collectors.base import BaseCollector
from typing import Dict, List

class MarketCollector(BaseCollector):
    def __init__(self):
        super().__init__("MarketCollector")

    def collect(self) -> Dict:
        result = {
            'stocks': [],
            'industry_flow': [],
            'concept_flow': [],
            'main_flow': [],
            'lhb': []
        }

        # 沪深京A股实时行情
        try:
            df = ak.stock_zh_a_spot_em()
            result['stocks'] = df.to_dict('records')[:100]  # 限制前100条
            logger.info(f"A股行情: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"A股行情采集失败: {e}")

        # 行业资金流
        try:
            df = ak.stock_fund_flow_industry(symbol="即时")
            result['industry_flow'] = df.to_dict('records')
            logger.info(f"行业资金流: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"行业资金流采集失败: {e}")

        # 概念资金流
        try:
            df = ak.stock_fund_flow_concept(symbol="即时")
            result['concept_flow'] = df.to_dict('records')
            logger.info(f"概念资金流: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"概念资金流采集失败: {e}")

        # 主力资金流
        try:
            df = ak.stock_main_fund_flow(symbol="全部股票")
            result['main_flow'] = df.to_dict('records')[:50]  # 限制前50条
            logger.info(f"主力资金流: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"主力资金流采集失败: {e}")

        # 龙虎榜（获取最近一天）
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")
            df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
            result['lhb'] = df.to_dict('records')
            logger.info(f"龙虎榜: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"龙虎榜采集失败: {e}")

        logger.success(f"市场数据采集完成")
        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_market_collector.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/collectors/market_collector.py tests/unit/test_market_collector.py
git commit -m "feat: implement market data collector"
```

---

## Phase 3: 数据清洗模块

### Task 6: 实现规则清洗器

**Files:**
- Create: `src/processors/cleaner.py`
- Create: `tests/unit/test_cleaner.py`

**Step 1: Write the failing test**

Create `tests/unit/test_cleaner.py`:

```python
from src.processors.cleaner import RuleCleaner

def test_rule_cleaner_removes_duplicates():
    cleaner = RuleCleaner()
    news = [
        {'title': '新闻A', 'content': '内容A'},
        {'title': '新闻A', 'content': '内容A'},
        {'title': '新闻B', 'content': '内容B'},
    ]
    result = cleaner.clean(news)
    assert len(result) == 2

def test_rule_cleaner_normalizes_time():
    cleaner = RuleCleaner()
    news = [
        {'title': '新闻', 'content': '内容', 'time': '2024-03-11 08:30'},
    ]
    result = cleaner.clean(news)
    assert 'time' in result[0]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_cleaner.py -v`
Expected: FAIL

**Step 3: Implement rule cleaner**

Create `src/processors/cleaner.py`:

```python
from loguru import logger
from typing import List, Dict
import hashlib
from datetime import datetime
import re

class RuleCleaner:
    def __init__(self):
        self.seen_hashes = set()

    def clean(self, news_list: List[Dict]) -> List[Dict]:
        cleaned = []

        for item in news_list:
            # 计算内容hash用于去重
            content_str = f"{item.get('title', '')}{item.get('content', '')}"
            content_hash = hashlib.md5(content_str.encode()).hexdigest()

            if content_hash in self.seen_hashes:
                continue

            self.seen_hashes.add(content_hash)

            # 清洗数据
            cleaned_item = {
                'title': self._clean_text(item.get('title', '')),
                'content': self._clean_text(item.get('content', '')),
                'source': item.get('source', ''),
                'time': self._normalize_time(item.get('time', '')),
            }

            if cleaned_item['title'] or cleaned_item['content']:
                cleaned.append(cleaned_item)

        logger.info(f"规则清洗: {len(news_list)} -> {len(cleaned)}")
        return cleaned

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', str(text))
        # 移除多余空白
        text = ' '.join(text.split())
        return text.strip()

    def _normalize_time(self, time_str: str) -> str:
        if not time_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 简单的时间标准化
        try:
            return str(time_str).strip()
        except:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_cleaner.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/processors/cleaner.py tests/unit/test_cleaner.py
git commit -m "feat: implement rule-based cleaner"
```

---

### Task 7: 实现LLM智能清洗器

**Files:**
- Modify: `src/processors/cleaner.py`
- Modify: `tests/unit/test_cleaner.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_cleaner.py`:

```python
from unittest.mock import Mock, patch

def test_llm_cleaner_extracts_entities(monkeypatch):
    # Mock LLM response
    mock_response = '''{
        "cleaned_content": "贵州茅台发布年报",
        "entities": ["贵州茅台"],
        "sentiment": "neutral",
        "importance": 3,
        "tags": ["白酒"],
        "is_trash": false
    }'''

    mock_client = Mock()
    mock_client.chat.return_value = mock_response

    from src.processors.cleaner import LLMCleaner
    cleaner = LLMCleaner()
    cleaner.llm_client = mock_client

    news = [{'title': '贵州茅台', 'content': '发布年报'}]
    result = cleaner.clean(news)

    assert len(result) == 1
    assert result[0]['entities'] == ["贵州茅台"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_cleaner.py::test_llm_cleaner_extracts_entities -v`
Expected: FAIL

**Step 3: Create LLM client**

Create `src/generators/llm_client.py`:

```python
from openai import OpenAI
from loguru import logger
from config.settings import config

class LLMClient:
    def __init__(self):
        self.chat_client = OpenAI(
            base_url=config.llm.base_url,
            api_key=config.llm.api_key,
        )
        self.embedding_client = OpenAI(
            base_url=config.embedding.base_url,
            api_key=config.embedding.api_key or config.llm.api_key,
        )

    def chat(self, messages: list, model: str = None, **kwargs) -> str:
        model = model or config.llm.chat_model
        try:
            response = self.chat_client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def clean(self, content: str) -> dict:
        try:
            response = self.chat_client.chat.completions.create(
                model=config.llm.clean_model,
                messages=[{"role": "user", "content": content}],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"清洗调用失败: {e}")
            raise

    def embed(self, texts: list) -> list:
        try:
            response = self.embedding_client.embeddings.create(
                model=config.embedding.embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Embedding调用失败: {e}")
            raise

llm_client = LLMClient()
```

**Step 4: Implement LLM cleaner**

Add to `src/processors/cleaner.py`:

```python
from src.generators.llm_client import llm_client
import json

class LLMCleaner:
    def __init__(self):
        self.llm_client = llm_client
        self.clean_prompt = """你是一个金融新闻清洗专家。请对以下新闻进行清洗和结构化：

新闻标题：{title}
新闻内容：{content}

任务：
1. 去除广告、重复信息，提取核心内容
2. 识别涉及的股票、公司、行业
3. 判断情感倾向（positive/negative/neutral）
4. 评估市场重要性（1-5分）
5. 自动打标签
6. 判断是否为垃圾信息

输出JSON格式：
{{
    "cleaned_content": "清洗后的核心内容",
    "entities": ["股票名", "公司名", "行业"],
    "sentiment": "positive/negative/neutral",
    "importance": 3,
    "tags": ["标签1", "标签2"],
    "is_trash": false
}}"""

    def clean(self, news_list: list, batch_size: int = 10) -> list:
        cleaned = []
        total = len(news_list)

        for i in range(0, total, batch_size):
            batch = news_list[i:i + batch_size]
            batch_results = self._clean_batch(batch)
            cleaned.extend(batch_results)
            logger.info(f"LLM清洗: {i + len(batch)}/{total}")

        return cleaned

    def _clean_batch(self, batch: list) -> list:
        results = []
        for item in batch:
            try:
                prompt = self.clean_prompt.format(
                    title=item.get('title', ''),
                    content=item.get('content', '')
                )
                response = self.llm_client.clean(prompt)
                parsed = json.loads(response)

                if not parsed.get('is_trash'):
                    results.append({
                        **item,
                        'cleaned_content': parsed.get('cleaned_content', item.get('content', '')),
                        'entities': parsed.get('entities', []),
                        'sentiment': parsed.get('sentiment', 'neutral'),
                        'importance': parsed.get('importance', 3),
                        'tags': parsed.get('tags', []),
                    })
            except Exception as e:
                logger.warning(f"单条清洗失败，保留原数据: {e}")
                results.append(item)

        return results
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_cleaner.py::test_llm_cleaner_extracts_entities -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/processors/cleaner.py src/generators/llm_client.py tests/unit/test_cleaner.py
git commit -m "feat: implement LLM-based cleaner"
```

---

## Phase 4: RAG模块

### Task 8: 实现向量存储

**Files:**
- Create: `src/rag/vector_store.py`
- Create: `tests/unit/test_vector_store.py`

**Step 1: Write the failing test**

Create `tests/unit/test_vector_store.py`:

```python
from src.rag.vector_store import VectorStore
import pytest

def test_vector_store_add_documents():
    store = VectorStore()
    docs = [
        {'id': '1', 'text': '测试文档1', 'metadata': {'source': 'test'}},
        {'id': '2', 'text': '测试文档2', 'metadata': {'source': 'test'}},
    ]
    store.add_documents(docs)
    assert store.count() >= 2

def test_vector_store_search():
    store = VectorStore()
    docs = [
        {'id': '1', 'text': '贵州茅台股价上涨', 'metadata': {'source': 'test'}},
    ]
    store.add_documents(docs)
    results = store.search('茅台', n_results=1)
    assert len(results) >= 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_vector_store.py -v`
Expected: FAIL

**Step 3: Implement vector store**

Create `src/rag/vector_store.py`:

```python
import chromadb
from chromadb.config import Settings
from loguru import logger
from config.settings import config
from typing import List, Dict, Optional

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(config.database.chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            return self.client.get_collection("financial_news")
        except:
            return self.client.create_collection(
                name="financial_news",
                metadata={"description": "Financial news for RAG"}
            )

    def add_documents(self, documents: List[Dict]) -> None:
        if not documents:
            return

        ids = [doc.get('id', str(hash(doc['text']))) for doc in documents]
        texts = [doc['text'] for doc in documents]
        metadatas = [doc.get('metadata', {}) for doc in documents]

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        logger.info(f"向量存储: 添加 {len(documents)} 条")

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else 0
                    })

            return documents
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    def count(self) -> int:
        return self.collection.count()

vector_store = VectorStore()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_vector_store.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/rag/vector_store.py tests/unit/test_vector_store.py
git commit -m "feat: implement Chroma vector store"
```

---

### Task 9: 实现嵌入生成器

**Files:**
- Create: `src/rag/embeddings.py`
- Create: `tests/unit/test_embeddings.py`

**Step 1: Write the failing test**

Create `tests/unit/test_embeddings.py`:

```python
from unittest.mock import Mock
from src.rag.embeddings import EmbeddingGenerator

def test_embedding_generator_generates_vectors(monkeypatch):
    mock_client = Mock()
    mock_client.embed.return_value = [[0.1] * 1536]

    from src.generators.llm_client import llm_client
    monkeypatch.setattr(llm_client, 'embed', mock_client.embed)

    generator = EmbeddingGenerator()
    texts = ["测试文本1", "测试文本2"]
    result = generator.generate(texts)

    assert len(result) == 2
    assert len(result[0]) == 1536
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_embeddings.py -v`
Expected: FAIL

**Step 3: Implement embedding generator**

Create `src/rag/embeddings.py`:

```python
from loguru import logger
from src.generators.llm_client import llm_client
from typing import List

class EmbeddingGenerator:
    def __init__(self):
        self.client = llm_client

    def generate(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        try:
            embeddings = self.client.embed(texts)
            logger.info(f"生成向量: {len(embeddings)} 条")
            return embeddings
        except Exception as e:
            logger.error(f"向量生成失败: {e}")
            raise

embedding_generator = EmbeddingGenerator()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_embeddings.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/rag/embeddings.py tests/unit/test_embeddings.py
git commit -m "feat: implement embedding generator"
```

---

### Task 10: 实现RAG检索器

**Files:**
- Create: `src/rag/retriever.py`
- Create: `tests/unit/test_retriever.py`

**Step 1: Write the failing test**

Create `tests/unit/test_retriever.py`:

```python
from src.rag.retriever import RAGRetriever

def test_rag_retriever_retrieves_context():
    retriever = RAGRetriever()
    context = retriever.retrieve("贵州茅台股价")
    assert isinstance(context, str)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_retriever.py -v`
Expected: FAIL

**Step 3: Implement RAG retriever**

Create `src/rag/retriever.py`:

```python
from loguru import logger
from src.rag.vector_store import vector_store
from typing import List, Dict

class RAGRetriever:
    def __init__(self):
        self.vector_store = vector_store

    def retrieve(self, query: str, n_results: int = 5) -> str:
        results = self.vector_store.search(query, n_results)

        if not results:
            return "无相关历史信息"

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[参考{i}] {result['text']}"
            )

        context = "\n\n".join(context_parts)
        logger.info(f"RAG检索: 查询'{query}'，返回 {len(results)} 条")
        return context

    def retrieve_by_entity(self, entity: str, n_results: int = 3) -> List[Dict]:
        results = self.vector_store.search(entity, n_results)
        return results

rag_retriever = RAGRetriever()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_retriever.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/rag/retriever.py tests/unit/test_retriever.py
git commit -m "feat: implement RAG retriever"
```

---

## Phase 5: 报告生成模块

### Task 11: 实现日报生成器

**Files:**
- Create: `src/generators/report_gen.py`
- Create: `config/prompts.py`
- Create: `tests/unit/test_report_gen.py`

**Step 1: Write the failing test**

Create `tests/unit/test_report_gen.py`:

```python
from unittest.mock import Mock
from src.generators.report_gen import ReportGenerator

def test_report_generator_generates_markdown():
    mock_client = Mock()
    mock_client.chat.return_value = """# 测试日报

## 1. 市场概览
测试内容
"""

    from src.generators.llm_client import llm_client
    import src.generators.report_gen as report_gen_module
    original_client = report_gen_module.llm_client
    report_gen_module.llm_client = mock_client

    try:
        generator = ReportGenerator()
        news_data = []
        market_data = {}
        context = ""
        result = generator.generate(news_data, market_data, context)

        assert isinstance(result, str)
        assert "市场概览" in result
    finally:
        report_gen_module.llm_client = original_client
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_report_gen.py -v`
Expected: FAIL

**Step 3: Create prompts**

Create `config/prompts.py`:

```python
DAILY_REPORT_PROMPT = """你是一位专业的金融分析师，负责生成每日财经日报。

## 输入数据
1. 今日新闻：
{news_data}

2. 市场数据：
{market_data}

3. 历史参考：
{historical_context}

## 输出要求
请生成一份结构化的Markdown日报，包含以下8大板块：

### 1. 市场概览
- 主要指数表现（上证/深证/创业板）
- 市场整体情绪判断
- 成交量概况

### 2. 资金动向
- 北向资金流向
- 主力资金净流入前5板块
- 资金流向趋势分析

### 3. 个股聚焦
- 涨幅榜前5分析
- 跌幅榜前5分析
- 龙虎榜重点个股

### 4. 行业分析
- 今日领涨板块及原因
- 今日领跌板块及原因
- 板块轮动迹象

### 5. 政策解读
- 重要政策要点
- 政策影响分析
- 受益板块/个股

### 6. 外围市场
- 美股/港股表现
- 全球宏观经济动态
- 国际重要事件

### 7. 策略参考
- 基于当前市场的操作建议
- 关注板块/个股
- 风险收益比评估

### 8. 风险提示
- 短期风险因素
- 需要警惕的信号
- 止损/仓位建议

## 输出格式
- 使用Markdown格式
- 每个板块用二级标题(##)分隔
- 关键数据用表格呈现
- 分析要客观，有数据支撑
- 风险提示要明确

请开始生成："""
```

**Step 4: Implement report generator**

Create `src/generators/report_gen.py`:

```python
from loguru import logger
from src.generators.llm_client import llm_client
from config.prompts import DAILY_REPORT_PROMPT
from datetime import datetime
from typing import List, Dict

class ReportGenerator:
    def __init__(self):
        self.client = llm_client

    def generate(self, news_data: List[Dict], market_data: Dict, context: str) -> str:
        news_summary = self._format_news(news_data)
        market_summary = self._format_market(market_data)

        prompt = DAILY_REPORT_PROMPT.format(
            news_data=news_summary,
            market_data=market_summary,
            historical_context=context
        )

        try:
            report = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            logger.success("日报生成完成")
            return report
        except Exception as e:
            logger.error(f"日报生成失败: {e}")
            raise

    def _format_news(self, news_data: List[Dict]) -> str:
        if not news_data:
            return "暂无新闻数据"

        formatted = []
        for item in news_data[:20]:  # 限制数量
            formatted.append(f"- {item.get('title', '')}: {item.get('cleaned_content', item.get('content', ''))[:100]}")

        return "\n".join(formatted)

    def _format_market(self, market_data: Dict) -> str:
        if not market_data:
            return "暂无市场数据"

        formatted = []

        if market_data.get('industry_flow'):
            formatted.append("行业资金流:")
            for item in market_data['industry_flow'][:5]:
                formatted.append(f"  - {item}")

        if market_data.get('main_flow'):
            formatted.append("主力资金流:")
            for item in market_data['main_flow'][:5]:
                formatted.append(f"  - {item}")

        return "\n".join(formatted)

report_generator = ReportGenerator()
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_report_gen.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/generators/report_gen.py config/prompts.py tests/unit/test_report_gen.py
git commit -m "feat: implement daily report generator"
```

---

## Phase 6: 存储模块

### Task 12: 实现SQLite存储

**Files:**
- Create: `src/storage/database.py`
- Create: `tests/unit/test_database.py`

**Step 1: Write the failing test**

Create `tests/unit/test_database.py`:

```python
import tempfile
from pathlib import Path
from src.storage.database import Database

def test_database_creates_tables():
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
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)

        news = {'title': '测试', 'content': '内容', 'source': 'test'}
        db.save_news([news])

        count = db.get_news_count()
        assert count >= 1
        db.close()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_database.py -v`
Expected: FAIL

**Step 3: Implement database**

Create `src/storage/database.py`:

```python
import sqlite3
from pathlib import Path
from loguru import logger
from typing import List, Dict
from datetime import datetime
import json

class Database:
    def __init__(self, db_path: Path = None):
        from config.settings import config
        self.db_path = db_path or config.database.sqlite_path
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_tables()

    def _create_tables(self):
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

    def save_news(self, news_list: List[Dict]):
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
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reports (report_date, report_type, content)
            VALUES (?, ?, ?)
        """, (report_date, report_type, content))
        self.conn.commit()
        logger.info(f"保存日报: {report_date} - {report_type}")

    def get_news_count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM news")
        return cursor.fetchone()[0]

    def close(self):
        self.conn.close()

database = Database()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_database.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/storage/database.py tests/unit/test_database.py
git commit -m "feat: implement SQLite database storage"
```

---

## Phase 7: 定时调度与主流程

### Task 13: 实现定时调度器

**Files:**
- Create: `src/scheduler/cron_scheduler.py`
- Create: `tests/unit/test_scheduler.py`

**Step 1: Write the failing test**

Create `tests/unit/test_scheduler.py`:

```python
from unittest.mock import Mock, patch
from src.scheduler.cron_scheduler import ReportScheduler

def test_scheduler_initializes():
    scheduler = ReportScheduler()
    assert scheduler.scheduler is not None

def test_scheduler_has_jobs():
    scheduler = ReportScheduler()
    jobs = scheduler.scheduler.get_jobs()
    assert len(jobs) == 3
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_scheduler.py -v`
Expected: FAIL

**Step 3: Implement scheduler**

Create `src/scheduler/cron_scheduler.py`:

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from config.settings import config
from datetime import datetime

class ReportScheduler:
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        self.scheduler.add_job(
            self._pre_market_task,
            trigger=CronTrigger(hour=8, minute=30),
            id="pre_market",
            name="开盘前日报"
        )

        self.scheduler.add_job(
            self._mid_close_task,
            trigger=CronTrigger(hour=11, minute=30),
            id="mid_close",
            name="午间日报"
        )

        self.scheduler.add_job(
            self._after_close_task,
            trigger=CronTrigger(hour=15, minute=30),
            id="after_close",
            name="收盘日报"
        )

        logger.info("定时任务配置完成")

    def _pre_market_task(self):
        logger.info(f"[{datetime.now()}] 执行开盘前任务")
        # TODO: 调用主流程

    def _mid_close_task(self):
        logger.info(f"[{datetime.now()}] 执行中午收盘任务")
        # TODO: 调用主流程

    def _after_close_task(self):
        logger.info(f"[{datetime.now()}] 执行晚间收盘任务")
        # TODO: 调用主流程

    def start(self):
        logger.info("调度器启动，等待定时任务...")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("调度器停止")

    def run_now(self, task_type: str = "after_close"):
        task_map = {
            "pre_market": self._pre_market_task,
            "mid_close": self._mid_close_task,
            "after_close": self._after_close_task,
        }
        if task_type in task_map:
            task_map[task_type]()
        else:
            logger.error(f"未知任务类型: {task_type}")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_scheduler.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/scheduler/cron_scheduler.py tests/unit/test_scheduler.py
git commit -m "feat: implement cron scheduler"
```

---

### Task 14: 实现主流程

**Files:**
- Modify: `src/main.py`
- Create: `tests/integration/test_full_pipeline.py`

**Step 1: Write the failing test**

Create `tests/integration/test_full_pipeline.py`:

```python
from src.main import generate_daily_report

def test_full_pipeline_generates_report():
    result = generate_daily_report("test")
    assert isinstance(result, str)
    assert len(result) > 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_full_pipeline.py -v`
Expected: FAIL

**Step 3: Implement main flow**

Create `src/main.py`:

```python
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

def generate_daily_report(report_type: str = "after_close") -> str:
    """生成日报主流程"""
    logger.info(f"开始生成日报: {report_type}")

    # 1. 数据采集
    logger.info("=== 步骤1: 数据采集 ===")
    news_collector = NewsCollector()
    market_collector = MarketCollector()

    news_data = news_collector.collect()
    market_data = market_collector.collect()

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
    database.save_news(news_data)

    # 5. 向量化并存储到Chroma
    logger.info("=== 步骤5: 向量化存储 ===")
    docs = []
    for item in news_data:
        docs.append({
            'id': f"{datetime.now().timestamp()}_{hash(item['title'])}",
            'text': f"{item['title']}\n{item.get('cleaned_content', item['content'])}",
            'metadata': {'source': item['source'], 'time': item['time']}
        })

    try:
        vector_store.add_documents(docs)
    except Exception as e:
        logger.warning(f"向量存储失败: {e}")

    # 6. RAG检索相关历史
    logger.info("=== 步骤6: RAG检索 ===")
    context = ""
    try:
        # 根据今日新闻关键词检索
        if news_data:
            context = rag_retriever.retrieve(news_data[0]['title'])
    except Exception as e:
        logger.warning(f"RAG检索失败: {e}")

    # 7. 生成日报
    logger.info("=== 步骤7: 生成日报 ===")
    report = report_generator.generate(news_data, market_data, context)

    # 8. 保存日报
    logger.info("=== 步骤8: 保存日报 ===")
    report_date = datetime.now().strftime("%Y-%m-%d")
    database.save_report(report_date, report_type, report)

    # 保存到文件
    output_file = config.output_dir / f"{report_date}_{report_type}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.success(f"日报已保存: {output_file}")

    return report

def main():
    """主入口"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # 立即运行一次
        report_type = sys.argv[2] if len(sys.argv) > 2 else "after_close"
        generate_daily_report(report_type)
    else:
        # 启动定时调度
        from src.scheduler.cron_scheduler import ReportScheduler
        scheduler = ReportScheduler()
        scheduler.start()

if __name__ == "__main__":
    main()
```

**Step 4: Update scheduler to call main flow**

Modify `src/scheduler/cron_scheduler.py`:

```python
from src.main import generate_daily_report

def _pre_market_task(self):
    logger.info(f"[{datetime.now()}] 执行开盘前任务")
    generate_daily_report("pre_market")

def _mid_close_task(self):
    logger.info(f"[{datetime.now()}] 执行中午收盘任务")
    generate_daily_report("mid_close")

def _after_close_task(self):
    logger.info(f"[{datetime.now()}] 执行晚间收盘任务")
    generate_daily_report("after_close")
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_full_pipeline.py -v -s`
Expected: PASS (需要API配置)

**Step 6: Commit**

```bash
git add src/main.py src/scheduler/cron_scheduler.py tests/integration/test_full_pipeline.py
git commit -m "feat: implement main generation pipeline"
```

---

## Phase 8: 收尾与文档

### Task 15: 完善异常处理

**Files:**
- Create: `src/utils/exceptions.py`
- Create: `src/utils/retry.py`
- Modify: `src/main.py`

**Step 1: Create exceptions**

Create `src/utils/exceptions.py`:

```python
class FinancialReportError(Exception):
    """基础异常类"""
    pass

class DataCollectionError(FinancialReportError):
    """数据采集异常"""
    pass

class DataCleaningError(FinancialReportError):
    """数据清洗异常"""
    pass

class LLMError(FinancialReportError):
    """LLM调用异常"""
    pass

class EmbeddingError(FinancialReportError):
    """向量嵌入异常"""
    pass

class StorageError(FinancialReportError):
    """存储异常"""
    pass

class ReportGenerationError(FinancialReportError):
    """报告生成异常"""
    pass
```

**Step 2: Create retry decorator**

Create `src/utils/retry.py`:

```python
from functools import wraps
import time
from loguru import logger

def retry_on_failure(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
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

                    logger.warning(f"{func.__name__} 失败 ({retries}/{max_retries}): {e}, {current_delay}秒后重试...")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator
```

**Step 3: Update main with error handling**

Modify `src/main.py`:

```python
from src.utils.exceptions import *
from src.utils.retry import retry_on_failure

@retry_on_failure(max_retries=3, delay=2, exceptions=(DataCollectionError,))
def collect_with_retry(collector):
    return collector.collect()

def generate_daily_report(report_type: str = "after_close") -> str:
    try:
        # ... 现有代码 ...
    except DataCollectionError as e:
        logger.error(f"数据采集失败: {e}")
        raise ReportGenerationError("数据采集失败") from e
    except LLMError as e:
        logger.error(f"LLM调用失败: {e}")
        raise ReportGenerationError("日报生成失败") from e
    except Exception as e:
        logger.critical(f"未预期错误: {e}")
        raise
```

**Step 4: Commit**

```bash
git add src/utils/exceptions.py src/utils/retry.py src/main.py
git commit -m "feat: add exception handling and retry logic"
```

---

### Task 16: 更新文档并测试完整流程

**Files:**
- Modify: `README.md`
- Create: `docs/usage.md`

**Step 1: Update README**

Update `README.md` with complete usage instructions:

```markdown
# 金融日报机器人

基于LLM和RAG技术的智能金融日报生成系统。

## 功能特性

- 自动定时采集财经新闻和市场数据
- LLM智能清洗和分析数据
- RAG技术增强内容关联
- 生成结构化Markdown日报

## 安装

\`\`\`bash
# 使用uv安装依赖
uv sync

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入API密钥
\`\`\`

## 配置

编辑 `.env` 文件：

\`\`\`bash
# LLM API配置
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_api_key

# Embedding API配置
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=

# 模型选择
CHAT_MODEL=gpt-4o
CLEAN_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
\`\`\`

## 使用

### 立即生成日报

\`\`\`bash
# 生成收盘日报
uv run python src/main.py run

# 生成开盘前日报
uv run python src/main.py run pre_market

# 生成午间日报
uv run python src/main.py run mid_close
\`\`\`

### 启动定时任务

\`\`\`bash
uv run python src/main.py
\`\`\`

定时任务会在以下时间自动执行：
- 开盘前 8:30
- 中午收盘 11:30
- 晚间收盘 15:30

## 输出

日报保存在 `outputs/` 目录，格式为 `YYYY-MM-DD_{type}.md`

## 测试

\`\`\`bash
# 运行所有测试
uv run pytest

# 运行单元测试
uv run pytest tests/unit/

# 运行集成测试
uv run pytest tests/integration/
\`\`\`
```

**Step 2: Create usage guide**

Create `docs/usage.md`:

```markdown
# 使用指南

## 首次运行

1. 配置 `.env` 文件
2. 运行 `uv run python src/main.py run after_close` 测试
3. 确认输出文件生成正常

## 定时运行

直接运行 `uv run python src/main.py` 启动定时调度。

## 更换LLM服务商

只需修改 `.env` 中的 `BASE_URL` 和 `API_KEY`，无需修改代码。

支持的兼容接口：
- OpenAI
- DeepSeek
- Moonshot
- 本地部署（如Ollama）
```

**Step 3: Run full integration test**

Run: `uv run pytest tests/ -v`
Expected: 所有测试通过

**Step 4: Final commit**

```bash
git add README.md docs/usage.md
git commit -m "docs: update README and usage guide"
```

---

## 实施完成检查清单

- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 能生成完整日报
- [ ] 定时任务正常工作
- [ ] 日志正常记录
- [ ] 向量库正常存储
- [ ] 错误处理正常工作
- [ ] 文档完整

---

**计划完成！** 保存到 `docs/plans/2026-03-11-financial-daily-report-implementation.md`
