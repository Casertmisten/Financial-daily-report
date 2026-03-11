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
│   ├── collector/         # 数据采集模块
│   ├── cleaner/           # 数据清洗模块
│   ├── generator/         # 日报生成模块
│   └── scheduler/         # 定时调度模块
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

# 4. 运行程序
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

## 定时任务

系统会在以下时间自动生成并发布报告：

- **开盘前 8:30**：财经早餐
  - 盘前要闻回顾
  - 重要公告汇总
  - 市场预期分析

- **中午收盘 11:30**：午间快讯
  - 上午市场动态
  - 热点板块追踪
  - 资金流向分析

- **晚间收盘 15:30**：收盘总结
  - 全日市场综述
  - 涨跌停统计
  - 后市展望

## 开发

```bash
# 运行测试
uv run pytest

# 添加新依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>
```

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
