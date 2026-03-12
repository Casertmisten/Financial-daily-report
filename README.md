# 金融日报机器人

基于LLM和RAG技术的智能金融日报生成系统。

## 功能特性

- 自动定时采集财经新闻和市场数据
- LLM智能清洗和分析数据
- RAG技术增强内容关联
- 生成结构化Markdown日报

## 项目结构

```
financial-daily-report/
├── src/                    # 源代码目录
│   ├── main.py            # 主程序入口
│   ├── collectors/        # 数据采集模块
│   ├── processors/        # 数据清洗模块
│   ├── generators/        # LLM和日报生成模块
│   ├── rag/               # RAG检索模块
│   ├── storage/           # 数据存储模块
│   ├── scheduler/         # 定时调度模块
│   └── utils/             # 工具模块
├── config/                # 配置文件目录
├── data/                  # 数据存储目录
├── outputs/               # 生成报告输出目录
├── docs/                  # 文档目录
├── tests/                 # 测试目录
├── pyproject.toml         # 项目配置文件
├── .env.example          # 环境变量示例
└── README.md             # 项目说明
```

## 前置要求

- Python 3.10 或更高版本
- uv 包管理器（推荐）

### 安装 uv

```bash
# macOS / Linux / WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

## 快速开始

```bash
# 1. 克隆项目（如果适用）
git clone <repository-url>
cd Financial-daily-report

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的API密钥和配置

# 4. 立即生成日报测试
uv run python src/main.py run

# 5. 启动定时调度
uv run python src/main.py
```

## 配置说明

项目使用 `.env` 文件进行配置，主要配置项包括：

### LLM 配置
- `LLM_BASE_URL`: LLM服务的基础URL（支持OpenAI兼容接口）
- `LLM_API_KEY`: LLM服务的API密钥（必填）
- `CHAT_MODEL`: 用于对话和生成的模型名称
- `CLEAN_MODEL`: 用于数据清洗的模型名称

### Embedding 配置
- `EMBEDDING_BASE_URL`: Embedding服务的基础URL
- `EMBEDDING_API_KEY`: Embedding服务的API密钥（可选）
- `EMBEDDING_MODEL`: 用于向量嵌入的模型名称

### 定时任务配置
- `PRE_MARKET_TIME`: 开盘前报告生成时间（格式：HH:MM）
- `MID_CLOSE_TIME`: 中午收盘报告生成时间（格式：HH:MM）
- `AFTER_CLOSE_TIME`: 晚间收盘报告生成时间（格式：HH:MM）

### 日志配置
- `LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）

## 使用方法

### 立即生成日报

```bash
# 生成收盘日报
uv run python src/main.py run

# 生成开盘前日报
uv run python src/main.py run pre_market

# 生成午间日报
uv run python src/main.py run mid_close
```

### 启动定时任务

```bash
uv run python src/main.py
```

定时任务会在以下时间自动执行：
- 开盘前 8:30
- 中午收盘 11:30
- 晚间收盘 15:30

## 输出

日报保存在 `outputs/` 目录，格式为 `YYYY-MM-DD_{type}.md`

## 测试

```bash
# 运行所有测试
uv run pytest

# 运行单元测试
uv run pytest tests/unit/

# 运行集成测试
uv run pytest tests/integration/

# 运行特定测试
uv run pytest tests/unit/test_embeddings.py -v
```

## 架构说明

系统采用模块化架构，主要包含以下模块：

1. **数据采集模块** (`src/collectors/`)
   - 新闻采集器：从多个财经网站采集新闻
   - 市场数据采集器：采集股市行情和资金流向数据

2. **数据清洗模块** (`src/processors/`)
   - 规则清洗器：基于规则的文本清洗和去重
   - LLM清洗器：使用LLM进行智能清洗和实体提取

3. **RAG模块** (`src/rag/`)
   - 向量存储：基于ChromaDB的文档向量存储
   - 嵌入生成器：将文本转换为向量
   - RAG检索器：检索相关历史文档作为上下文

4. **报告生成模块** (`src/generators/`)
   - LLM客户端：统一的LLM调用接口
   - 日报生成器：生成结构化的金融日报

5. **存储模块** (`src/storage/`)
   - 数据库：SQLite数据库存储新闻和报告

6. **调度模块** (`src/scheduler/`)
   - 定时调度器：基于APScheduler的定时任务

## 开发

```bash
# 添加新依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>
```

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
