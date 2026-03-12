# 金融日报机器人设计文档

**项目名称**：Financial Daily Report
**创建日期**：2026-03-11
**设计目标**：基于LLM和RAG技术的智能金融日报生成系统

---

## 1. 系统概述

### 1.1 功能描述
自动定时采集财经新闻和市场数据，通过LLM清洗分析，结合RAG技术生成结构化的每日金融日报。

### 1.2 目标用户
个人投资参考，用于获取每日市场动态和投资决策支持。

### 1.3 定时执行
- **开盘前 8:30**：财经早餐 + 全球财经快讯
- **中午收盘 11:30**：上午行情回顾 + 午间快讯
- **晚间收盘 15:30**：全日总结 + 盘后分析

---

## 2. 系统架构

```
定时触发器 (8:30 / 11:30 / 15:30)
         │
         ▼
   数据采集模块
   ├─ 新闻采集（6个源）
   └─ 市场数据采集（5个接口）
         │
         ▼
   数据清洗模块 (LLM + 规则)
   ├─ 规则清洗（去重/格式化）
   └─ LLM智能清洗（提取/分类/评分）
         │
         ▼
   RAG增强模块
   ├─ 向量嵌入（OpenAI API）
   └─ 向量检索（Chroma）
         │
         ▼
   LLM生成模块
   └─ 结构化日报生成（Markdown）
         │
         ▼
   保存输出
   ├─ SQLite（元数据）
   └─ outputs/（Markdown文件）
```

---

## 3. 数据源

### 3.1 新闻源（AKShare接口）

| 接口函数 | 数据源 | 说明 |
|---------|--------|------|
| `stock_info_cjzc_em` | 东财财富 | 财经早餐 |
| `stock_info_global_em` | 东财财富 | 全球财经快讯 |
| `stock_info_global_sina` | 新浪财经 | 全球财经快讯 |
| `stock_info_global_futu` | 富途牛牛 | 快讯 |
| `stock_info_global_ths` | 同花顺财经 | 全球财经直播 |
| `stock_info_global_cls` | 财联社 | 电报 |

### 3.2 市场数据接口（AKShare）

| 接口函数 | 数据类型 |
|---------|---------|
| `stock_zh_a_spot_em` | 沪深京A股实时行情 |
| `stock_fund_flow_industry` | 行业资金流 |
| `stock_fund_flow_concept` | 概念资金流 |
| `stock_main_fund_flow` | 主力资金流排名 |
| `stock_lhb_detail_em` | 龙虎榜数据 |

---

## 4. 项目结构

```
Financial-daily-report/
├── pyproject.toml              # uv项目配置
├── README.md                   # 项目说明
├── .env.example                # 环境变量模板
├── .env                        # 环境变量（不提交）
│
├── config/
│   ├── __init__.py
│   ├── settings.py             # 配置管理
│   └── prompts.py              # LLM提示词模板
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # 主入口
│   │
│   ├── collectors/             # 数据采集模块
│   │   ├── __init__.py
│   │   ├── news_collector.py   # 新闻采集
│   │   └── market_collector.py # 行情数据采集
│   │
│   ├── processors/             # 数据处理模块
│   │   ├── __init__.py
│   │   ├── cleaner.py          # 数据清洗（LLM+规则）
│   │   └── analyzer.py         # 数据分析
│   │
│   ├── rag/                    # RAG增强模块
│   │   ├── __init__.py
│   │   ├── embeddings.py       # 向量嵌入
│   │   └── vector_store.py     # Chroma向量库
│   │
│   ├── generators/             # 报告生成模块
│   │   ├── __init__.py
│   │   ├── llm_client.py       # LLM客户端
│   │   └── report_gen.py       # 日报生成器
│   │
│   ├── storage/                # SQLite存储模块
│   │   ├── __init__.py
│   │   └── database.py         # 数据库操作
│   │
│   ├── scheduler/              # 定时任务模块
│   │   ├── __init__.py
│   │   └── cron_scheduler.py   # APScheduler
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── logger.py           # 日志配置
│       ├── exceptions.py       # 异常定义
│       └── retry.py            # 重试装饰器
│
├── data/
│   ├── financial.db            # SQLite数据库
│   ├── chroma_db/              # Chroma向量数据库
│   └── logs/                   # 日志文件
│
├── outputs/                    # 日报Markdown输出
│
└── tests/                      # 测试
    ├── unit/                   # 单元测试
    └── integration/            # 集成测试
```

---

## 5. 核心模块设计

### 5.1 数据清洗（LLM + 规则）

**第1层：规则清洗**
- 去除HTML标签、广告
- 时间格式标准化
- 重复内容检测

**第2层：LLM智能清洗**
- 提取核心信息
- 识别关键实体（股票/公司/行业）
- 情感倾向判断
- 重要性评分（1-5分）
- 自动分类标签

### 5.2 LLM客户端（双配置）

```python
# 生成模型配置
LLMConfig:
  - base_url: LLM服务地址
  - api_key: API密钥
  - chat_model: 主模型（如 gpt-4o）
  - clean_model: 清洗模型（如 gpt-4o-mini）

# 嵌入模型配置
EmbeddingConfig:
  - base_url: Embedding服务地址
  - api_key: API密钥（可留空使用LLM的）
  - embedding_model: 嵌入模型
```

### 5.3 存储架构

| 存储 | 用途 |
|------|------|
| SQLite | 新闻元数据、市场数据、生成的日报 |
| Chroma | 向量嵌入存储和检索 |

---

## 6. 日报输出格式

### 8大板块结构

```markdown
# 每日金融日报 - YYYY-MM-DD

## 1. 市场概览
- 主要指数表现
- 市场整体情绪
- 成交量概况

## 2. 资金动向
- 北向资金流向
- 主力资金净流入前5板块
- 资金流向趋势分析

## 3. 个股聚焦
- 涨幅榜前5分析
- 跌幅榜前5分析
- 龙虎榜重点个股

## 4. 行业分析
- 今日领涨板块及原因
- 今日领跌板块及原因
- 板块轮动迹象

## 5. 政策解读
- 重要政策要点
- 政策影响分析
- 受益板块/个股

## 6. 外围市场
- 美股/港股表现
- 全球宏观经济动态
- 国际重要事件

## 7. 策略参考
- 基于当前市场的操作建议
- 关注板块/个股
- 风险收益比评估

## 8. 风险提示
- 短期风险因素
- 需要警惕的信号
- 止损/仓位建议
```

---

## 7. 依赖库

| 库 | 用途 |
|---|------|
| `akshare` | 金融数据接口 |
| `openai` | LLM + Embeddings（API兼容） |
| `chromadb` | 向量数据库 |
| `apscheduler` | 定时任务 |
| `python-dotenv` | 环境变量 |
| `loguru` | 日志管理 |

---

## 8. 错误处理策略

| 错误类型 | 处理策略 | 降级方案 |
|---------|---------|---------|
| 网络超时 | 重试3次，指数退避 | 使用缓存数据 |
| API限流 | 延迟重试 | 切换备用API |
| 数据采集失败 | 记录错误，跳过该源 | 使用其他数据源 |
| LLM调用失败 | 重试后使用备用模型 | 使用简化模板 |
| 向量嵌入失败 | 跳过向量化 | 无RAG直接生成 |
| 存储失败 | 重试后记录日志 | 仅输出文件 |

---

## 9. 配置文件

### .env.example

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

---

## 10. 测试策略

- **单元测试**：各模块独立功能测试
- **集成测试**：完整流程测试
- **Mock数据**：避免实际API调用

---

*文档版本：1.0*
*最后更新：2026-03-11*
