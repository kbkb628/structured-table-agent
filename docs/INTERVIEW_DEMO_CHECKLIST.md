# Interview Demo Checklist

本文用于面试时做最短演示路径，目标是在 2-5 分钟内用最少页面切换证明项目不是纸面设计，而是有真实后端闭环、真实 provider 接入、真实运行态诊断和真实评估指标。
如果演示前还没确认服务、provider 和脚本是否处于可展示状态，先按 [INTERVIEW_DEMO_PREFLIGHT.md](./INTERVIEW_DEMO_PREFLIGHT.md) 做一遍预检查。

## 最短演示路径

建议顺序固定为：

1. `GET /demo`
2. `GET /api/llm/provider-status`
3. `POST /api/llm/provider-smoke`
4. `GET /api/project-status`
5. `scripts/demo_mvp.ps1`

如果时间更紧，只保留：

1. `GET /demo`
2. `GET /api/project-status`
3. `scripts/demo_mvp.ps1`

## Step 1：打开 `/demo`

目的：

- 先证明项目不是只有后端接口说明，而是已经有可直接操作的真实演示入口
- 说明页面不是静态 mock，而是薄壳 demo，直接复用真实后端 API

建议说法：

- “这里的 `/demo` 不是单独做的一套假前端，它直接串真实上传、任务执行、provider 诊断、fixed eval 和 project runtime overview。”

建议观察点：

- 上传 CSV / Excel 的入口
- `LLM Provider Status`
- `Project Runtime Overview`
- `Latest Task Artifacts / Evaluation / Judgement / Context / Tools / Errors`
- `Fixed Eval Cases` 区块里的 case coverage 列表，可直接看到三条中文 MVP 验收问句
- 问题输入框下方的中文快捷按钮，可一键填入三条中文 MVP 验收问句
- 问题输入框下方也覆盖六条英文演示问题快捷按钮，其中包含 `analyse sales by region`

## Step 2：打开 `GET /api/llm/provider-status`

目的：

- 证明项目里不是只留了 `LLMClient` 抽象，而是真的把 Tongyi Qianwen provider 接进来了
- 证明 provider 选择、key 来源、fallback 和 smoke readiness 都能在运行时被检查

建议说法：

- “我没有把模型调用写死在节点里，而是做了 provider 工厂。这里可以直接看到当前 provider、key 来源和 provider 是否 ready。”

建议观察字段：

- `provider`
- `allow_fallback`
- `has_api_key`
- `api_key_source`
- `diagnostics.provider_supported`
- `diagnostics.smoke_ready`

## Step 3：执行 `POST /api/llm/provider-smoke`

目的：

- 证明真实 LLM 调用链不是停留在配置层，而是能做最小真实调用
- 说明 smoke 接口不会创建业务任务，只负责 provider 诊断

建议说法：

- “这个接口不跑完整业务任务，只做最小 provider 调用，所以能快速证明真实模型链路通不通。”

建议观察字段：

- `ok`
- `client_type`
- `analysis_goal`
- `error_type`
- `error_message`

## Step 4：打开 `GET /api/project-status`

目的：

- 证明 project runtime overview 是真实运行态聚合，不是手写描述
- 一次性展示 LangGraph 路由、RAG 分数拆解、Redis/SQLite 状态、latest task 产物和 fixed eval 指标

建议说法：

- “这是我专门做的运行态聚合接口，把 provider、demo、session store、latest task 和 SQLite 表统计统一拉平，便于演示和自检。”

最值得直接指出的字段：

- LangGraph / 规划链路
  - `project_status_latest_task_analysis_goal`
  - `project_status_latest_task_analysis_plan_count`
  - `project_status_latest_task_latest_route_decision`
  - `project_status_latest_task_planned_tool_call_count`
- RAG / 业务语义增强
  - `project_status_latest_task_top_business_context_bm25_score`
  - `project_status_latest_task_top_business_context_embedding_score`
  - `project_status_latest_task_top_business_context_rerank_score`
  - `project_status_latest_task_top_business_context_retrieval_sources`
  - `project_status_latest_task_top_business_context_keyword_score`
  - `project_status_latest_task_top_business_context_field_score`
- Session / 恢复能力
  - `project_status_session_store_active_backend`
  - `project_status_session_store_degraded_to_sqlite`
  - `project_status_latest_task_checkpoint_status`
  - `project_status_latest_task_checkpoint_pending_metric_count`
- 评估 / 质量信号
  - `project_status_latest_task_eval_tool_success_rate`
  - `project_status_latest_task_eval_trace_completeness`
  - `project_status_latest_task_eval_report_completeness`

## Step 5：运行 `scripts/demo_mvp.ps1`

目的：

- 用一个 repo 内脚本跑通固定样例链路
- 证明这些运行态字段不只在网页里可见，也能沉淀成脚本化交付证据

建议说法：

- “这个脚本会上传样例 CSV，跑支持的 demo 问题，查询 provider diagnostics、project runtime overview 和 fixed eval，并输出结构化摘要。”

最值得直接指出的字段：

- `project_status_latest_task_analysis_goal`
- `project_status_latest_task_latest_route_decision`
- `project_status_latest_task_top_business_context_bm25_score`
- `project_status_latest_task_top_business_context_embedding_score`
- `project_status_latest_task_top_business_context_rerank_score`
- `project_status_latest_task_checkpoint_status`
- `fixed_eval_pass_rate`
- `fixed_eval_case_ids`
- `fixed_eval_questions`

## 2 分钟版本

按下面顺序说即可：

1. 打开 `/demo`，说明这不是静态 mock，而是真实后端薄壳演示页。
2. 打开 `GET /api/llm/provider-status` 或 `POST /api/llm/provider-smoke`，证明 Tongyi Qianwen 已真实接入。
3. 打开 `GET /api/project-status`，指出 `project_status_latest_task_analysis_goal`、`project_status_latest_task_latest_route_decision`、`project_status_latest_task_top_business_context_bm25_score`、`project_status_latest_task_top_business_context_embedding_score`、`project_status_latest_task_top_business_context_rerank_score`、`project_status_latest_task_checkpoint_status`。
4. 最后展示 `scripts/demo_mvp.ps1` 输出里的 `fixed_eval_pass_rate`，说明不是只有流程，还有固定 case 质量回归。

## 5 分钟版本

按下面顺序说即可：

1. `/demo`：先讲整体闭环。
2. `provider-status` + `provider-smoke`：讲真实 provider 接入和运行时诊断。
3. `project-status`：讲 LangGraph、RAG、session store 和 latest task 运行态。
4. `demo_mvp.ps1`：讲脚本化演示交付和 fixed eval。
5. 如果面试官继续追问，再回到 [RESUME_EVIDENCE_MAP.md](./RESUME_EVIDENCE_MAP.md) 按条目展开代码和测试证据。

## 不要现场说过头的点

- 不要把当前实现夸大成独立向量数据库或分布式检索平台
- 不要说已经实现 DockerSandbox
- 不要说已经实现完整 React 前端
- 不要说所有数值结论都是模型直接算出来的
