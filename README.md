# 金融日报机器人

基于LLM和RAG技术的智能金融日报生成系统。

## 功能特性

- 自动定时采集财经新闻和市场数据
- LLM智能清洗和分析数据
- RAG技术增强内容关联
- 生成结构化Markdown日报

## 快速开始

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入API密钥

# 运行
uv run python src/main.py
```

## 定时任务

- 开盘前 8:30：财经早餐
- 中午收盘 11:30：午间快讯
- 晚间收盘 15:30：收盘总结
