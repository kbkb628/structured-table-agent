# API Reference

本文档描述当前仓库已经真实实现的后端接口，接口边界与 `DEVELOPMENT_GUIDE.md`、测试和简历表达保持一致。

## 1. 上传文件

### `POST /api/files/upload`

用途：

- 上传 CSV 文件
- 上传 Excel 文件
- 生成字段画像
- 持久化文件元数据到 SQLite

请求：

- `multipart/form-data`
- 字段：`file`

当前限制：

- 支持 `.csv`、`.xlsx`、`.xls`
- Excel 上传后会先标准化为 CSV，再复用现有画像与分析链路
- 空文件会返回 `400`

响应字段：

- `file_id`
- `filename`
- `row_count`
- `column_count`
- `columns`
- `created_at`

## 2. 查询字段画像

### `GET /api/files/{file_id}/profile`

用途：

- 读取已经持久化的字段画像

失败：

- 文件不存在时返回 `404`

## 3. 创建分析任务

### `POST /api/analysis/start`

用途：

- 基于上传文件创建分析任务
- 运行轻量 JSONL 业务检索
- 使用当前配置的 `LLMClient` 生成 `analysis_goal` 和 `analysis_plan`
- 写入任务启动事件时间线

请求体：

```json
{
  "file_id": "file_xxx",
  "question": "analyse sales by region"
}
```

响应字段：

- `task_id`
- `status`
- `analysis_goal`
- `analysis_plan`

失败：

- 文件不存在时返回 `404`
- `LLM_PROVIDER=qwen` 但没有可用 key 时返回 `503`
- 外部 provider 调用失败时返回 `502`

## 4. 执行分析任务

### `POST /api/analysis/{task_id}/run`

用途：

- 执行带显式 `route_next_step` 的 LangGraph 最小状态流
- 完成字段匹配、DuckDB 聚合、图表生成、报告生成和规则评分
- 对多指标问题显式决定是否继续执行下一轮工具

当前图结构：

1. `load_task`
2. `match_fields`
3. `execute_tools`
4. `validate_tool_result`
5. `route_next_step`
6. `generate_charts`
7. `generate_report`
8. `evaluate_report`

当前最小动态行为：

- `match_fields` 可以为单个问题解析出多个待执行 metric
- `match_fields` 会把本轮 `planned_tool_calls` 写入状态
- `execute_tools` 每次只执行一个 metric 的真实工具调用
- `validate_tool_result` 会显式校验工具结果是否成功且非空
- `route_next_step` 会根据 `pending_metrics` 决定继续进入 `execute_tools`，还是结束工具阶段进入图表生成
- 运行入口会为同一 `task_id` 获取 `task_lock`，避免重复并发执行同一任务

响应为完整任务状态，包含：

- `field_understanding`
- `tool_results`
- `chart_specs`
- `draft_report`
- `final_report`
- `eval_result`
- `events`
- `errors`

额外失败场景：

- 任务不存在时返回 `404`
- 同一任务在执行中再次调用 `/run` 时返回 `409`

## 5. 查询任务状态

### `GET /api/analysis/{task_id}`

用途：

- 读取完整任务状态
- 回填当前任务事件列表
- 返回 `pending_metrics`、`pending_tool_calls`、`context_checkpoint` 和 `tool_call_logs`

失败：

- 任务不存在时返回 `404`

## 6. 查询事件时间线

### `GET /api/analysis/{task_id}/events`

用途：

- 查询当前任务的持久化事件时间线

当前事件来源：

- `backend/app/observability/event_logger.py`
- SQLite 表：`analysis_events`

典型事件类型：

- `task_created`
- `rag_retrieved`
- `goal_understood`
- `plan_generated`
- `fields_matched`
- `tool_called`
- `tool_succeeded`
- `tool_failed`
- `chart_generated`
- `chart_failed`
- `report_generated`
- `eval_finished`
- `task_completed`
- `task_failed`
- `context_checkpoint_refreshed`
- `session_store_warning`
- `session_state_recovered`

## 7. 查询工具调用日志

### `GET /api/analysis/{task_id}/tool-logs`

用途：

- 查询当前任务持久化到 SQLite 的工具调用日志
- 返回每次工具调用的请求 JSON、响应 JSON、成功状态与耗时

失败：

- 任务不存在时返回 `404`

## 8. 手动重跑单任务评估

### `POST /api/eval/run`

用途：

- 基于当前任务状态重跑 `RuleScorer`
- 持久化新的 `eval_result`
- 追加 `eval_finished` 事件

请求体：

```json
{
  "task_id": "task_xxx"
}
```

失败：

- 任务不存在时返回 `404`

## 9. 运行固定回归评测

### `POST /api/eval/cases/run`

用途：

- 运行当前 6 个真实支持 case 的固定回归评测
- 返回整体通过率、重试统计和平均质量指标
- 复用真实 `run_fixed_eval_cases()` 链路，不依赖额外 mock

当前摘要字段：

- `total_cases`
- `passed_cases`
- `failed_cases`
- `pass_rate`
- `retried_tool_calls`
- `retry_attempts_total`
- `average_tool_success_rate`
- `average_tool_elapsed_ms_total`
- `average_trace_completeness`
- `average_report_completeness`
- `average_chart_validity`
- `average_field_validity`
- `results`

当前 6 个真实支持 case 包括：

- `analyse category sales top 5`
- `analyse category sales share`
- `analyse category sales anomalies`
- `analyse sales by region`
- `analyse sales trend by order date`
- `analyse channel order count and sales performance`

## 10. 本地演示页

### `GET /demo`

用途：

- 作为极简本地演示页复用现有真实后端接口
- 串联文件上传、分析任务创建、任务执行、结果轮询和过程展示

页面当前能力：

- 上传 CSV / Excel
- 选择或填写当前支持的分析问题
- 展示任务摘要
- 预览基于 `chart_specs` 的图表结果
- 展示最终报告、事件时间线和工具日志
- 查看 LLM provider 状态并触发 smoke 检查
- 查看 project runtime overview
- 运行固定评测集并展示摘要

说明：

- 该页面由 FastAPI 直接返回 HTML
- 它不是 React 前端，也不是独立前端工程

### `GET /api/project-status`

用途：

- 查询当前项目运行总览状态
- 统一展示 provider 解析、演示页可用性和 SQLite 表行数

返回字段：

- `summary.provider`
- `summary.demo`
- `summary.session_store`
- `summary.database.tables.files`
- `summary.database.tables.analysis_tasks`
- `summary.database.tables.analysis_events`
- `summary.database.tables.tool_call_logs`
- `summary.database.tables.eval_results`

说明：

- 这个接口只读取已有状态，不会写入业务数据
- `/demo` 当前已经使用这个接口展示 project runtime overview
- `summary.session_store` 会直接暴露 session store runtime mode，包括 `preferred_backend`、`active_backend`、`redis_available`、`degraded_to_sqlite` 和 `redis_url`

## 11. 相关验证命令

全量测试：

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m pytest -v
```

固定回归评测：

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/eval/cases/run"
```

一键演示：

```powershell
cd E:\bgagent1
.\scripts\demo_mvp.ps1 -StartServer
```

脚本会输出一份紧凑的 JSON 摘要，其中包含：

- `project_status_provider`
- `project_status_session_store_active_backend`
- `project_status_session_store_warning_count`
- `provider_smoke_error_message`
- `fixed_eval_average_trace_completeness`
- `fixed_eval_average_report_completeness`
- 以及六个固定 demo 问题的执行摘要

项目运行总览：

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/api/project-status"
```

## 12. LLM Provider 状态与 smoke 检查

### `GET /api/llm/provider-status`

用途：

- 查询当前 LLM provider 解析结果
- 确认 provider、fallback 开关、key 来源、base URL、model 和 timeout

返回字段：

- `provider`
- `allow_fallback`
- `has_api_key`
- `api_key_source`
- `base_url`
- `model`
- `timeout_seconds`
- `diagnostics`

### `POST /api/llm/provider-smoke`

用途：

- 执行一次最小真实 provider 调用
- 用于部署前或环境变量切换后的快速验证

返回字段：

- `provider_resolution`
- `client_type`
- `ok`
- `analysis_goal` 或 `error_type`
- `error_message`
- `diagnostics`

说明：

- 这个接口不会写入业务任务状态
- 这个接口专用于 provider 诊断
- 仓库根目录下的 `scripts/qwen_provider_smoke.ps1` 复用同样的最小验证逻辑

相关验证命令：

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/api/llm/provider-status"
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/llm/provider-smoke"
cd E:\bgagent1
.\scripts\qwen_provider_smoke.ps1
```

`diagnostics` 字段说明：

- `provider_supported`：当前 provider 是否属于项目已支持集合
- `key_source_kind`：当前 key 来源类别，可能为 `qwen`、`openai_compatible` 或 `missing`
- `smoke_ready`：当前配置是否满足最小 smoke 调用前置条件
- `warnings`：当前配置下的风险提示
- `recommendations`：建议的下一步排查或配置动作
