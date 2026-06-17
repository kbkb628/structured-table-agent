# API Reference

本文档描述当前 MVP 已真实实现的后端接口，接口边界与 `DEVELOPMENT_GUIDE.md` 保持一致。

## 1. 上传文件

### `POST /api/files/upload`

用途：

- 上传 CSV 文件
- 生成字段画像
- 持久化文件元数据到 SQLite

请求：

- `multipart/form-data`
- 字段：`file`

当前限制：

- 仅支持 `.csv`
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
- 运行轻量 JSONL 关键词检索
- 用 `MockLLM` 生成 `analysis_goal` 和 `analysis_plan`
- 写入启动事件时间线

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
- `business_context`

失败：

- 文件不存在时返回 `404`

## 4. 执行分析任务

### `POST /api/analysis/{task_id}/run`

用途：

- 执行 LangGraph 最小线性状态流
- 完成字段匹配、DuckDB 聚合、图表生成、报告生成和规则评分

当前图结构：

1. `load_task`
2. `match_fields`
3. `execute_tools`
4. `generate_charts`
5. `generate_report`
6. `evaluate_report`

响应为完整任务状态，包含：

- `field_understanding`
- `tool_results`
- `chart_specs`
- `final_report`
- `eval_result`
- `errors`

## 5. 查询任务状态

### `GET /api/analysis/{task_id}`

用途：

- 读取完整任务状态
- 回填当前任务事件列表

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
- `task_completed`
- `task_failed`
- `eval_finished`

## 7. 手动重跑评估

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

## 8. 相关验证命令

全量测试：

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m pytest -v
```

一键演示：

```powershell
cd E:\bgagent1
.\scripts\demo_mvp.ps1 -StartServer
```
