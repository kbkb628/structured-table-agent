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
- SQLite 持久化：`files`、`analysis_tasks`、`analysis_events`、`tool_call_logs`、`eval_results`
- DuckDB 真实聚合工具：按品类、地区、渠道执行聚合分析
- Share 分析工具：按维度计算指标占比、贡献率和百分比
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

## 当前真实能力边界

当前可以真实声明已实现：

- CSV / Excel 上传与字段画像
- 从自然语言问题到工具执行的完整分析闭环
- 轻量 RAG 业务语义增强
- 本地混合检索 / BM25 风格语义增强
- LangGraph 多步状态流与最小动态路由
- pandas / DuckDB / Plotly 的受控工具链
- 占比分析工具与主链接入
- 真实 Tongyi Qianwen Provider 接入
- SQLite 持久化与 Redis 优先 / SQLite 降级
- 规则评分与固定 case 回归验证

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
- `business_context` 继续真实写入任务状态，并可通过 `GET /api/analysis/{task_id}` 查看
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
- 报告工具输出与 LLM 报告层最终都受 `FinalReport` schema 约束
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
- `keyword_retriever` 当前已升级为本地混合检索：
  - 关键词重叠打分
  - 短语命中加权
  - related_fields 字段加权
  - BM25 风格归一化评分
  - `score_breakdown` 检索打分明细

## 当前结论

- 如果按最初 MVP 要求看，项目主链路早已完成。
- 按当前“贴合简历表达”的目标看，项目现在已经跨过“真实 LLM 接入”这一条关键门槛。
- 现阶段剩余未实现内容主要是第二阶段增强，而不是当前主链缺口。

## 剩余增强方向

- 升级到 `embedding + 向量检索 + rerank`
- 增强 Redis 会话记忆和异步执行
- 引入 DockerSandbox
- 增强前端过程展示
- 扩展更多分析工具，如趋势分析、异常检测、占比分析
