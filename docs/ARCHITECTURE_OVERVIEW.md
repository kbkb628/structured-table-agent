# Architecture Overview

本文档给出当前后端架构说明，所有模块都必须能在仓库中找到对应实现。

## 1. 总体链路

当前系统的真实链路是：

1. 用户上传 CSV / Excel
2. 服务端生成字段画像并持久化
3. 用户发起分析任务
4. 系统执行本地 JSONL 混合检索
5. `LLMClient` 生成分析目标和分析计划
6. LangGraph 驱动字段匹配、DuckDB 聚合、`validate_tool_result` 校验、`route_next_step` 路由、图表生成、报告生成和评估
7. 任务状态、事件时间线、工具调用日志和评估结果写入 SQLite / SessionStore

## 2. 模块职责

### `app/api`

负责 HTTP 接口：

- `files.py`：上传文件与查询字段画像
- `analysis.py`：创建任务、执行任务、查询任务状态、事件和工具日志
- `eval.py`：手动重跑规则评估与 fixed cases

### `app/services`

负责共享服务逻辑：

- `analysis_runner.py`：封装任务执行入口
- `task_builder.py`：构造任务初始状态、启动事件和共享初始化流程

### `app/agent`

负责 LangGraph 状态流：

- `graph.py`：定义带 `validate_tool_result` 与 `route_next_step` 的最小状态图
- `nodes.py`：实现字段匹配、工具执行、结果校验、下一步路由、图表生成、报告生成和评估节点
- `state.py`：任务状态结构

### `app/tools`

负责确定性数据分析能力：

- `data_profile.py`：字段画像
- `match_fields.py`：字段匹配
- `duckdb_tools.py`：分组聚合
- `chart_tool.py`：柱状图配置生成
- `report_tool.py`：结构化基础报告生成

### `app/rag`

负责轻量业务语义增强：

- `knowledge_base.jsonl`：本地知识库
- `knowledge_loader.py`：知识加载
- `keyword_retriever.py`：本地混合检索，包含关键词、短语命中、字段加权和 BM25 风格评分

### `app/llm`

负责可替换模型接口：

- `base.py`：`LLMClient`
- `mock_client.py`：`MockLLMClient`
- `qwen_client.py`：`QwenClient`
- `factory.py`：provider 工厂与配置校验

当前实现支持：

- `LLM_PROVIDER=qwen`
- `LLM_PROVIDER=mock`
- `LLM_ALLOW_FALLBACK=true|false`

### `app/observability`

负责事件语义层：

- `trace_models.py`：事件常量和关键 trace 集合
- `event_logger.py`：事件记录、事件查询、状态事件回填

### `app/storage`

负责持久化：

- `database.py`：SQLite 表初始化
- `file_store.py`：文件元数据存取
- `analysis_store.py`：任务状态、事件、工具调用和评估结果存取
- `session_store.py`：Redis 优先 / SQLite 降级的会话状态与任务锁

## 3. 数据持久化

当前 SQLite 包含以下真实表：

- `files`
- `analysis_tasks`
- `analysis_events`
- `tool_call_logs`
- `eval_results`

`SessionStore` 会优先尝试 Redis；当 Redis 不可用时，会显式降级到 SQLite 并记录 `session_store_warning`。若 Redis 可用，系统还会把 `draft_report`、`final_report`、`llm_judgement`、`intermediate_findings`、`business_context`、压缩后的 `context_checkpoint` 和 `task_lock` 分别写入细粒度 key。

## 4. 运行时状态流

任务启动阶段统一构造：

- `analysis_goal`
- `business_context`
- `analysis_plan`
- `field_understanding`
- `tool_results`
- `chart_specs`
- `draft_report`
- `final_report`
- `llm_judgement`
- `eval_result`
- `events`
- `errors`
- `status`

运行阶段通过 LangGraph 推进：

- `match_fields` 写入 `field_understanding`、`pending_metrics` 和 `planned_tool_calls`
- `execute_tools` 每次只消费一个 metric
- `validate_tool_result` 显式校验工具执行成功与结果非空
- `route_next_step` 决定继续执行下一轮统计还是进入图表阶段
- `generate_report` 先形成 `draft_report`
- `report_tool.generate_report` 形成工具侧基础结构化报告
- `LLMClient.generate_report` 形成最终 `final_report`
- `LLMClient.judge_report` 形成补充型 `llm_judgement`
- `evaluate_report` 持久化 `eval_result`

## 5. 真实性边界

当前系统真实提供的是：

- CSV / Excel 上传与画像
- 轻量 RAG 语义增强与本地混合检索
- LangGraph 多步状态流
- DuckDB 聚合与 Plotly 配置
- 结构化报告
- 真实 Tongyi Qianwen Provider 接入
- SQLite / Redis 状态持久化
- 规则评估与固定 case 回归

当前没有实现：

- embedding / 向量检索 / rerank
- DockerSandbox
- 完整前端页面
- 异步队列

需要特别强调：

- LLM 负责目标理解、计划生成、报告表达和补充 judgement
- 数值计算仍由确定性工具完成
- 因此项目是真实接入了 LLM，但不是“让大模型直接算整张表”
