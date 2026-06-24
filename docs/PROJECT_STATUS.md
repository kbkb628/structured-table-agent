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
- Sandbox 运行时诊断：`GET /api/sandbox/status`
- Sandbox 受控执行：`POST /api/sandbox/execute`
- SQLite 持久化：`files`、`analysis_tasks`、`analysis_events`、`tool_call_logs`、`eval_results`
- DuckDB 真实聚合工具：按品类、地区、渠道执行聚合分析
- Share 分析工具：按维度计算指标占比、贡献率和百分比
- Trend 分析工具：按 `order_date` 执行时间维度聚合、升序排序和折线图输出
- Anomaly 分析工具：按分组聚合结果执行基于 z-score 的异常值识别
- JSONL staged retrieval 检索栈，包含显式 BM25 召回、embedding 向量召回、rerank 重排与 SQLite embedding cache
- LangGraph 显式状态流，包含 `validate_tool_result` 与 `route_next_step`
- `GET /api/project-status` / `/demo` / `demo_mvp.ps1` 会暴露最新任务里 `route_next_step:continue|finish` 的真实摘要，证明多指标任务确实发生过继续/收尾路由
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
- 本地 staged retrieval 语义增强（BM25 + embedding + rerank）
- LangGraph 多步状态流与最小动态路由
- pandas / DuckDB 与真实 Plotly 图表生成、`plotly_spec` 兼容持久化输出的受控工具链
- 占比分析工具与主链接入
- 趋势分析工具与主链接入
- 异常检测工具与主链接入
- 真实 Tongyi Qianwen Provider 接入
- SQLite 持久化与 Redis 优先 / SQLite 降级
- 规则评分与固定 case 回归验证
- 受控 DockerSandbox 执行能力，支持 `advanced_code_execution`、`GET /api/sandbox/status` 和 `POST /api/sandbox/execute`
- `GET /api/sandbox/status` 与 `GET /api/project-status` 中的 `summary.sandbox` 已显式暴露 `supported_templates`、`max_timeout_seconds` 和 `max_code_chars`
- 基于真实 API 的极简页面演示闭环
- 基于 `GET /api/project-status` 的项目运行总览接口
- 基于 `scripts/demo_mvp.ps1` 的一键演示交付链路

当前不能声明已实现：

- 异步队列执行
- 完整 React 前端
- 完整生产级多 Provider 调度平台

说明：

- 现在已经实现“真实外部 LLM Provider 接入”，因此旧的“未实现真实 LLM Provider”边界已经失效。
- 但不能把项目表述成“所有分析都由 LLM 完成”。数值计算仍然由确定性工具完成，LLM 主要负责目标理解、计划组织、报告表达和补充评审。
- 现在已经实现受控 DockerSandbox，但不能把它表述成主分析链或默认执行路径。主数值真相路径仍然是 DuckDB + 受控工具链。

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
- `keyword_retriever` 当前已升级为 staged retrieval 组装层：
  - `bm25_retriever` 负责显式 BM25 lexical retrieval
  - `vector_retriever` 负责 embedding similarity retrieval
  - `reranker` 负责 merged candidates 的最终重排
  - `embedding_store` 负责 SQLite knowledge embedding cache
  - `retrieval_evidence` 会写入 `bm25_rank`、`bm25_score`、`embedding_rank`、`embedding_score`、`rerank_score`、`final_rank`、`retrieval_sources`
  - `score_breakdown` 仍保留 lexical score 可拆解明细
- `GET /api/project-status` / `/demo` / `demo_mvp.ps1` 会暴露最新任务 top business context 的 `score`、`related_field_count`、`has_score_breakdown`、`keyword_score`、`field_score`、`phrase_score`、`bm25_score`、`embedding_score`、`rerank_score` 和 `retrieval_sources`
- `GET /api/project-status` / `/demo` / `demo_mvp.ps1` 也会暴露最新任务 `field_understanding` 里的 `analysis_type`、`candidate_fields`、`warnings`、`planned_tool_sequence` 摘要，作为字段错配治理和 schema 约束仍然留存在运行态的证据
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
    - 最近一次 `session_state_recovered` 的 `recovery_source`
    - 最近一次恢复涉及的 `recovered_segments`
  - `files`
  - `analysis_tasks`
  - `analysis_events`
  - `tool_call_logs`
  - `eval_results`
- `scripts/demo_mvp.ps1` 当前输出：
  - `project_status_provider`
  - `project_status_demo_available`
  - `project_status_demo_path`
  - `project_status_latest_task_id`
  - `project_status_latest_task_status`
  - `project_status_latest_task_updated_at`
  - `project_status_session_store_preferred_backend`
  - `project_status_session_store_active_backend`
  - `project_status_session_store_redis_available`
  - `project_status_session_store_degraded_to_sqlite`
  - `project_status_session_store_redis_url`
  - `project_status_session_store_warning_count`
  - `project_status_session_store_recovered_count`
  - `project_status_session_store_latest_warning_task_id`
  - `project_status_session_store_latest_warning_at`
  - `project_status_session_store_latest_recovered_task_id`
  - `project_status_session_store_latest_recovered_at`
  - `project_status_session_store_latest_recovered_recovery_source`
  - `project_status_session_store_latest_recovered_segment_count`
  - `project_status_session_store_latest_recovered_segments`
  - `project_status_latest_task_has_business_context`
  - `project_status_latest_task_has_eval_result`
  - `project_status_latest_task_eval_overall_score`
  - `project_status_latest_task_eval_issue_count`
  - `project_status_latest_task_eval_suggestion_count`
  - `project_status_latest_task_eval_schema_valid`
  - `project_status_latest_task_eval_tool_success_rate`
  - `project_status_latest_task_eval_tool_elapsed_ms_total`
  - `project_status_latest_task_eval_field_validity`
  - `project_status_latest_task_eval_chart_validity`
  - `project_status_latest_task_eval_report_completeness`
  - `project_status_latest_task_eval_trace_completeness`
  - `project_status_latest_task_pending_metric_count`
  - `project_status_latest_task_planned_tool_call_count`
  - `project_status_latest_task_event_count`
  - `project_status_latest_task_latest_event_type`
  - `project_status_latest_task_route_decision_count`
  - `project_status_latest_task_continued_route_decision_count`
  - `project_status_latest_task_finished_route_decision_count`
  - `project_status_latest_task_latest_route_decision`
  - `project_status_latest_task_chart_spec_count`
  - `project_status_latest_task_key_finding_count`
  - `project_status_latest_task_business_suggestion_count`
  - `project_status_latest_task_data_limitation_count`
  - `project_status_latest_task_business_context_count`
  - `project_status_latest_task_top_business_context_title`
  - `project_status_latest_task_top_business_context_score`
  - `project_status_latest_task_top_business_context_related_field_count`
  - `project_status_latest_task_top_business_context_has_score_breakdown`
  - `project_status_latest_task_top_business_context_keyword_score`
  - `project_status_latest_task_top_business_context_field_score`
  - `project_status_latest_task_top_business_context_phrase_score`
  - `project_status_latest_task_top_business_context_bm25_score`
  - `project_status_latest_task_top_business_context_embedding_score`
  - `project_status_latest_task_top_business_context_rerank_score`
  - `project_status_latest_task_top_business_context_retrieval_sources`
  - `project_status_latest_task_checkpoint_current_step`
  - `project_status_latest_task_checkpoint_status`
  - `project_status_latest_task_checkpoint_pending_metric_count`
  - `project_status_latest_task_checkpoint_finding_count`
  - `project_status_latest_task_checkpoint_business_context_title_count`
  - `project_status_latest_task_checkpoint_business_context_titles`
  - `project_status_latest_task_checkpoint_draft_report_status`
  - `project_status_latest_task_has_context_checkpoint`
  - `project_status_latest_task_has_draft_report`
  - `project_status_latest_task_has_final_report`
  - `project_status_latest_task_eval_has_dimension_scores`
  - `project_status_latest_task_latest_event_at`
  - `project_status_latest_task_llm_issue_count`
  - `project_status_latest_task_next_step_count`
  - `project_status_latest_task_checkpoint_latest_error_code`
  - `project_status_latest_task_analysis_goal`
  - `project_status_latest_task_analysis_plan_count`
  - `project_status_latest_task_current_step`
  - `project_status_latest_task_completed_step_count`
  - `project_status_latest_task_finding_count`
  - `project_status_latest_task_dimension_field`
  - `project_status_latest_task_match_analysis_type`
  - `project_status_latest_task_candidate_field_count`
  - `project_status_latest_task_match_warning_count`
  - `project_status_latest_task_planned_tool_sequence`
  - `project_status_latest_task_metric_count`
  - `project_status_latest_task_tool_result_count`
  - `project_status_latest_task_successful_tool_result_count`
  - `project_status_latest_task_failed_tool_result_count`
  - `project_status_latest_task_retried_tool_result_count`
  - `project_status_latest_task_retry_attempts_total`
  - `project_status_latest_task_latest_retry_status`
  - `project_status_latest_task_latest_tool_name`
  - `project_status_latest_task_total_tool_elapsed_ms`
  - `project_status_latest_task_error_count`
  - `project_status_latest_task_latest_error_code`
  - `project_status_latest_task_latest_error_message`
  - `project_status_latest_task_has_degradation`
  - `project_status_latest_task_top_key_finding`
  - `project_status_latest_task_latest_finding_summary`
  - `project_status_latest_task_has_llm_judgement`
  - `project_status_latest_task_supported_by_tools`
  - `project_status_latest_task_has_findings`
  - `project_status_latest_task_judgement_issue_count`
  - `project_status_latest_task_tool_call_log_count`
  - `project_status_files`
  - `project_status_tasks`
  - `project_status_analysis_events`
  - `project_status_tool_call_logs`
  - `project_status_eval_results`
  - `provider_status_allow_fallback`
  - `provider_status_has_api_key`
  - `provider_status_key_source`
  - `provider_status_base_url`
  - `provider_status_model`
  - `provider_status_timeout_seconds`
  - `provider_status_provider_supported`
  - `provider_status_key_source_kind`
  - `provider_status_smoke_ready`
  - `provider_status_warnings`
  - `provider_status_recommendations`
  - `provider_smoke_ok`
  - `provider_smoke_client_type`
  - `provider_smoke_error_type`
  - `provider_smoke_error_message`
  - `fixed_eval_pass_rate`
  - `fixed_eval_passed_cases`
  - `fixed_eval_total_cases`
  - `fixed_eval_retried_tool_calls`
  - `fixed_eval_retry_attempts_total`
  - `fixed_eval_average_tool_elapsed_ms_total`
  - `fixed_eval_average_trace_completeness`
  - `fixed_eval_average_report_completeness`
  - `fixed_eval_average_tool_success_rate`
  - `fixed_eval_average_chart_validity`
  - `fixed_eval_average_field_validity`
  - `fixed_eval_case_ids`
  - `fixed_eval_questions`
  - `project_status_demo_available`
  - `project_status_session_store_redis_available`
  - `project_status_session_store_degraded_to_sqlite`
  - `project_status_session_store_recovered_count`
  - `project_status_latest_task_eval_issue_count`
  - `project_status_latest_task_planned_tool_call_count`
  - `project_status_latest_task_event_count`
  - `project_status_latest_task_business_suggestion_count`
  - `project_status_latest_task_data_limitation_count`
  - `project_status_latest_task_top_business_context_title`
  - `project_status_latest_task_checkpoint_draft_report_status`
  - `project_status_latest_task_completed_step_count`
  - `project_status_latest_task_metric_count`
  - `project_status_latest_task_successful_tool_result_count`
  - `project_status_latest_task_failed_tool_result_count`
  - `project_status_latest_task_latest_retry_status`
  - `project_status_latest_task_latest_error_code`
  - `project_status_files_exists`
  - `project_status_tasks_exists`
  - `project_status_analysis_events_exists`
  - `project_status_tool_call_logs_exists`
  - `project_status_eval_results_exists`
  - `project_status_files`
  - `project_status_tasks`
  - `project_status_analysis_events`
  - `project_status_tool_call_logs`
  - `project_status_eval_results`
  - 九个固定 case 的任务结果摘要，其中包含三条中文 MVP 验收问句

## 当前结论

- 如果按最初 MVP 要求看，项目主链路早已完成。
- 按当前“贴合简历表达”的目标看，项目现在已经跨过“真实 LLM 接入”和“可验证演示交付”这两个关键门槛。
- 现阶段剩余未实现内容已经不包含 retrieval 主链本体，主要集中在执行隔离、前端和生产化治理。

## 剩余增强方向

- 增强 retrieval 规模化能力，例如 embedding 增量刷新、召回质量评测和模型缓存治理
- 增强 Redis 会话记忆和异步执行
- 增强 DockerSandbox 工程化能力，例如更细的资源约束、脚本模板与异常分类
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

## Redis Memory Realization Update

- Added real Redis-backed `memory_context` for file-scoped historical analysis reuse.
- Runtime memory now includes `recent_turns`, `summary_memory`, `summary_text`, and windowed `recent_turn_count`.
- `SessionStore` now writes both task-scoped `analysis_state` and file-scoped memory snapshots.
- `task_builder` injects memory into startup planning, and completed tasks append back into Redis memory.
- `GET /api/project-status` and `/demo` now surface memory runtime evidence alongside retrieval, report, and tool evidence.

## LLM-As-Judge Realization Update

- Added a structured `LLM-as-Judge` layer with `judge_summary`, `judge_status`, and dimensioned judge outputs.
- Current judge dimensions include `groundedness`, `completeness`, and `clarity`.
- Judge evidence is packed from question, final report, tool outputs, retrieval context, memory context, and trace events.
- Judge provider failures now degrade explicitly to `judge_status = degraded` instead of failing a completed task.
- `GET /api/project-status`, `/demo`, `/api/eval/run`, and fixed eval cases now surface judge runtime evidence separately from rule scores.
## DockerSandbox Realization Update

- Added real `DockerSandbox` runtime capability through the controlled `advanced_code_execution` path.
- Added sandbox diagnostics endpoint: `GET /api/sandbox/status`
- Added sandbox execution endpoint: `POST /api/sandbox/execute`
- Added dedicated persisted sandbox execution evidence for direct sandbox API runs.
- Added classified sandbox failure codes, including `SANDBOX_SYNTAX_ERROR`, `SANDBOX_IMPORT_ERROR`, `SANDBOX_PERMISSION_ERROR`, `SANDBOX_NETWORK_ERROR`, and `SANDBOX_RESOURCE_KILLED`.
- Added named sandbox execution templates, including `region_sales_summary`.
- Added timeout request validation so sandbox API calls cannot exceed the configured runtime ceiling.
- Added explicit sandbox capability boundary fields: `supported_templates`, `max_timeout_seconds`, and `max_code_chars`.
- Added inline `python_code` length validation so direct sandbox API calls stay within the configured code ceiling.
- Added sandbox runtime summary inside `GET /api/project-status`
- Surfaced sandbox runtime evidence in `/demo`
- DockerSandbox remains a second-phase controlled execution capability and does not replace the main DuckDB and tool-driven deterministic analysis chain.
