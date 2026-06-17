# Architecture Overview

本文档给出当前 MVP 的文字架构说明，所有模块都必须能在仓库中找到对应实现。

## 1. 总体链路

当前系统的真实链路是：

1. 用户上传 CSV
2. 服务端生成字段画像并持久化
3. 用户发起分析任务
4. 系统执行轻量 JSONL 关键词检索
5. `MockLLM` 生成分析目标和计划
6. LangGraph 驱动字段匹配、DuckDB 聚合、图表生成、报告生成和规则评分
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

- `graph.py`：定义最小线性图
- `nodes.py`：实现字段匹配、工具执行、图表生成、报告生成和评估节点
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

这与 `DEVELOPMENT_GUIDE.md` 的 MVP 存储边界保持一致，尚未引入 Redis。

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

运行阶段通过 LangGraph 顺序推进，遇到不可执行字段匹配或空结果时会进入失败分支，并写入 `task_failed` 事件。

## 5. 真实性边界

当前系统真实提供的是：

- CSV 上传与画像
- 规则驱动问题理解
- DuckDB 聚合
- Plotly 柱状图配置
- 结构化报告
- SQLite 事件和评估持久化

当前没有实现：

- 外部真实 LLM API
- embedding / BM25 / rerank
- Redis 记忆
- 异步队列
- DockerSandbox
- LLM-as-Judge
- 完整前端页面
