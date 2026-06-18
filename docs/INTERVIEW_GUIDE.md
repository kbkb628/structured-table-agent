# Interview Guide

本文档用于面试时讲解当前项目，所有说法都应以仓库中的真实实现为准。

## 1. 项目目标

这个项目不是一个简单的 CSV 问答脚本，而是一个能体现 Agent 工程化思路的结构化表格分析后端：

- 有明确状态流
- 有确定性工具执行
- 有轻量业务语义增强
- 有任务状态与事件时间线
- 有规则评估与固定 case 回归
- 有真实 LLM Provider 接入

## 2. 为什么不是“把整张表直接扔给大模型”

核心原因是结构化分析里的精确计算必须交给确定性工具：

- CSV 明细统计需要可复现
- 聚合结果需要可追溯
- 报告里的数字必须能回到工具结果
- 模型负责目标理解、计划组织、表达和补充评审，不负责编造计算结果

当前实现里：

- 语义理解层：`QwenClient` / `MockLLMClient`
- 数据计算层：DuckDB / pandas 工具
- 报告数字来源：`tool_results`

## 3. 为什么要做可替换 LLM Provider

如果把模型调用直接写死在节点里，会带来三个问题：

- 无法在无外部依赖时稳定开发
- 无法在真实 Provider 和本地回退之间切换
- 无法把“模型能力边界”和“工具能力边界”分开

所以当前代码用了：

- `LLMClient` 抽象接口
- `QwenClient` 真实实现
- `MockLLMClient` 本地回退实现
- `get_llm_client()` provider 工厂
- `GET /api/llm/provider-status`
- `POST /api/llm/provider-smoke`

这能支撑一个真实、可验证的表达：项目已经接入 Tongyi Qianwen，并且可以通过接口和脚本检查当前 provider 解析结果、key 来源和最小 smoke 状态。

## 4. 为什么 RAG 只做增强，不做计算

当前项目里的 RAG 是本地 `knowledge_base.jsonl + keyword_retriever`，并且已经从纯关键词检索升级到本地混合检索，只解决：

- 指标口径解释
- 字段语义映射
- 分析模板提示

当前检索层包含：

- 关键词重叠打分
- 短语命中加权
- `related_fields` 字段加权
- BM25 风格归一化评分

它不负责：

- 从 CSV 明细里精确求值
- 替代 SQL / DuckDB 聚合

这样可以把“语义增强”和“精确计算”分层，避免职责混乱。

## 5. 为什么引入 LangGraph

引入 LangGraph 不是为了堆概念，而是为了让任务流转可见、可扩展、可验证。

当前最小图已经是一个带显式路由节点的可执行状态流：

- `load_task`
- `match_fields`
- `execute_tools`
- `validate_tool_result`
- `route_next_step`
- `generate_charts`
- `generate_report`
- `evaluate_report`

其中：

- `validate_tool_result` 负责把工具成功、失败、空结果分开处理
- `route_next_step` 负责在多指标问题下决定继续执行下一轮统计还是进入图表阶段
- 现在还能通过 `GET /api/project-status`、`/demo` 和 `demo_mvp.ps1` 直接看到 continue / finish 的路由摘要，而不只是口头说明有动态路由
- `generate_report` 先生成 `draft_report`，再由 LLM 层组织最终 `final_report`
- `evaluate_report` 同时写入规则评分和 `llm_judgement`

这说明当前项目已经不是“固定顺序脚本”，而是一个有明确状态语义和最小动态推进能力的 Agent 后端。

## 6. 为什么规则评估和 LLM judgement 要分开

当前项目里：

- `RuleScorer` 是主评估层
- `llm_judgement` 是补充评估层

这样拆分的原因是：

- 规则评分更稳定、可回归、可批量跑 fixed cases
- LLM judgement 更适合补充表达质量、贴题性、是否有发现
- 不能一上来就用 LLM judgement 替代全部评估，否则主链可验证性会变差

所以现在可以讲成：

- 规则评分保证工程可验证
- LLM judgement 提供模型视角的补充检查

## 7. 当前真实边界

面试中必须明确：

- 已经接入真实 Tongyi Qianwen Provider
- 默认可以通过 `LLM_PROVIDER=qwen` 切到真实模型
- 本地仍保留 `mock` 回退路径
- 当前 RAG 是 `knowledge_base.jsonl + keyword_retriever` 的本地混合检索实现，不是纯关键词版本
- 当前 SessionStore 会优先尝试 Redis，不可用时显式降级到 SQLite
- 当前已经实现 `draft_report`、`final_report`、`llm_judgement`、`business_context`、`intermediate_findings` 和 `context_checkpoint` 的 Redis 细粒度持久化与回填
- 即使 Redis 的主 `analysis_state` 快照缺失，也可以基于 SQLite 状态和细粒度 Redis key 恢复任务视图
- 这类恢复不会静默发生，而是会写入 `session_state_recovered` 事件，进入任务时间线
- 现在还可以通过 `GET /api/project-status`、`/demo` 和 `demo_mvp.ps1` 直接展示最近一次恢复的 `recovery_source`、`recovered_segments` 和 segment 数量
- 当前已经实现基于 FastAPI 返回的极简 `/demo` 演示页，用于串联上传、任务执行、Provider 诊断、固定评测和 project runtime overview
- 当前已经实现 `GET /api/project-status`，用于聚合 provider 解析、demo 可用性、session store runtime mode 和 SQLite 表行数
- `scripts/demo_mvp.ps1` 会跑真实演示链路，并输出 project status 摘要
- 当前没有实现 embedding / 向量检索 / rerank、DockerSandbox、完整 React 前端、异步队列

如果把没做的能力说成已经完成，会直接破坏项目可信度。

## 8. 如何证明这些说法不是纸面能力

当前仓库里已经有可直接展示的验证入口：

- `GET /demo`
- `GET /api/llm/provider-status`
- `POST /api/llm/provider-smoke`
- `GET /api/project-status`
- `POST /api/eval/cases/run`
- `scripts/demo_mvp.ps1`
- `scripts/qwen_provider_smoke.ps1`

讲解时可以强调：

- provider 能力不只停留在代码抽象上，还能通过接口和脚本做运行时诊断
- demo 不只是静态页面，而是基于真实后端接口拉取任务状态、事件和工具日志
- project runtime overview 能直接展示 SQLite 表行数、provider 状态以及当前 session store 是 Redis 还是 SQLite 降级，便于演示当前系统状态
- `demo_mvp.ps1` 还能直接输出 `project_status_provider`、`project_status_session_store_preferred_backend`、`project_status_session_store_active_backend`、`project_status_session_store_redis_available`、`project_status_session_store_degraded_to_sqlite`、`project_status_session_store_redis_url`、`project_status_session_store_warning_count`、`project_status_session_store_recovered_count`、`project_status_session_store_latest_warning_task_id`、`project_status_session_store_latest_warning_at`、`project_status_session_store_latest_recovered_task_id`、`project_status_session_store_latest_recovered_at`、`project_status_session_store_latest_recovered_recovery_source`、`project_status_session_store_latest_recovered_segment_count`、`project_status_session_store_latest_recovered_segments`、`project_status_latest_task_has_business_context`、`project_status_latest_task_has_context_checkpoint`、`project_status_latest_task_has_draft_report`、`project_status_latest_task_has_final_report`、`project_status_latest_task_has_eval_result`、`project_status_latest_task_eval_overall_score`、`project_status_latest_task_eval_suggestion_count`、`project_status_latest_task_eval_has_dimension_scores`、`project_status_latest_task_eval_schema_valid`、`project_status_latest_task_eval_tool_success_rate`、`project_status_latest_task_eval_tool_elapsed_ms_total`、`project_status_latest_task_eval_field_validity`、`project_status_latest_task_eval_chart_validity`、`project_status_latest_task_eval_report_completeness`、`project_status_latest_task_eval_trace_completeness`、`project_status_latest_task_pending_metric_count`、`project_status_latest_task_latest_event_type`、`project_status_latest_task_latest_event_at`、`project_status_latest_task_llm_issue_count`、`project_status_latest_task_route_decision_count`、`project_status_latest_task_continued_route_decision_count`、`project_status_latest_task_finished_route_decision_count`、`project_status_latest_task_latest_route_decision`、`project_status_latest_task_chart_spec_count`、`project_status_latest_task_key_finding_count`、`project_status_latest_task_next_step_count`、`project_status_latest_task_business_context_count`、`project_status_latest_task_top_business_context_score`、`project_status_latest_task_top_business_context_related_field_count`、`project_status_latest_task_top_business_context_has_score_breakdown`、`project_status_latest_task_top_business_context_keyword_score`、`project_status_latest_task_top_business_context_field_score`、`project_status_latest_task_top_business_context_phrase_score`、`project_status_latest_task_top_business_context_bm25_score`、`project_status_latest_task_checkpoint_current_step`、`project_status_latest_task_checkpoint_status`、`project_status_latest_task_checkpoint_pending_metric_count`、`project_status_latest_task_checkpoint_finding_count`、`project_status_latest_task_checkpoint_business_context_title_count`、`project_status_latest_task_checkpoint_business_context_titles`、`project_status_latest_task_checkpoint_latest_error_code`、`project_status_latest_task_analysis_goal`、`project_status_latest_task_analysis_plan_count`、`project_status_latest_task_current_step`、`project_status_latest_task_finding_count`、`project_status_latest_task_dimension_field`、`project_status_latest_task_match_analysis_type`、`project_status_latest_task_candidate_field_count`、`project_status_latest_task_match_warning_count`、`project_status_latest_task_planned_tool_sequence`、`project_status_latest_task_supported_by_tools`、`project_status_latest_task_has_findings`、`project_status_latest_task_tool_result_count`、`project_status_latest_task_retried_tool_result_count`、`project_status_latest_task_retry_attempts_total`、`project_status_latest_task_latest_tool_name`、`project_status_latest_task_total_tool_elapsed_ms`、`project_status_latest_task_error_count`、`project_status_latest_task_latest_error_message`、`project_status_latest_task_has_degradation`、`provider_smoke_error_message`、`fixed_eval_retried_tool_calls`、`fixed_eval_retry_attempts_total`、`fixed_eval_average_tool_elapsed_ms_total`、`fixed_eval_average_trace_completeness`、`fixed_eval_average_report_completeness`、`fixed_eval_average_chart_validity`、`fixed_eval_average_field_validity` 等字段，作为 fixed eval 质量指标和运行时诊断证据，便于当场说明系统当前可用性和结果质量
- 另外也可以继续指向 `project_status_demo_available`、`project_status_session_store_redis_available`、`project_status_session_store_degraded_to_sqlite`、`project_status_session_store_recovered_count`、`project_status_latest_task_has_llm_judgement`、`project_status_latest_task_tool_call_log_count`、`project_status_latest_task_eval_issue_count`、`project_status_latest_task_planned_tool_call_count`、`project_status_latest_task_event_count`、`project_status_latest_task_business_suggestion_count`、`project_status_latest_task_data_limitation_count`、`project_status_latest_task_top_business_context_title`、`project_status_latest_task_checkpoint_draft_report_status`、`project_status_latest_task_completed_step_count`、`project_status_latest_task_metric_count`、`project_status_latest_task_successful_tool_result_count`、`project_status_latest_task_failed_tool_result_count`、`project_status_latest_task_latest_retry_status`、`project_status_latest_task_latest_error_code`、`project_status_files` 和 `project_status_tasks` 这些脚本已输出的补充诊断字段

如果面试官追问“你怎么证明轻量 RAG 不是只返回一个分数”，现在也可以直接展示 `GET /api/project-status`、`/demo` 和 `demo_mvp.ps1` 里的 `project_status_latest_task_top_business_context_keyword_score`、`project_status_latest_task_top_business_context_field_score`、`project_status_latest_task_top_business_context_phrase_score`、`project_status_latest_task_top_business_context_bm25_score`。这些字段都来自本地 hybrid retriever 的 `score_breakdown`，说明关键词命中、字段对齐、短语命中和 BM25 风格归一化在运行时都是可拆解、可验证的。

如果面试官追问“你怎么证明 Redis 细粒度状态恢复和过程检查点不是口头描述”，现在也可以直接展示 `GET /api/project-status`、`/demo` 和 `demo_mvp.ps1` 里的 `project_status_latest_task_checkpoint_status`、`project_status_latest_task_checkpoint_pending_metric_count`、`project_status_latest_task_checkpoint_finding_count`、`project_status_latest_task_checkpoint_business_context_title_count`、`project_status_latest_task_checkpoint_business_context_titles`。这些字段都来自 SessionStore 持久化下来的 `context_checkpoint`，说明过程检查点不是隐藏在 Redis 内部的黑盒数据，而是可以对外验证的运行时事实。

如果面试官追问字段错配和结构漂移怎么控制，现在可以直接指向 `GET /api/project-status`、`/demo` 和 `demo_mvp.ps1` 里的 `project_status_latest_task_match_analysis_type`、`project_status_latest_task_candidate_field_count`、`project_status_latest_task_match_warning_count`、`project_status_latest_task_planned_tool_sequence`。这些字段都来自 `match_fields` 持久化下来的 `field_understanding`，说明 ToolResponse 与 Pydantic schema 约束过的结构化匹配结果在运行时仍然可见，而不是只停留在代码声明层。

如果面试官继续追问“你怎么证明规则评估不是纸面设计”，现在也可以直接展示 `GET /api/project-status`、`/demo` 和 `demo_mvp.ps1` 里的 `project_status_latest_task_eval_schema_valid`、`project_status_latest_task_eval_tool_success_rate`、`project_status_latest_task_eval_tool_elapsed_ms_total`、`project_status_latest_task_eval_field_validity`、`project_status_latest_task_eval_chart_validity`、`project_status_latest_task_eval_report_completeness`、`project_status_latest_task_eval_trace_completeness`。这些字段都来自真实持久化的 `eval_result`，说明 RuleScorer 的质量信号在运行时可见、可回放、可验。

## 9. 后续迭代方向

当前代码最合理的后续方向是：

- 升级到 embedding / 向量检索 / rerank
- 增强 Redis 会话记忆和异步执行
- 引入 DockerSandbox
- 补更完整的前端过程展示
- 在现有能力上继续扩展更细粒度的趋势分析与异常检测策略
