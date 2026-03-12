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

## 常见问题

### Q: 如何测试系统是否正常工作？
A: 运行 `uv run pytest` 检查所有测试是否通过。

### Q: 报告生成失败怎么办？
A: 检查 `.env` 配置是否正确，查看日志文件 `data/logs/` 获取详细错误信息。

### Q: 如何修改报告生成时间？
A: 修改 `.env` 文件中的定时任务配置项。
