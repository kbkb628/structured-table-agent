# Resume Evidence Map

本文用于把简历中的项目说法直接映射到当前仓库里的真实代码证据、演示证据和测试证据，避免后续表述漂移。

## 使用方式

- 面试前先用 [RESUME_PROJECT_DESCRIPTION.md](./RESUME_PROJECT_DESCRIPTION.md) 组织表述
- 需要快速走一遍现场演示时，直接打开 [INTERVIEW_DEMO_CHECKLIST.md](./INTERVIEW_DEMO_CHECKLIST.md)
- 被追问“这是不是只写在文档里”时，直接回到本文对应条目
- 所有说法都应落在“代码证据 + 演示证据 + 测试证据”三层同时成立的范围内

## 证据映射

### 1. 简历说法：支持 CSV / Excel 上传、字段画像生成、任务创建、任务执行与分析结果查询

- 代码证据
  - `backend/app/api/files.py`
  - `backend/app/api/analysis.py`
  - `backend/app/services/task_builder.py`
  - `backend/app/tools/data_profile.py`
- 演示证据
  - `GET /demo`
  - `POST /api/files/upload`
  - `POST /api/analysis/start`
  - `POST /api/analysis/{task_id}/run`
  - `GET /api/analysis/{task_id}`
- 测试证据
  - `backend/tests/test_files_api.py`
  - `backend/tests/test_analysis_api.py`
  - 其中 `backend/tests/test_analysis_api.py` 已覆盖 `DEVELOPMENT_GUIDE.md` 中三条中文 MVP 验收问句的真实 HTTP 闭环

### 2. 简历说法：使用 LangGraph 编排最小状态流，并通过 `route_next_step` 支持多指标问题的最小动态推进

- 代码证据
  - `backend/app/agent/graph.py`
  - `backend/app/agent/nodes.py`
  - `backend/app/agent/state.py`
- 演示证据
  - `GET /api/project-status`
  - `GET /demo`
  - `scripts/demo_mvp.ps1`
  - 可直接观察 `project_status_latest_task_route_decision_count`
  - 可直接观察 `project_status_latest_task_continued_route_decision_count`
  - 可直接观察 `project_status_latest_task_finished_route_decision_count`
  - 可直接观察 `project_status_latest_task_latest_route_decision`
- 测试证据
  - `backend/tests/test_agent_graph.py`
  - `backend/tests/test_analysis_runner.py`

### 3. 简历说法：通过统一 `ToolResponse`、Pydantic schema 和 Plotly 风格图表配置约束参数、返回值和错误信息，降低字段错配和结构漂移风险

- 代码证据
  - `backend/app/schemas/tool_schema.py`
  - `backend/app/tools/registry.py`
  - `backend/app/tools/match_fields.py`
  - `backend/app/tools/chart_tool.py`
  - `backend/app/tools/report_tool.py`
- 演示证据
  - `GET /api/project-status`
  - `GET /demo`
  - `scripts/demo_mvp.ps1`
  - 图表结果当前以 `plotly_spec` 的结构化配置形式暴露，而不是依赖前端单独拼接图表字段
  - 可直接观察 `project_status_latest_task_match_analysis_type`
  - 可直接观察 `project_status_latest_task_candidate_field_count`
  - 可直接观察 `project_status_latest_task_match_warning_count`
  - 可直接观察 `project_status_latest_task_planned_tool_sequence`
- 测试证据
  - `backend/tests/test_match_fields.py`
  - `backend/tests/test_tool_registry.py`
  - `backend/tests/test_chart_and_report_tools.py`

### 4. 简历说法：补齐占比分析、趋势分析和基于 z-score 的异常检测能力，并保持数值结论来自确定性工具链

- 代码证据
  - `backend/app/tools/share_tool.py`
  - `backend/app/tools/trend_tool.py`
  - `backend/app/tools/anomaly_tool.py`
  - `backend/app/tools/duckdb_tools.py`
- 演示证据
  - `POST /api/analysis/start`
  - `POST /api/analysis/{task_id}/run`
  - `POST /api/eval/cases/run`
  - `scripts/demo_mvp.ps1`
- 测试证据
  - `backend/tests/test_tool_registry.py`
  - `backend/tests/test_anomaly_tool.py`
  - `backend/tests/test_analysis_runner.py`
  - `backend/tests/test_analysis_api.py`

### 5. 简历说法：设计可替换 `LLMClient` 抽象，完成 `QwenClient` 与 `MockLLMClient` 双实现，并通过 provider 工厂支持真实 Tongyi Qianwen 接入，以及在缺少可用 API key 时按配置执行显式本地回退

- 代码证据
  - `backend/app/llm/base.py`
  - `backend/app/llm/qwen_client.py`
  - `backend/app/llm/mock_client.py`
  - `backend/app/llm/factory.py`
  - `backend/app/api/llm.py`
- 演示证据
  - `GET /api/llm/provider-status`
  - `POST /api/llm/provider-smoke`
  - `scripts/qwen_provider_smoke.ps1`
  - `GET /api/project-status`
- 测试证据
  - `backend/tests/test_qwen_client.py`
  - `backend/tests/test_llm_provider_factory.py`
  - `backend/tests/test_llm_api.py`

### 6. 简历说法：将真实 LLM 接入到分析目标生成、分析计划生成、最终报告组织和补充型 `llm_judgement`

- 代码证据
  - `backend/app/services/task_builder.py`
  - `backend/app/agent/nodes.py`
  - `backend/app/llm/qwen_client.py`
  - `backend/app/llm/mock_client.py`
- 演示证据
  - `GET /api/project-status`
  - `GET /demo`
  - `scripts/demo_mvp.ps1`
  - 可直接观察 `project_status_latest_task_analysis_goal`
  - 可直接观察 `project_status_latest_task_analysis_plan_count`
  - 可直接观察 `project_status_latest_task_has_llm_judgement`
  - 可直接观察 `project_status_latest_task_judgement_issue_count`
- 测试证据
  - `backend/tests/test_task_builder.py`
  - `backend/tests/test_analysis_runner.py`
  - `backend/tests/test_analysis_api.py`

### 7. 简历说法：构建本地混合检索模块，基于 JSONL 知识库实现关键词、短语命中、字段加权和 BM25 风格评分

- 代码证据
  - `backend/app/rag/knowledge_base.jsonl`
  - `backend/app/rag/knowledge_loader.py`
  - `backend/app/rag/keyword_retriever.py`
- 演示证据
  - `GET /api/project-status`
  - `GET /demo`
  - `scripts/demo_mvp.ps1`
  - 可直接观察 `project_status_latest_task_top_business_context_has_score_breakdown`
  - 可直接观察 `project_status_latest_task_top_business_context_keyword_score`
  - 可直接观察 `project_status_latest_task_top_business_context_field_score`
  - 可直接观察 `project_status_latest_task_top_business_context_phrase_score`
  - 可直接观察 `project_status_latest_task_top_business_context_bm25_score`
- 测试证据
  - `backend/tests/test_keyword_retriever.py`
  - `backend/tests/test_project_status_api.py`

### 8. 简历说法：设计 Redis 优先、SQLite 降级的会话状态存储方案，并通过 `context_checkpoint` 等细粒度 key 增强过程恢复和追踪能力

- 代码证据
  - `backend/app/storage/session_store.py`
  - `backend/app/observability/event_logger.py`
  - `backend/app/api/project_status.py`
- 演示证据
  - `GET /api/project-status`
  - `GET /demo`
  - `scripts/demo_mvp.ps1`
  - 可直接观察 `project_status_session_store_active_backend`
  - 可直接观察 `project_status_session_store_degraded_to_sqlite`
  - 可直接观察 `project_status_session_store_latest_recovered_recovery_source`
  - 可直接观察 `project_status_session_store_latest_recovered_segments`
  - 可直接观察 `project_status_latest_task_checkpoint_status`
  - 可直接观察 `project_status_latest_task_checkpoint_pending_metric_count`
- 测试证据
  - `backend/tests/test_session_store.py`
  - `backend/tests/test_project_status_api.py`
  - `backend/tests/test_analysis_api.py`

### 9. 简历说法：使用 SQLite 持久化文件元数据、任务状态、事件时间线、工具调用日志和评估结果，并通过固定 case 回归输出质量指标

- 代码证据
  - `backend/app/storage/database.py`
  - `backend/app/storage/models.py`
  - `backend/app/storage/analysis_store.py`
  - `backend/app/eval/rule_scorer.py`
  - `backend/app/eval/eval_cases.py`
- 演示证据
  - `GET /api/project-status`
  - `POST /api/eval/cases/run`
  - `GET /demo`
  - `scripts/demo_mvp.ps1`
  - 可直接观察 `project_status_files`
  - 可直接观察 `project_status_tasks`
  - 可直接观察 `project_status_analysis_events`
  - 可直接观察 `project_status_tool_call_logs`
  - 可直接观察 `project_status_eval_results`
  - 可直接观察 `fixed_eval_pass_rate`
  - 可直接观察 `fixed_eval_average_trace_completeness`
  - 可直接观察 `fixed_eval_average_report_completeness`
- 测试证据
  - `backend/tests/test_analysis_store.py`
  - `backend/tests/test_rule_scorer.py`
  - `backend/tests/test_eval_cases.py`

### 10. 简历说法：增加运行时可观测与交付能力，通过 provider 诊断、project runtime overview 和 demo 脚本支撑真实演示

- 代码证据
  - `backend/app/api/llm.py`
  - `backend/app/api/project_status.py`
  - `backend/app/api/demo.py`
  - `scripts/demo_mvp.ps1`
  - `scripts/qwen_provider_smoke.ps1`
- 演示证据
  - `GET /api/llm/provider-status`
  - `POST /api/llm/provider-smoke`
  - `GET /api/project-status`
  - `GET /demo`
  - `scripts/demo_mvp.ps1`
- 测试证据
  - `backend/tests/test_demo_page.py`
  - `backend/tests/test_demo_script_consistency.py`
  - `backend/tests/test_delivery_docs.py`

## 不能越界的说法

- 不能说已经实现 embedding / 向量检索 / rerank
- 不能说已经实现 DockerSandbox
- 不能说已经实现完整 React 前端
- 不能说所有分析结论都由 LLM 自动完成
- 不能说系统已经是生产级多租户或高并发架构

## 建议的面试使用顺序

1. 先用 [RESUME_PROJECT_DESCRIPTION.md](./RESUME_PROJECT_DESCRIPTION.md) 讲一句话版本和项目描述版本
2. 再用 [INTERVIEW_GUIDE.md](./INTERVIEW_GUIDE.md) 讲“为什么这么设计”
3. 用 [INTERVIEW_DEMO_CHECKLIST.md](./INTERVIEW_DEMO_CHECKLIST.md) 走最短演示路径
4. 被追问真实性时，回到本文按“简历说法 -> 代码证据 -> 演示证据 -> 测试证据”逐条展开
