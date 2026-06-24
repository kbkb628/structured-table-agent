# Structured Table Agent

面向结构化表格数据的多步骤分析与报告生成后端项目。当前实现仍然严格遵守 `DEVELOPMENT_GUIDE.md` 的真实边界，但已经从最初的 MockLLM-only MVP 演进到“真实 Tongyi Qianwen Provider + 可验证 demo 交付”的阶段。

## 项目简介

这个项目面向上传后的企业结构化表格数据，目标是在真实后端链路内完成：

- 字段画像
- 业务语义增强
- 分析计划生成
- DuckDB 聚合执行
- 图表配置生成
- 结构化报告输出
- 事件时间线记录
- 规则评分与固定 case 回归
- Provider 诊断与项目运行总览展示

当前主链已经打通：

- CSV / Excel 上传与字段画像
- SQLite 元数据与任务状态持久化
- 基于 DuckDB 的真实聚合分析
- 基于 JSONL 的轻量混合检索
- 可替换的 `LLMClient` 抽象
- 真实 Tongyi Qianwen Provider 接入
- 基于 LangGraph 的最小分析状态流编排，包含显式 `route_next_step`
- 分析任务创建、执行、事件时间线查询和工具日志查询
- 品类、地区、渠道、趋势、占比、异常六类真实支持问题
- 规则评分 `eval_result` 自动写回与手动重算
- `/demo` 极简演示页
- `GET /api/project-status` 项目运行总览接口
- `scripts/demo_mvp.ps1` Windows 一键演示脚本

当前明确未实现：

- 异步队列
- DockerSandbox
- 完整 React 前端
- 生产级多 Provider 调度平台

## 技术栈

- 后端框架：FastAPI
- 状态编排：LangGraph
- 数据处理：pandas、DuckDB
- 模型约束：Pydantic
- 轻量 RAG：JSONL + staged retrieval（BM25 + embedding + rerank）
- 模型接口：`LLMClient`、`QwenClient`、`MockLLMClient`
- 持久化：SQLite
- 会话状态：Redis 优先，SQLite 降级
- 可观测性：SQLite 事件时间线 + `backend/app/observability`
- 测试：pytest

## 架构说明

当前真实链路如下：

1. 用户上传 CSV / Excel，服务端生成字段画像并落库
2. 用户创建分析任务，系统检索本地业务知识并生成 `analysis_goal` / `analysis_plan`
3. LangGraph 驱动字段匹配、DuckDB 聚合、下一步路由、图表生成、报告生成和规则评分
4. 关键步骤写入事件时间线，任务状态、工具日志和评估结果持久化到 SQLite
5. `/demo` 演示页与 `demo_mvp.ps1` 复用真实 API 展示任务流、provider 诊断、固定评测和 project runtime overview

## 目录结构

```text
backend/
  app/
    api/               HTTP 接口
    agent/             LangGraph 状态流
    eval/              RuleScorer 与固定回归 case
    llm/               Provider 工厂、QwenClient、MockLLMClient
    observability/     事件记录与 trace 常量
    rag/               本地 JSONL 知识库与检索
    schemas/           Pydantic 请求/响应结构
    services/          任务运行与 builder
    storage/           SQLite 与会话状态存储
    tools/             受控数据分析工具
  data/
    samples/           演示数据
    uploads/           上传文件
scripts/
  demo_mvp.ps1         Windows 一键演示脚本
  qwen_provider_smoke.ps1
docs/
  PROJECT_STATUS.md    当前项目状态与收口清单
  API_REFERENCE.md     接口说明
  RESUME_PROJECT_DESCRIPTION.md
  INTERVIEW_GUIDE.md
  superpowers/
```

## 项目文档

- [DEVELOPMENT_GUIDE.md](/e:/bgagent1/.worktrees/day1-mvp-backend/DEVELOPMENT_GUIDE.md)
  当前阶段开发边界与策略来源
- [docs/PROJECT_STATUS.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/PROJECT_STATUS.md)
  当前项目状态、真实边界与最新 smoke 证据
- [docs/API_REFERENCE.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/API_REFERENCE.md)
  后端接口说明与验证命令
- [docs/ARCHITECTURE_OVERVIEW.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/ARCHITECTURE_OVERVIEW.md)
  当前后端结构说明
- [docs/RESUME_PROJECT_DESCRIPTION.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/RESUME_PROJECT_DESCRIPTION.md)
  简历项目描述与可复用表达
- [docs/RESUME_EVIDENCE_MAP.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/RESUME_EVIDENCE_MAP.md)
  简历说法到代码、演示和测试证据的映射
- [docs/INTERVIEW_GUIDE.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/INTERVIEW_GUIDE.md)
  面试讲解稿与边界表达
- [docs/INTERVIEW_DEMO_CHECKLIST.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/INTERVIEW_DEMO_CHECKLIST.md)
  2-5 分钟最短面试演示路径
- [docs/INTERVIEW_DEMO_PREFLIGHT.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/INTERVIEW_DEMO_PREFLIGHT.md)
  演示前启动、自检与失败排查清单
- [docs/RELEASE_READINESS_AUDIT.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/RELEASE_READINESS_AUDIT.md)
  当前仓库是否已达到可封板状态的审计结论
- [backend/README.md](/e:/bgagent1/.worktrees/day1-mvp-backend/backend/README.md)
  后端启动、测试、Provider 配置和 Windows API 示例
- [scripts/demo_mvp.ps1](/e:/bgagent1/.worktrees/day1-mvp-backend/scripts/demo_mvp.ps1)
  一键上传样例 CSV 并跑通当前演示链路

## 快速开始

```powershell
cd E:\bgagent1\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=120 fastapi uvicorn python-multipart pandas duckdb pytest httpx
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

完整使用示例、测试命令和 API 调用方式见 [backend/README.md](/e:/bgagent1/.worktrees/day1-mvp-backend/backend/README.md)。

## 环境与数据

- Python：`3.12`
- 默认数据库：`backend/app.db`
- 样例数据：`backend/data/samples/sales_orders.csv`
- 默认上传目录：`backend/data/uploads`

说明：
- `backend/app.db` 与 `backend/data/*.db` 属于本地运行时 SQLite 产物，不作为源码交付内容纳入版本控制。

LLM 相关环境变量：

- `LLM_PROVIDER=qwen|mock`
- `LLM_ALLOW_FALLBACK=true|false`
- `QWEN_API_KEY`
- `TONGYI_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_MODEL`
- `QWEN_TIMEOUT_SECONDS`

当前 Redis 仍是推荐依赖而不是强制依赖。Redis 不可用时，系统会显式降级到 SQLite 并记录 `session_store_warning` 事件。
现在 `GET /api/project-status` 与 `/demo` 也会直接展示 session store runtime mode，包括 `preferred_backend`、`active_backend`、`redis_available` 和 `degraded_to_sqlite`，便于把“Redis 优先 / SQLite 降级”作为运行时事实演示，而不只是文档表述。
如果最新恢复事件存在，`GET /api/project-status`、`/demo` 和 `scripts/demo_mvp.ps1` 还会直接暴露 `project_status_session_store_latest_recovered_recovery_source`、`project_status_session_store_latest_recovered_segment_count` 和 `project_status_session_store_latest_recovered_segments`，用于说明最近一次 `session_state_recovered` 事件是基于哪些细粒度 Redis 段完成回填的。

## 样例数据说明

当前样例数据文件是 `backend/data/samples/sales_orders.csv`，字段包括：

- `order_id`
- `customer_id`
- `order_date`
- `region`
- `channel`
- `product_category`
- `product_name`
- `quantity`
- `sales_amount`
- `discount`
- `order_status`

样例数据当前支持：

- 品类销售额 TopN
- 品类销售占比
- 品类异常检测
- 地区销售额对比
- 渠道订单数与销售额对比
- 按日期的销售趋势分析

## 一键演示

如果本地已经建好 `backend/.venv`，可以直接运行：

```powershell
cd E:\bgagent1
.\scripts\demo_mvp.ps1 -StartServer
```

脚本会：

- 自动启动本地 FastAPI 服务
- 调用 `GET /api/llm/provider-status` 与 `POST /api/llm/provider-smoke`，先做 provider 运行时诊断
- 上传 `backend/data/samples/sales_orders.csv`
- 依次运行六个当前支持的英文演示问题（页面快捷按钮已覆盖其中 6 条）
- `/demo` 页面同时提供三条中文 MVP 验收问句的快捷按钮，便于直接演示指导文档定义的中文验收口径
- 对最后一个任务调用 `POST /api/eval/run` 重跑一次评估
- 刷新 `GET /api/project-status` 获取本轮演示后的当前项目运行总览
- 在 project runtime overview 中直接查看 session store runtime mode，包括 `preferred_backend`、`active_backend`、`redis_available` 和 `degraded_to_sqlite`
- 输出 project status 摘要、任务状态、图表数量、工具调用数量和评估分数摘要
- 输出 `project_status_provider` 作为 project runtime overview 的 provider 摘要字段
- 输出 `project_status_session_store_preferred_backend`、`project_status_session_store_active_backend`、`project_status_session_store_redis_available`、`project_status_session_store_degraded_to_sqlite`、`project_status_session_store_redis_url`、`project_status_session_store_warning_count`、`project_status_session_store_recovered_count`、`project_status_session_store_latest_warning_task_id`、`project_status_session_store_latest_warning_at`、`project_status_session_store_latest_recovered_task_id`、`project_status_session_store_latest_recovered_at`、`project_status_session_store_latest_recovered_recovery_source`、`project_status_session_store_latest_recovered_segment_count`、`project_status_session_store_latest_recovered_segments` 等 session store runtime mode 与事件摘要字段
- 输出 `project_status_latest_task_has_business_context`、`project_status_latest_task_has_context_checkpoint`、`project_status_latest_task_has_draft_report`、`project_status_latest_task_has_final_report`、`project_status_latest_task_has_eval_result`、`project_status_latest_task_eval_overall_score`、`project_status_latest_task_eval_suggestion_count`、`project_status_latest_task_eval_has_dimension_scores`、`project_status_latest_task_eval_schema_valid`、`project_status_latest_task_eval_tool_success_rate`、`project_status_latest_task_eval_tool_elapsed_ms_total`、`project_status_latest_task_eval_field_validity`、`project_status_latest_task_eval_chart_validity`、`project_status_latest_task_eval_report_completeness`、`project_status_latest_task_eval_trace_completeness`、`project_status_latest_task_pending_metric_count`、`project_status_latest_task_latest_event_type`、`project_status_latest_task_latest_event_at`、`project_status_latest_task_llm_issue_count`、`project_status_latest_task_route_decision_count`、`project_status_latest_task_continued_route_decision_count`、`project_status_latest_task_finished_route_decision_count`、`project_status_latest_task_latest_route_decision`、`project_status_latest_task_chart_spec_count`、`project_status_latest_task_key_finding_count`、`project_status_latest_task_top_key_finding`、`project_status_latest_task_next_step_count`、`project_status_latest_task_business_context_count`、`project_status_latest_task_top_business_context_title`、`project_status_latest_task_top_business_context_score`、`project_status_latest_task_top_business_context_related_field_count`、`project_status_latest_task_top_business_context_has_score_breakdown`、`project_status_latest_task_top_business_context_keyword_score`、`project_status_latest_task_top_business_context_field_score`、`project_status_latest_task_top_business_context_phrase_score`、`project_status_latest_task_top_business_context_bm25_score`、`project_status_latest_task_top_business_context_embedding_score`、`project_status_latest_task_top_business_context_rerank_score`、`project_status_latest_task_top_business_context_retrieval_sources`、`project_status_latest_task_checkpoint_current_step`、`project_status_latest_task_checkpoint_status`、`project_status_latest_task_checkpoint_pending_metric_count`、`project_status_latest_task_checkpoint_finding_count`、`project_status_latest_task_checkpoint_business_context_title_count`、`project_status_latest_task_checkpoint_business_context_titles`、`project_status_latest_task_checkpoint_latest_error_code`、`project_status_latest_task_analysis_goal`、`project_status_latest_task_analysis_plan_count`、`project_status_latest_task_current_step`、`project_status_latest_task_finding_count`、`project_status_latest_task_latest_finding_summary`、`project_status_latest_task_dimension_field`、`project_status_latest_task_match_analysis_type`、`project_status_latest_task_candidate_field_count`、`project_status_latest_task_match_warning_count`、`project_status_latest_task_planned_tool_sequence`、`project_status_latest_task_supported_by_tools`、`project_status_latest_task_has_findings`、`project_status_latest_task_tool_result_count`、`project_status_latest_task_retried_tool_result_count`、`project_status_latest_task_retry_attempts_total`、`project_status_latest_task_latest_tool_name`、`project_status_latest_task_total_tool_elapsed_ms`、`project_status_latest_task_error_count`、`project_status_latest_task_latest_error_message`、`project_status_latest_task_has_degradation` 等 latest task artifact / evaluation / judgement / process / report / context / semantics / tools / errors 摘要字段
- 另外还会输出 `project_status_demo_available`、`project_status_demo_path`、`project_status_latest_task_id`、`project_status_latest_task_status`、`project_status_latest_task_updated_at`、`project_status_session_store_redis_available`、`project_status_session_store_degraded_to_sqlite`、`project_status_session_store_recovered_count`、`project_status_latest_task_has_llm_judgement`、`project_status_latest_task_judgement_issue_count`、`project_status_latest_task_tool_call_log_count`、`project_status_latest_task_eval_issue_count`、`project_status_latest_task_planned_tool_call_count`、`project_status_latest_task_event_count`、`project_status_latest_task_business_suggestion_count`、`project_status_latest_task_data_limitation_count`、`project_status_latest_task_checkpoint_draft_report_status`、`project_status_latest_task_completed_step_count`、`project_status_latest_task_metric_count`、`project_status_latest_task_successful_tool_result_count`、`project_status_latest_task_failed_tool_result_count`、`project_status_latest_task_latest_retry_status`、`project_status_latest_task_latest_error_code`、`project_status_files_exists`、`project_status_tasks_exists`、`project_status_analysis_events_exists`、`project_status_tool_call_logs_exists`、`project_status_eval_results_exists`、`project_status_files`、`project_status_tasks`、`project_status_analysis_events`、`project_status_tool_call_logs` 和 `project_status_eval_results` 等补充诊断字段
- 输出 `provider_status_allow_fallback`、`provider_status_has_api_key`、`provider_status_key_source`、`provider_status_base_url`、`provider_status_model`、`provider_status_timeout_seconds`、`provider_status_provider_supported`、`provider_status_key_source_kind`、`provider_status_smoke_ready`、`provider_status_warnings`、`provider_status_recommendations`、`provider_smoke_ok`、`provider_smoke_client_type`、`provider_smoke_error_type`、`provider_smoke_error_message` 等 provider 运行时诊断字段
- 输出 `fixed_eval_pass_rate`、`fixed_eval_passed_cases`、`fixed_eval_total_cases`、`fixed_eval_retried_tool_calls`、`fixed_eval_retry_attempts_total`、`fixed_eval_average_tool_elapsed_ms_total`、`fixed_eval_average_trace_completeness`、`fixed_eval_average_report_completeness`、`fixed_eval_average_tool_success_rate`、`fixed_eval_average_chart_validity`、`fixed_eval_average_field_validity`、`fixed_eval_case_ids`、`fixed_eval_questions` 等 fixed eval 质量指标
- fixed eval 当前同时覆盖六个英文演示问题，以及 `DEVELOPMENT_GUIDE.md` 里定义的三条中文 MVP 验收问句

## API 与验证

当前关键接口：

- `POST /api/files/upload`
- `GET /api/files/{file_id}/profile`
- `POST /api/analysis/start`
- `POST /api/analysis/{task_id}/run`
- `GET /api/analysis/{task_id}`
- `GET /api/analysis/{task_id}/events`
- `GET /api/analysis/{task_id}/tool-logs`
- `POST /api/eval/run`
- `POST /api/eval/cases/run`
- `GET /api/llm/provider-status`
- `POST /api/llm/provider-smoke`
- `GET /api/project-status`
- `GET /demo`

Windows 示例：

```powershell
cd E:\bgagent1\backend
curl.exe -X POST -F "file=@data/samples/sales_orders.csv" http://127.0.0.1:8000/api/files/upload
```

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/api/project-status"
```

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/llm/provider-smoke"
```

全量测试：

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m pytest -q
```

## 当前真实边界

当前已经真实实现的 AI / Agent 相关部分是：

- `QwenClient`：真实 Tongyi Qianwen Provider 调用
- `MockLLMClient`：显式本地回退
- `knowledge_base.jsonl + keyword_retriever`：真实本地混合检索
- `business_context`：检索结果会写入任务状态并记录 `rag_retrieved` 事件
- `SessionStore`：Redis 可用时保存完整状态与细粒度 key，不可用时降级为 SQLite + 内存锁
- `LangGraph`：当前 `/api/analysis/{task_id}/run` 已通过包含 `route_next_step` 的最小状态流执行
- `match_fields + ToolResponse/Pydantic schema`：字段匹配阶段会产出结构化 `field_understanding`，其中 `analysis_type`、`candidate_fields`、`warnings`、`planned_tool_sequence` 已继续透出到 `GET /api/project-status`、`/demo` 和 `scripts/demo_mvp.ps1`，作为字段错配治理和结构约束的运行时证据
- `RuleScorer + fixed eval cases`：规则评分与固定 case 回归
- `GET /api/llm/provider-status` / `POST /api/llm/provider-smoke`：Provider 运行时诊断
- `GET /api/project-status`：项目运行总览
- `/demo`：极简真实 API 演示页

当前仍然没有实现的部分是：

- DockerSandbox
- 完整 React 前端
- 异步任务队列
- 生产级多 Provider 编排

## 面试讲解要点

- 为什么不能把整张表直接交给大模型做分析
- 为什么业务语义检索只负责增强，不负责 CSV 明细精确计算
- 为什么要把 DuckDB、工具调用、事件时间线、规则评分、provider 诊断和 project-status 放在同一条真实链路里
- 为什么真实 LLM 只负责目标理解、计划组织、报告表达和补充评审，而不直接替代数值计算
## DockerSandbox Runtime Evidence

- The repository now includes a real `DockerSandbox` execution path exposed as the controlled `advanced_code_execution` capability.
- Runtime diagnostics are available through `GET /api/sandbox/status`.
- Controlled execution is available through `POST /api/sandbox/execute`.
- `GET /api/project-status` and `/demo` surface sandbox runtime status and latest execution evidence.
- DockerSandbox remains a second-phase controlled execution capability and does not replace the main DuckDB and tool-driven deterministic analysis chain.
