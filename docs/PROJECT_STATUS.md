# Project Status

本文件是当前项目状态的唯一收口清单，用于持续对齐 `DEVELOPMENT_GUIDE.md`、README、测试和交付边界。

## 已完成

- 文件上传：`POST /api/files/upload`
- 字段画像查询：`GET /api/files/{file_id}/profile`
- 分析任务创建：`POST /api/analysis/start`
- 分析任务执行：`POST /api/analysis/{task_id}/run`
- 任务状态查询：`GET /api/analysis/{task_id}`
- 事件时间线查询：`GET /api/analysis/{task_id}/events`
- 规则评估重算：`POST /api/eval/run`
- SQLite 持久化：`files`、`analysis_tasks`、`analysis_events`、`tool_call_logs`、`eval_results`
- DuckDB 真实聚合工具：按品类、地区、渠道执行聚合分析
- MockLLM 目标/计划生成
- JSONL 关键词业务语义检索
- LangGraph 最小线性状态流
- Observability 事件收口：`backend/app/observability`
- 固定回归评测：3 个真实支持 case
- Windows 一键演示脚本：`scripts/demo_mvp.ps1`

## 当前真实 MVP 边界

当前可以真实声称已实现：

- CSV 上传与画像
- 结构化问题到工具执行的完整分析闭环
- 业务语义增强但非向量化的轻量 RAG
- 任务状态与事件时间线回放
- 规则评分与固定 case 回归验证

当前不能声称已实现：

- 异步队列执行
- 真实外部 LLM Provider
- embedding / BM25 / rerank
- DockerSandbox
- LLM-as-Judge
- 完整 React 前端

## 待收口项

- 保持 README、演示脚本、测试和文档边界持续一致
- 如果要宣称“项目完成”，必须先按 `DEVELOPMENT_GUIDE.md` 做逐项完成度审计并保留验证证据

## 第二阶段规划

- 接入真实 LLM Provider
- 升级为 embedding / BM25 / rerank 检索
- 增加更完整的 Redis 会话记忆与异步任务执行
- 引入 DockerSandbox
- 引入 LLM-as-Judge
- 补完整前端体验
