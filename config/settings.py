from dataclasses import dataclass, field
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
    api_type: str = "openai"  # "openai" 或 "ollama"

@dataclass
class ScheduleConfig:
    pre_market: str = "08:30"
    mid_close: str = "11:30"
    after_close: str = "15:30"

@dataclass
class DatabaseConfig:
    sqlite_path: Path = field(default_factory=lambda: Path("data/financial.db"))
    chroma_path: Path = field(default_factory=lambda: Path("data/chroma_db"))

@dataclass
class NewsSourceConfig:
    sources: List[str] = field(default_factory=list)
    enabled_sources: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.sources:
            self.sources = [
                "cjzc_em", "global_em", "global_sina",
                "global_futu", "global_ths", "global_cls",
            ]
        if not self.enabled_sources:
            self.enabled_sources = self.sources

@dataclass
class Config:
    llm: LLMConfig
    embedding: EmbeddingConfig
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    news: NewsSourceConfig = field(default_factory=NewsSourceConfig)

    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    log_dir: Path = field(default_factory=lambda: Path("data/logs"))

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
        api_type=os.getenv("EMBEDDING_API_TYPE", "openai"),  # "openai" 或 "ollama"
    )
)
