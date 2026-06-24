# Resume Project Description

以下内容用于简历或项目介绍，表述边界严格限制在当前仓库已经真实实现的能力内。
如果需要把简历说法继续映射到具体代码、接口、脚本和测试证据，可继续查看 [RESUME_EVIDENCE_MAP.md](./RESUME_EVIDENCE_MAP.md)。

## 一句话版本

基于 FastAPI、LangGraph、DuckDB、SQLite 和 Tongyi Qianwen Provider 构建结构化表格分析 Agent，打通“CSV / Excel 上传 - 字段画像 - 业务语义检索 - 分析计划 - 受控工具执行 - 图表与报告生成 - 规则评估 - 过程追踪”的真实后端闭环，并提供 `/demo`、`/api/project-status` 与 `demo_mvp.ps1` 作为可验证的演示交付入口。

## 简历项目描述版本

- 基于 FastAPI 设计并实现结构化表格分析后端，支持 CSV / Excel 上传、字段画像生成、任务创建、任务执行与分析结果查询。
- 使用 LangGraph 编排“字段匹配 - 工具执行 - 结果校验 - 下一步路由 - 图表生成 - 报告生成 - 规则评估”的最小状态流，并通过 `route_next_step` 支持多指标问题的最小动态推进。
- 封装 pandas / DuckDB 与真实 Plotly 图表生成的受控分析工具，对外继续输出兼容持久化的 `plotly_spec`，并通过统一 `ToolResponse` 和 Pydantic schema 约束参数、返回值和错误信息，降低字段错配和结构漂移风险。
- 在受控工具链中补齐占比分析、趋势分析和基于 z-score 的异常检测能力，持续保持数值结论来自确定性聚合结果而非模型臆断。
- 设计可替换 `LLMClient` 抽象，完成 `QwenClient` 与 `MockLLMClient` 双实现，并通过 provider 工厂支持真实 Tongyi Qianwen 接入、缺少可用 API key 时的显式降级与本地回退。
- 将真实 LLM 接入到分析目标生成、分析计划生成、最终报告组织和补充型 `llm_judgement`，同时保持数值计算仍由 DuckDB / 工具链完成，避免模型直接编造结果。
- 构建本地 staged retrieval 模块，基于 JSONL 知识库实现显式 BM25 召回、embedding 向量召回、rerank 重排和 SQLite embedding cache，为字段语义理解和分析计划生成提供可验证的业务上下文增强。
- 设计 Redis 优先、SQLite 降级的会话状态存储方案，并将 `draft_report`、中间发现、业务上下文和 `context_checkpoint` 拆分为细粒度 key，增强过程恢复和追踪能力。
- 使用 SQLite 持久化文件元数据、任务状态、事件时间线、工具调用日志和评估结果，并通过固定 case 回归输出工具成功率、Trace 完整度、报告完整度与执行耗时等质量指标。
- 增加运行时可观测与交付能力，通过 `GET /api/llm/provider-status`、`POST /api/llm/provider-smoke`、`GET /api/project-status`、`GET /demo` 和 `scripts/demo_mvp.ps1` 支撑真实演示、provider 诊断与项目运行总览展示。

## 面试中可展开的工程点

- 为什么真实 LLM 只负责目标理解、计划组织、报告表达和补充评审，而不直接负责数值计算
- 为什么结构化表格分析必须把 DuckDB / pandas 工具链作为数值真相源
- 为什么要通过 `LLMClient` 抽象和 provider 工厂实现真实模型接入，而不是把模型调用写死在节点中
- 为什么 RAG 只负责语义增强而不替代 CSV 明细计算
- 为什么当前选择 JSONL + SQLite embedding cache 的 staged retrieval，而不是直接引入独立向量数据库
- 为什么要把事件时间线、规则评估、工具日志、provider 状态和 project-status 一起纳入主链，支撑可追踪、可验证的工程表达

## 当前不能过度声称的点

- 不能说已经实现完整 React 前端
- 不能说所有分析都由大模型自动完成
- 不能说项目已经是生产级多租户或高并发系统

## Redis Memory Runtime Evidence

- Real Redis memory is now implemented through `memory_context`, not only `analysis_state` persistence.
- The system stores `recent_turns` plus `summary_memory` for the same `file_id`.
- Recent turns follow a sliding window policy controlled by `MEMORY_MAX_RECENT_TURNS`.
- Older turns are compressed into summary memory text and surfaced as `summary_text`.
- `task_builder` passes `memory_context` into `generate_analysis_goal` and `generate_analysis_plan`.
- `GET /api/project-status` and `/demo` expose `recent_turn_count`, `summary_turn_count`, and `summary_text`.

## LLM-As-Judge Runtime Evidence

- The project now includes a real `LLM-as-Judge` layer rather than only a lightweight supplementary judgement flag.
- Judge outputs are persisted through `llm_judgement` with `judge_summary`, `judge_status`, and structured dimension results.
- The current dimension set includes `groundedness`, `completeness`, and `clarity`.
- Judge provider failures degrade explicitly to `judge_status = degraded` instead of failing the entire completed analysis task.
- `GET /api/project-status`, `/demo`, and `/api/eval/run` expose judge runtime evidence separately from deterministic rule scores.

## DockerSandbox Runtime Evidence

- The project now includes a real `DockerSandbox` execution path exposed as the controlled `advanced_code_execution` capability.
- Sandbox execution is available through `POST /api/sandbox/execute` and runtime diagnostics are exposed by `GET /api/sandbox/status`.
- Direct `POST /api/sandbox/execute` calls now persist the latest sandbox runtime evidence instead of relying only on indirect tool-log side effects.
- Latest persisted sandbox evidence includes classified failure codes such as `SANDBOX_SYNTAX_ERROR`, `SANDBOX_IMPORT_ERROR`, and `SANDBOX_PERMISSION_ERROR`.
- Sandbox demo execution now supports named templates such as `region_sales_summary` instead of only arbitrary inline Python.
- Sandbox timeout requests are capped by the configured runtime ceiling rather than accepted without boundary.
- `GET /api/project-status` and `/demo` surface sandbox runtime evidence and latest execution status.
- DockerSandbox is implemented as a second-phase controlled execution module and does not replace the main DuckDB and tool-driven deterministic analysis chain.
