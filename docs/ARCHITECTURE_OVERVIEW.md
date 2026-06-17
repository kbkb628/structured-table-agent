# Architecture Overview

本文档给出当前 MVP 的文字架构说明，所有模块都必须能在仓库中找到对应实现。

## 1. 总体链路

当前系统的真实链路是：

1. 用户上传 CSV
2. 服务端生成字段画像并持久化
3. 用户发起分析任务
4. 系统执行轻量 JSONL 关键词检索
5. `MockLLM` 生成分析目标和计划
6. LangGraph 驱动字段匹配、DuckDB 聚合、`validate_tool_result` 校验、`route_next_step` 显式路由、图表生成、报告生成和规则评分
7. 任务状态、事件时间线、工具调用日志和评估结果都写入 SQLite

## 2. 模块职责

### `app/api`

负责 HTTP 接口：

- `files.py`：上传文件与查询字段画像
- `analysis.py`：创建任务、执行任务、查询任务状态和事件
- `eval.py`：手动重跑规则评估

### `app/services`

负责共享服务逻辑：

- `analysis_runner.py`：封装任务执行入口
- `task_builder.py`：构造任务初始状态、启动事件和共享初始化流程

### `app/agent`

负责 LangGraph 状态流：

- `graph.py`：定义带 `validate_tool_result` 和 `route_next_step` 的最小状态图
- `nodes.py`：实现字段匹配、工具执行、工具结果校验、下一步路由、图表生成、报告生成和评估节点
- `state.py`：任务状态结构

### `app/tools`

负责确定性数据分析能力：

- `data_profile.py`：字段画像
- `match_fields.py`：字段匹配
- `duckdb_tools.py`：分组聚合
- `chart_tool.py`：柱状图配置生成
- `report_tool.py`：结构化报告生成

### `app/rag`

负责轻量业务语义增强：

- `knowledge_base.jsonl`：本地知识库
- `knowledge_loader.py`：知识加载
- `keyword_retriever.py`：关键词检索

### `app/llm`

负责可替换模型接口：

- `base.py`：`LLMClient`
- `mock_client.py`：`MockLLMClient`

当前真实运行默认使用 `MockLLMClient`，没有接入外部模型服务。

### `app/observability`

负责事件语义层：

- `trace_models.py`：事件常量和关键 trace 集合
- `event_logger.py`：事件记录、事件查询、状态事件回填

### `app/storage`

负责持久化：

- `database.py`：SQLite 表初始化
- `file_store.py`：文件元数据存取
- `analysis_store.py`：任务状态、事件、工具调用和评估结果存取

## 3. 数据持久化

当前 SQLite 包含以下真实表：

- `files`
- `analysis_tasks`
- `analysis_events`
- `tool_call_logs`
- `eval_results`

这与 `DEVELOPMENT_GUIDE.md` 的 MVP 存储边界保持一致。当前代码已经实现 `SessionStore`，会优先尝试 Redis；当 Redis 不可用或本地未安装依赖时，会显式降级到 SQLite 持久化并记录 `session_store_warning` 事件。若 Redis 可用，当前还会把 `draft_report`、`intermediate_findings` 和压缩后的 `context_checkpoint` 分别写入细粒度 key，并使用 `task_lock:{task_id}` 避免同一任务重复执行；Redis 不可用时则降级为进程内任务锁。每次状态持久化还会额外记录一次 `context_checkpoint_refreshed` 事件，用于追踪轻量上下文摘要的刷新时机。

## 4. 运行时状态流

任务启动阶段会构造统一状态字段：

- `analysis_goal`
- `business_context`
- `analysis_plan`
- `field_understanding`
- `tool_results`
- `chart_specs`
- `final_report`
- `eval_result`
- `events`
- `errors`
- `status`

运行阶段通过 LangGraph 推进：

- `match_fields` 会写入 `field_understanding` 和待执行的 `pending_metrics`
- `match_fields` 还会生成 `planned_tool_calls`，把当前分析问题对应的受控工具执行计划写入状态
- `execute_tools` 每次只消费一个 metric，并把最新结果暂存到状态
- `validate_tool_result` 会显式校验工具执行成功与结果非空，成功后再写入 `tool_results`
- `route_next_step` 会根据是否还有待执行 metric，决定回到 `execute_tools` 继续统计，或进入 `generate_charts`
- `generate_report` 前会先基于 `intermediate_findings` 和 `chart_specs` 生成 `draft_report`
- `generate_report` 工具返回前会通过 `FinalReport` Pydantic schema 校验最终报告结构
- 遇到不可执行字段匹配或空结果时会进入失败分支，并写入 `task_failed` 事件
- 关键事件 payload 当前还会补充 `node_input_summary`、`node_output_summary` 和 `tool_result_summary`，只保存轻量摘要而不写入完整大数据内容

## 5. 真实性边界

当前系统真实提供的是：

- CSV / Excel 上传与画像
- 规则驱动问题理解
- DuckDB 聚合
- Plotly 柱状图配置
- 结构化报告
- SQLite 事件和评估持久化

当前没有实现：

- 外部真实 LLM API
- embedding / BM25 / rerank
- 更完整的 Redis 会话记忆能力
- 异步队列
- DockerSandbox
- LLM-as-Judge
- 完整前端页面
