# Project Status

本文档是当前项目状态的唯一收口清单，用于持续对齐 `DEVELOPMENT_GUIDE.md`、README、测试和简历表达边界。

## 已完成

- 文件上传：`POST /api/files/upload`
- 字段画像查询：`GET /api/files/{file_id}/profile`
- 分析任务创建：`POST /api/analysis/start`
- 分析任务执行：`POST /api/analysis/{task_id}/run`
- 任务状态查询：`GET /api/analysis/{task_id}`
- 事件时间线查询：`GET /api/analysis/{task_id}/events`
- 工具调用日志查询：`GET /api/analysis/{task_id}/tool-logs`
- 规则评估重算：`POST /api/eval/run`
- 固定回归评测：`POST /api/eval/cases/run`
- LLM provider 诊断：`GET /api/llm/provider-status`
- LLM provider smoke：`POST /api/llm/provider-smoke`
- 项目运行总览：`GET /api/project-status`
- SQLite 持久化：`files`、`analysis_tasks`、`analysis_events`、`tool_call_logs`、`eval_results`
- DuckDB 真实聚合工具：按品类、地区、渠道执行聚合分析
- Share 分析工具：按维度计算指标占比、贡献率和百分比
- Trend 分析工具：按 `order_date` 执行时间维度聚合、升序排序和折线图输出
- Anomaly 分析工具：按分组聚合结果执行基于 z-score 的异常值识别
- JSONL 本地混合检索，包含关键词、短语命中、字段加权和 BM25 风格评分
- LangGraph 显式状态流，包含 `validate_tool_result` 与 `route_next_step`
- 真实可替换 LLM Provider 接入：
  - `QwenClient`
  - `MockLLMClient`
  - `get_llm_client()` provider 工厂
- Qwen 驱动的：
  - 分析目标生成
  - 分析计划生成
  - 最终报告生成
  - 补充型 `llm_judgement`
- Observability 事件收口：`backend/app/observability`
- Windows 一键演示脚本：`scripts/demo_mvp.ps1`
- provider smoke 脚本：`scripts/qwen_provider_smoke.ps1`
- 极简本地演示页：`GET /demo`

## 当前真实能力边界

当前可以真实声明已实现：

- CSV / Excel 上传与字段画像
- 从自然语言问题到工具执行的完整分析闭环
- 轻量 RAG 业务语义增强
- 本地混合检索 / BM25 风格语义增强
- LangGraph 多步状态流与最小动态路由
- pandas / DuckDB / Plotly 的受控工具链
- 占比分析工具与主链接入
- 趋势分析工具与主链接入
- 异常检测工具与主链接入
- 真实 Tongyi Qianwen Provider 接入
- SQLite 持久化与 Redis 优先 / SQLite 降级
- 规则评分与固定 case 回归验证
- 基于真实 API 的极简页面演示闭环
- 基于 `GET /api/project-status` 的项目运行总览接口
- 基于 `scripts/demo_mvp.ps1` 的一键演示交付链路

当前不能声明已实现：

- 异步队列执行
- embedding / 向量检索 / rerank
- DockerSandbox
- 完整 React 前端
- 完整生产级多 Provider 调度平台

说明：

- 现在已经实现“真实外部 LLM Provider 接入”，因此旧的“未实现真实 LLM Provider”边界已经失效。
- 但不能把项目表述成“所有分析都由 LLM 完成”。数值计算仍然由确定性工具完成，LLM 主要负责目标理解、计划组织、报告表达和补充评审。

## 已完成审计证据

- 最新 provider / task-builder / runner / qwen 定向验证：
  - `tests/test_llm_provider_factory.py`
  - `tests/test_task_builder.py`
  - `tests/test_qwen_client.py`
  - `tests/test_analysis_runner.py`
- 最新 demo / 交付文档 / project-status 相关验证：
  - `tests/test_demo_page.py`
  - `tests/test_demo_script_consistency.py`
  - `tests/test_project_status_api.py`
  - `tests/test_delivery_docs.py`
- 最新全量测试：
  - 以 `cd backend && .\.venv\Scripts\python.exe -m pytest -q` 为准
- 最新真实 Provider smoke check：
  - 以 `LLM_PROVIDER=qwen` 环境下 `get_llm_client()` 和最小真实调用结果为准

## 当前实现细节收口

- `POST /api/analysis/start` 返回：
  - `task_id`
  - `status`
  - `analysis_goal`
  - `analysis_plan`
- `business_context` 会真实写入任务状态，并可通过 `GET /api/analysis/{task_id}` 查看
- `GET /api/analysis/{task_id}` 当前还会返回：
  - `pending_metrics`
  - `pending_tool_calls`
  - `context_checkpoint`
  - `tool_call_logs`
  - `llm_judgement`
- 工具调用链真实落库到 `tool_call_logs`：
  - `match_fields`
  - `groupby_aggregate`
  - `calculate_share`
  - `trend_analysis`
  - `anomaly_analysis`
  - `generate_chart`
  - `generate_report`
- 固定 case 回归当前额外输出：
  - `retried_tool_calls`
  - `retry_attempts_total`
  - `average_tool_success_rate`
  - `average_tool_elapsed_ms_total`
  - `average_trace_completeness`
  - `average_report_completeness`
  - `average_chart_validity`
  - `average_field_validity`
- 报告工具输出和 LLM 报告层最终都受 `FinalReport` schema 约束
- LangGraph 当前支持：
  - `match_fields` 生成 `pending_metrics`
  - `match_fields` 生成 `planned_tool_calls`
  - `execute_tools` 逐个消费 metric
  - `validate_tool_result` 校验成功与非空结果
  - `route_next_step` 决定继续统计还是进入图表阶段
  - `generate_report` 先形成 `draft_report`，再生成最终 `final_report`
- `evaluate_report` 写入 `eval_result` 与 `llm_judgement`
- `share_tool` 当前支持：
  - 分组后指标占比计算
  - `share_ratio`
  - `share_percent`
  - 自然语言 share 问题接入 LangGraph 主链
- `trend_tool` 当前支持：
  - 按时间维度聚合
  - 按日期升序排序
  - 趋势类问题输出折线图配置
- `anomaly_tool` 当前支持：
  - 按维度聚合后的 z-score 异常值识别
  - 输出 `z_score`
  - 输出 `is_anomaly`
- `keyword_retriever` 当前已升级为本地混合检索：
  - 关键词重叠打分
  - 短语命中加权
  - `related_fields` 字段加权
  - BM25 风格归一化评分
  - `score_breakdown` 检索打分明细
- `/demo` 当前支持：
  - 上传或加载样例数据
  - 创建并执行真实分析任务
  - 查看任务摘要、图表预览、最终报告、事件时间线和工具日志
  - 查看 provider status / smoke
  - 查看 project runtime overview
  - 运行 fixed eval cases
- `GET /api/project-status` 当前聚合：
  - provider 解析与 diagnostics
  - demo 可用性与路径
  - `summary.session_store` 运行态摘要
  - `files`
  - `analysis_tasks`
  - `analysis_events`
  - `tool_call_logs`
  - `eval_results`
- `scripts/demo_mvp.ps1` 当前输出：
  - `project_status_provider`
  - `project_status_demo_available`
  - `project_status_session_store_active_backend`
  - `project_status_session_store_redis_available`
  - `project_status_session_store_degraded_to_sqlite`
  - `project_status_session_store_warning_count`
  - `project_status_session_store_recovered_count`
  - `project_status_latest_task_has_business_context`
  - `project_status_latest_task_has_eval_result`
  - `project_status_latest_task_eval_overall_score`
  - `project_status_latest_task_eval_issue_count`
  - `project_status_latest_task_pending_metric_count`
  - `project_status_latest_task_planned_tool_call_count`
  - `project_status_latest_task_event_count`
  - `project_status_latest_task_latest_event_type`
  - `project_status_latest_task_chart_spec_count`
  - `project_status_latest_task_key_finding_count`
  - `project_status_latest_task_business_suggestion_count`
  - `project_status_latest_task_data_limitation_count`
  - `project_status_latest_task_business_context_count`
  - `project_status_latest_task_top_business_context_title`
  - `project_status_latest_task_checkpoint_current_step`
  - `project_status_latest_task_checkpoint_draft_report_status`
  - `project_status_latest_task_analysis_goal`
  - `project_status_latest_task_analysis_plan_count`
  - `project_status_latest_task_completed_step_count`
  - `project_status_latest_task_dimension_field`
  - `project_status_latest_task_metric_count`
  - `project_status_latest_task_tool_result_count`
  - `project_status_latest_task_successful_tool_result_count`
  - `project_status_latest_task_failed_tool_result_count`
  - `project_status_latest_task_total_tool_elapsed_ms`
  - `project_status_latest_task_error_count`
  - `project_status_latest_task_latest_error_code`
  - `project_status_latest_task_has_degradation`
  - `project_status_latest_task_has_llm_judgement`
  - `project_status_latest_task_supported_by_tools`
  - `project_status_latest_task_has_findings`
  - `project_status_latest_task_tool_call_log_count`
  - `project_status_files`
  - `project_status_tasks`
  - `provider_status_key_source`
  - `provider_status_smoke_ready`
  - `provider_smoke_ok`
  - `provider_smoke_client_type`
  - `provider_smoke_error_type`
  - `provider_smoke_error_message`
  - `fixed_eval_pass_rate`
  - `fixed_eval_passed_cases`
  - `fixed_eval_total_cases`
  - `fixed_eval_average_trace_completeness`
  - `fixed_eval_average_report_completeness`
  - `fixed_eval_average_tool_success_rate`
  - 六个固定 demo 问题的任务结果摘要

## 当前结论

- 如果按最初 MVP 要求看，项目主链路早已完成。
- 按当前“贴合简历表达”的目标看，项目现在已经跨过“真实 LLM 接入”和“可验证演示交付”这两个关键门槛。
- 现阶段剩余未实现内容主要是第二阶段增强，而不是当前主链缺口。

## 剩余增强方向

- 升级到 `embedding + 向量检索 + rerank`
- 增强 Redis 会话记忆和异步执行
- 引入 DockerSandbox
- 增强前端过程展示
- 扩展更多分析工具，如更细粒度趋势分析、更多异常检测策略

## Latest Increment

- Added backend provider observability endpoint: `GET /api/llm/provider-status`
- Added backend provider smoke endpoint: `POST /api/llm/provider-smoke`
- Added repo-level smoke script: `scripts/qwen_provider_smoke.ps1`
- Added backend runtime overview endpoint: `GET /api/project-status`
- Added session store runtime summary inside `GET /api/project-status`
- Surfaced runtime overview in `/demo`
- Surfaced runtime overview in `scripts/demo_mvp.ps1`

These additions turn real Tongyi Qianwen integration and demo delivery into runtime-verifiable capabilities instead of only code-level capabilities:

- inspect the resolved `provider`
- inspect whether a usable key is detected
- inspect the current `api_key_source`
- run one minimal real provider call without creating a business task
- inspect whether `/demo` is available
- inspect SQLite row counts for core runtime tables

Latest real smoke evidence on this machine:

- resolved key source: `TONGYI_API_KEY`
- request reached DashScope successfully
- provider smoke returned `ok = true`
- `client_type = QwenClient`
- example `analysis_goal`: `Summarize total sales amount by region`
