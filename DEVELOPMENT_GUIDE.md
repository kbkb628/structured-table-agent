# 面向结构化表格数据的多步骤分析与报告生成智能体：开发指导文档

本文档用于指导新的开发对话在 `E:\bgagent1` 目录下开展项目开发。新对话必须先阅读本文档，再进行任何代码生成或文件创建。

项目目标不是做一个炫技 Demo，而是做一个能支撑简历和面试表达的工程化 AI Agent 项目。开发过程中必须优先保证主链路真实可跑，再逐步加入 Agent、RAG、记忆、评估和可观测。

---

## 1. 项目定位

项目名称：

```text
面向结构化表格数据的多步骤分析与报告生成智能体
```

面向岗位：

```text
AI 应用开发 / Agent 工程化 / RAG / Tool Use / 后端落地
```

核心场景：

```text
用户上传 CSV / Excel 企业结构化数据，并输入自然语言分析问题。
系统自动完成字段理解、业务语义检索、分析计划生成、工具调用、图表生成、报告输出和质量评估。
```

一句话介绍：

```text
以 FastAPI 提供数据分析服务接口，以 LangGraph 编排 Agent 状态流，以 Pydantic 约束模型输出和工具参数，以 pandas / DuckDB / Plotly 封装确定性数据分析工具，以轻量 RAG 引入企业字段和指标口径语义，以 Redis / SQLite 保存分析状态和执行事件，并通过规则评分器对 Agent 过程和报告质量进行评估。
```

项目不是：

```text
不是简单 CSV 问答。
不是把整张表塞进大模型 prompt。
不是 Notebook 脚本。
不是纯前端页面。
不是只展示最终答案的黑盒工具。
```

项目应该体现：

```text
Agent 状态流
Tool Use
结构化输出
RAG 业务语义增强
多轮状态记忆
失败治理
事件 Trace
规则评估
后端服务化落地
```

---

## 2. 当前已确认开发决策

用户已经确认以下方案：

```text
1B：先设计可替换 LLM Provider，开发时可用 MockLLM，后续接真实 API。
2B：第一版以后端 API + Swagger / 极简页面为主。
3A：第一版聚焦销售订单数据。
4B：第一版做轻量本地知识库检索，后续升级 embedding + BM25 + rerank。
5B：DockerSandbox 放第二阶段，不进入 3-5 天 MVP 主线。
6B：SQLite + Redis。
7C：事件记录 + 前端轮询展示 Agent 执行过程。
8A：3-5 天做出 MVP。
```

重要边界：

```text
3-5 天 MVP 只要求主链路真实可跑，不要求完整企业级实现。
RAG、Eval、Trace 要做轻量但真实版本。
DockerSandbox、高级 RAG、完整 React 前端、真实 LLM-as-Judge 放第二阶段。
```

---

## 3. MVP 成功标准

MVP 必须跑通以下完整流程：

```text
上传销售订单 CSV
-> 生成字段画像
-> 输入自然语言问题
-> 轻量 RAG 召回业务语义
-> Agent 生成分析目标和分析计划
-> 调用 pandas / DuckDB 工具执行统计
-> 生成 Plotly 图表配置
-> 生成结构化分析报告
-> 记录每一步事件 Trace
-> 规则评分器输出质量评估结果
-> 可通过 API 查询任务状态、事件、报告和评估结果
```

MVP 结束时必须能演示以下三个问题：

```text
分析各品类销售额 Top5，并给出业务建议。
分析各地区销售额对比，并生成图表。
分析不同渠道的订单数量和销售额表现。
```

MVP 必须真实完成：

```text
真实文件上传。
真实 CSV 解析。
真实字段画像。
真实 pandas / DuckDB 计算。
真实 ToolResponse 返回。
真实 Agent 状态字段流转。
真实轻量知识库检索。
真实事件记录。
真实规则评分。
```

MVP 不要求完成：

```text
不要求完整 React 前端。
不要求登录权限。
不要求多租户。
不要求高并发队列。
不要求 DockerSandbox。
不要求真实向量数据库。
不要求完整 embedding + BM25 + rerank。
不要求真实 LLM-as-Judge。
```

---

## 4. 技术栈

第一阶段 MVP 技术栈：

```text
后端框架：FastAPI
Agent 编排：LangGraph
结构化校验：Pydantic
数据处理：pandas
SQL 分析：DuckDB
图表配置：Plotly
持久化：SQLite
短期状态：Redis
轻量 RAG：本地 JSONL 知识库 + 关键词检索
LLM 接入：可替换 LLM Provider，第一版使用 MockLLM
事件记录：SQLite events 表 + API 查询
前端展示：Swagger / 极简 HTML 页面
包管理：优先使用 uv 或 pip
部署预留：Docker / Docker Compose 第二阶段补充
```

第二阶段扩展技术：

```text
真实 LLM API：DeepSeek / OpenAI Compatible / 通义千问等
RAG 升级：embedding + BM25 + rerank
向量存储：pgvector / Elasticsearch / Chroma / FAISS 任选其一
记忆增强：Redis 会话摘要、任务锁、中间结果缓存
评估增强：LLM-as-Judge
可观测增强：Trace 可视化、Langfuse / OpenTelemetry 可选
前端增强：React + Vite
沙箱增强：DockerSandbox 受控代码执行
```

---

## 5. 推荐目录结构

开发时应尽量按以下结构创建项目：

```text
E:\bgagent1
  backend
    app
      main.py
      api
        files.py
        analysis.py
        events.py
        eval.py
      core
        config.py
        exceptions.py
      schemas
        file_schema.py
        analysis_schema.py
        tool_schema.py
        report_schema.py
        event_schema.py
      storage
        database.py
        models.py
        file_store.py
        session_store.py
      llm
        base.py
        mock_client.py
        prompt_templates.py
      agent
        state.py
        graph.py
        nodes.py
        planner.py
      tools
        base.py
        registry.py
        data_profile.py
        duckdb_tools.py
        dataframe_tools.py
        chart_tool.py
        report_tool.py
      rag
        knowledge_loader.py
        keyword_retriever.py
        knowledge_base.jsonl
      eval
        rule_scorer.py
        eval_cases.py
      observability
        event_logger.py
        trace_models.py
    data
      uploads
      samples
    tests
    README.md
```

模块职责：

```text
api：HTTP 接口。
schemas：Pydantic 请求、响应、状态和工具结构。
storage：SQLite、文件存储、Redis 会话状态。
llm：可替换模型调用接口。
agent：LangGraph 状态流与节点。
tools：受控数据分析工具。
rag：轻量知识库和检索。
eval：规则评分与固定 Case。
observability：事件、Trace、日志。
data：上传文件和演示数据。
tests：接口、工具和规则评分测试。
```

---

## 6. 核心设计原则

### 6.1 不允许假功能

禁止：

```text
禁止假上传。
禁止假工具调用。
禁止假数据库持久化。
禁止假 RAG 结果。
禁止把模型编造的数字写进报告。
禁止在 README 或简历表述中把未完成能力写成已完成。
```

允许：

```text
允许 MockLLM，但必须明确它是可替换 LLM Provider 的本地实现。
允许轻量 RAG，但必须真实从 JSONL 知识库检索。
允许 Redis 缺失时降级到 SQLite / 内存，但必须在代码和 README 中明确说明。
允许第二阶段预留 DockerSandbox，但不得在 MVP 中声称已实现。
```

### 6.2 模型和工具职责边界

大模型负责：

```text
理解用户目标。
生成分析计划。
选择工具。
组织中间发现。
生成自然语言报告。
评价报告质量。
```

确定性工具负责：

```text
读取数据。
字段识别。
缺失率统计。
筛选。
聚合。
排序。
指标计算。
图表数据生成。
```

RAG 负责：

```text
字段含义解释。
指标口径说明。
业务术语映射。
分析方法模板。
```

RAG 不负责：

```text
不负责从 CSV 明细中查具体数值。
不负责代替 SQL / pandas 做精确计算。
```

### 6.3 先闭环再增强

开发顺序必须遵循：

```text
真实数据链路
-> 工具封装
-> Agent 状态流
-> 轻量 RAG
-> 事件 Trace
-> 规则 Eval
-> 文档与演示
```

不要反过来先做复杂 RAG、复杂前端或 DockerSandbox。

---

## 7. API 契约

开发前必须冻结以下接口。后续如需改动，必须同步更新本文档和前端调用。

### 7.1 上传文件

```text
POST /api/files/upload
```

请求：

```text
multipart/form-data
file: csv 文件
```

响应：

```json
{
  "file_id": "file_xxx",
  "filename": "sales_orders.csv",
  "row_count": 1000,
  "column_count": 10,
  "columns": [
    {
      "name": "product_category",
      "type": "string",
      "missing_rate": 0.0,
      "sample_values": ["办公用品", "电子产品"],
      "unique_count": 8
    }
  ],
  "created_at": "2026-06-08T18:00:00"
}
```

### 7.2 查询字段画像

```text
GET /api/files/{file_id}/profile
```

响应：

```json
{
  "file_id": "file_xxx",
  "filename": "sales_orders.csv",
  "row_count": 1000,
  "column_count": 10,
  "columns": [],
  "created_at": "2026-06-08T18:00:00"
}
```

### 7.3 创建分析任务

```text
POST /api/analysis/start
```

请求：

```json
{
  "file_id": "file_xxx",
  "question": "分析各品类销售额 Top5，并给出业务建议"
}
```

响应：

```json
{
  "task_id": "task_xxx",
  "status": "created",
  "analysis_goal": "比较不同品类的销售额表现，找出销售额最高的品类并生成建议",
  "analysis_plan": [
    "识别品类字段和销售额字段",
    "按品类聚合销售额",
    "按销售额降序取 Top5",
    "生成柱状图",
    "生成结构化报告"
  ]
}
```

### 7.4 执行分析任务

```text
POST /api/analysis/{task_id}/run
```

响应：

```json
{
  "task_id": "task_xxx",
  "status": "completed",
  "completed_steps": [],
  "intermediate_findings": [],
  "tool_results": [],
  "chart_specs": [],
  "final_report": {},
  "eval_result": {},
  "errors": []
}
```

### 7.5 查询完整任务状态

```text
GET /api/analysis/{task_id}
```

响应为完整 Agent 状态，字段见第 8 节。

### 7.6 查询事件时间线

```text
GET /api/analysis/{task_id}/events
```

响应：

```json
{
  "task_id": "task_xxx",
  "events": [
    {
      "event_id": "evt_xxx",
      "event_type": "tool_called",
      "node": "execute_tool",
      "message": "调用 groupby_aggregate 工具",
      "payload": {},
      "created_at": "2026-06-08T18:01:00"
    }
  ]
}
```

### 7.7 运行规则评估

```text
POST /api/eval/run
```

MVP 可以只支持固定 Case 或指定 `task_id`。

---

## 8. Agent 状态字段

状态字段必须稳定。开发过程中不要随意改名。

```json
{
  "task_id": "任务 ID",
  "file_id": "文件 ID",
  "question": "用户原始问题",
  "analysis_goal": "归一化后的分析目标",
  "file_profile": "字段画像、行数、列数、缺失率、样例值",
  "field_understanding": "字段匹配与字段含义理解",
  "business_context": "轻量 RAG 检索到的业务上下文",
  "analysis_plan": "分析计划",
  "current_step": "当前执行步骤",
  "completed_steps": "已完成步骤",
  "intermediate_findings": "中间发现",
  "tool_results": "工具调用结果",
  "chart_specs": "图表配置",
  "draft_report": "报告草稿",
  "final_report": "最终报告",
  "eval_result": "评估结果",
  "events": "执行事件",
  "errors": "错误和降级记录",
  "status": "created/running/completed/failed"
}
```

字段说明：

```text
analysis_goal：让系统明确用户到底想分析什么。
file_profile：让 Agent 知道数据结构和字段可用性。
field_understanding：记录字段匹配结果，避免模型凭空选择字段。
business_context：保存 RAG 召回的业务语义，用于辅助计划生成。
analysis_plan：体现 Agent 的任务规划。
intermediate_findings：体现多步骤分析和动态推进。
tool_results：让最终报告中的数字可追溯。
errors：支撑失败治理和降级输出。
eval_result：支撑持续优化。
events：支撑过程回放和前端时间线展示。
```

---

## 9. LangGraph 工作流

MVP 工作流建议：

```text
start
  -> profile_dataset_node
  -> understand_goal_node
  -> retrieve_business_context_node
  -> generate_plan_node
  -> match_fields_node
  -> execute_tool_node
  -> validate_tool_result_node
  -> generate_chart_node
  -> generate_report_node
  -> evaluate_report_node
  -> end
```

各节点职责：

```text
profile_dataset_node：读取文件画像。
understand_goal_node：用 MockLLM / LLM 生成 analysis_goal。
retrieve_business_context_node：从本地知识库召回字段解释、指标口径、分析模板。
generate_plan_node：生成结构化 analysis_plan。
match_fields_node：根据问题、字段画像和业务上下文匹配维度字段和指标字段。
execute_tool_node：调用 pandas / DuckDB 工具。
validate_tool_result_node：检查工具结果是否为空、字段是否合法、是否需要降级。
generate_chart_node：生成 Plotly 图表配置。
generate_report_node：生成结构化报告。
evaluate_report_node：运行规则评分器。
```

MVP 可以先固定执行一轮工具链。第二阶段再增强为循环：

```text
execute_tool_node
-> validate_tool_result_node
-> route_next_step_node
-> execute_tool_node 或 generate_chart_node
```

`route_next_step_node` 后续用于体现 Agent 动态决策：

```text
是否已经回答问题。
是否需要继续下钻。
是否需要补充统计。
是否工具失败需要重试。
是否可以进入报告生成。
```

---

## 10. Tool Use 设计

所有工具必须通过统一注册表调用，不允许业务代码散落调用 pandas / DuckDB。

### 10.1 统一 ToolResponse

所有工具返回：

```json
{
  "success": true,
  "tool_name": "groupby_aggregate",
  "data": {},
  "summary": "按品类统计销售额并返回 Top5",
  "error": null,
  "metadata": {
    "columns_used": ["product_category", "sales_amount"],
    "row_count": 5,
    "elapsed_ms": 126
  }
}
```

失败返回：

```json
{
  "success": false,
  "tool_name": "groupby_aggregate",
  "data": null,
  "summary": "工具执行失败",
  "error": {
    "code": "FIELD_NOT_FOUND",
    "message": "字段 sales_amount 不存在",
    "suggested_fields": ["amount", "total_amount"]
  },
  "metadata": {
    "elapsed_ms": 12
  }
}
```

### 10.2 MVP 工具清单

必须实现：

```text
profile_dataset：生成字段画像。
match_fields：根据问题匹配维度字段和指标字段。
groupby_aggregate：分组聚合。
generate_chart：生成 Plotly 图表配置。
generate_report：生成结构化报告。
```

建议实现：

```text
filter_rows：按条件筛选。
sort_table：排序和 TopN。
calculate_metric：计算总和、均值、占比。
```

第二阶段实现：

```text
trend_analysis：趋势分析。
outlier_detection：异常波动识别。
advanced_code_execution：DockerSandbox 中执行复杂分析代码。
```

### 10.3 groupby_aggregate 参数

输入：

```json
{
  "file_id": "file_xxx",
  "group_by": "product_category",
  "metric_column": "sales_amount",
  "aggregation": "sum",
  "sort_order": "desc",
  "limit": 5
}
```

约束：

```text
group_by 必须存在于字段画像。
metric_column 必须存在于字段画像。
aggregation 只允许 sum / avg / count / min / max。
sort_order 只允许 asc / desc。
limit 默认 10，最大 100。
```

输出：

```json
{
  "success": true,
  "tool_name": "groupby_aggregate",
  "data": {
    "rows": [
      {
        "product_category": "电子产品",
        "sales_amount_sum": 120000
      }
    ]
  },
  "summary": "按品类统计销售额并返回 Top5",
  "error": null,
  "metadata": {
    "columns_used": ["product_category", "sales_amount"],
    "row_count": 5,
    "elapsed_ms": 126
  }
}
```

### 10.4 generate_chart 参数

输入：

```json
{
  "chart_type": "bar",
  "title": "各品类销售额 Top5",
  "x_field": "product_category",
  "y_field": "sales_amount_sum",
  "rows": []
}
```

输出：

```json
{
  "success": true,
  "tool_name": "generate_chart",
  "data": {
    "chart_type": "bar",
    "plotly_spec": {}
  },
  "summary": "生成柱状图配置",
  "error": null,
  "metadata": {}
}
```

### 10.5 final_report 结构

报告必须结构化：

```json
{
  "title": "各品类销售额 Top5 分析报告",
  "analysis_goal": "比较各品类销售额表现",
  "key_findings": [
    {
      "finding": "电子产品销售额最高",
      "evidence": "DuckDB 聚合结果显示电子产品销售额为 120000",
      "source_tool": "groupby_aggregate"
    }
  ],
  "chart_explanations": [],
  "business_suggestions": [],
  "data_limitations": [],
  "next_steps": []
}
```

报告中的数字必须来自 `tool_results`，不能由模型编造。

---

## 11. 轻量 RAG 设计

MVP 的 RAG 是轻量业务语义检索，不做完整向量库。

知识库路径：

```text
backend/app/rag/knowledge_base.jsonl
```

知识库样例：

```json
{"id":"metric_sales_amount","type":"metric_definition","title":"销售额","content":"销售额通常指订单成交金额，可由 sales_amount 字段求和得到。退款或取消订单应根据 order_status 排除。","tags":["销售","指标口径"],"related_fields":["sales_amount","order_status"]}
{"id":"dimension_product_category","type":"field_definition","title":"商品品类","content":"商品品类用于观察不同产品线的销售贡献，可用于 TopN、占比和趋势分析。","tags":["商品","维度"],"related_fields":["product_category"]}
{"id":"analysis_topn","type":"analysis_template","title":"TopN 分析","content":"TopN 分析适合找出贡献最高的维度项，通常包括分组聚合、降序排序、占比计算和业务建议。","tags":["分析方法"],"related_fields":[]}
```

检索输入：

```text
用户问题
字段列表
字段名
字段样例
```

检索输出：

```json
{
  "items": [
    {
      "id": "metric_sales_amount",
      "title": "销售额",
      "content": "销售额通常指订单成交金额...",
      "score": 0.82,
      "related_fields": ["sales_amount", "order_status"]
    }
  ]
}
```

MVP 检索策略：

```text
先用关键词匹配和简单加权得分。
问题命中 title / tags / related_fields 加分。
字段名命中 related_fields 加分。
返回 Top 3 到 Top 5。
```

第二阶段升级：

```text
BM25 关键词召回。
embedding 向量召回。
rerank 重排。
pgvector / Elasticsearch 存储。
```

面试边界：

```text
RAG 用于业务语义增强，不用于精确计算 CSV 明细。
CSV 明细计算由 pandas / DuckDB 完成。
```

---

## 12. LLM Provider 设计

MVP 必须先抽象模型接口，不能把模型调用写死在 Agent 节点中。

基础接口：

```text
LLMClient
  generate_analysis_goal(question, file_profile, business_context)
  generate_analysis_plan(analysis_goal, file_profile, business_context)
  generate_report(intermediate_findings, chart_specs, business_context)
  judge_report(question, final_report, tool_results)
```

MVP 实现：

```text
MockLLMClient
```

MockLLM 规则：

```text
如果问题包含“品类”和“销售额”，生成品类销售额 TopN 计划。
如果问题包含“地区”和“销售额”，生成地区销售额对比计划。
如果问题包含“渠道”和“订单”，生成渠道订单数量与销售额分析计划。
默认返回一个基础分组聚合计划。
```

第二阶段实现：

```text
OpenAICompatibleClient
DeepSeekClient
QwenClient
```

注意：

```text
MockLLM 是为了保障主流程可运行，不是为了伪造 AI 能力。
README 中必须说明 MVP 默认使用 MockLLM，真实模型接入为第二阶段或可选配置。
```

---

## 13. 存储设计

### 13.1 SQLite 表

建议表：

```text
files
analysis_tasks
analysis_events
analysis_reports
tool_call_logs
eval_results
```

files：

```text
file_id
filename
stored_path
row_count
column_count
columns_json
created_at
```

analysis_tasks：

```text
task_id
file_id
question
status
state_json
created_at
updated_at
```

analysis_events：

```text
event_id
task_id
event_type
node
message
payload_json
created_at
```

tool_call_logs：

```text
log_id
task_id
tool_name
request_json
response_json
success
elapsed_ms
created_at
```

eval_results：

```text
eval_id
task_id
score_json
created_at
```

### 13.2 Redis key

Redis 保存短期状态：

```text
analysis_state:{task_id}
draft_report:{task_id}
intermediate_findings:{task_id}
latest_context:{task_id}
task_lock:{task_id}
```

MVP 降级策略：

```text
如果本地未启动 Redis，则 SessionStore 降级为 SQLite / 内存。
降级时必须记录 warning 日志。
README 必须说明 Redis 是推荐依赖，但 MVP 可降级运行。
```

---

## 14. 事件 Trace 设计

事件类型：

```text
task_created
dataset_profiled
goal_understood
rag_retrieved
plan_generated
fields_matched
tool_called
tool_succeeded
tool_failed
chart_generated
report_generated
eval_finished
task_completed
task_failed
```

每个节点都必须写事件。

事件 payload 应包含：

```text
节点输入摘要。
节点输出摘要。
工具名称。
工具参数。
工具结果摘要。
失败原因。
耗时。
```

不要在事件中写入完整大文件数据。只保存摘要和必要结构。

---

## 15. 规则评分器设计

MVP 先做 RuleScorer，不做真实 LLM-as-Judge。

评分维度：

```text
schema_valid：输出结构是否合法。
tool_success_rate：工具调用成功率。
field_validity：工具参数字段是否存在。
chart_validity：图表数据是否为空。
report_completeness：报告是否包含必要模块。
trace_completeness：关键事件是否完整。
cost_control：MVP 可固定通过或记录耗时。
```

输出结构：

```json
{
  "overall_score": 0.86,
  "schema_valid": true,
  "tool_success_rate": 1.0,
  "field_validity": true,
  "chart_validity": true,
  "report_completeness": 0.8,
  "trace_completeness": 1.0,
  "issues": [],
  "suggestions": ["建议补充数据限制说明"]
}
```

第二阶段 LLM-as-Judge 维度：

```text
贴题性。
准确性。
可执行性。
完整性。
幻觉风险。
表达结构化程度。
```

---

## 16. 错误和降级策略

必须处理：

```text
文件格式不支持。
CSV 编码错误。
空文件。
字段不存在。
指标字段非数值。
聚合结果为空。
图表生成失败。
报告生成失败。
RAG 无召回。
Redis 不可用。
```

处理原则：

```text
能降级就降级，不能悄悄失败。
所有失败必须写入 errors 和 events。
工具失败不能让整个服务直接崩溃。
报告必须包含 data_limitations。
字段不存在时返回候选字段。
图表失败时保留统计表和文字结论。
RAG 无召回时继续基于字段画像和工具结果分析。
Redis 不可用时降级存储，并记录 warning。
```

---

## 17. 样例数据设计

MVP 使用销售订单数据。样例 CSV 字段建议：

```text
order_id
customer_id
order_date
region
channel
product_category
product_name
quantity
sales_amount
discount
order_status
```

样例问题：

```text
分析各品类销售额 Top5，并给出业务建议。
分析各地区销售额对比，并生成图表。
分析不同渠道的订单数量和销售额表现。
```

样例数据要求：

```text
至少 200 行。
包含 5 个以上品类。
包含 4 个以上地区。
包含 3 个以上渠道。
sales_amount 为数值。
order_status 包含 completed / cancelled / refunded。
```

---

## 18. 3-5 天开发计划

### 第 1 天：项目骨架 + 数据闭环

任务：

```text
创建 FastAPI 项目结构。
定义 Pydantic Schema。
实现 SQLite 数据库模型。
实现文件上传接口。
实现 CSV 解析。
实现字段画像 profile_dataset。
准备销售订单样例数据。
实现基础 groupby_aggregate 工具。
实现 ToolResponse 统一返回。
```

验收：

```text
Swagger 能上传 CSV。
能返回字段画像。
能调用 groupby_aggregate 得到品类销售额 Top5。
工具返回结构统一。
```

### 第 2 天：分析任务 + 工具链 + 报告

任务：

```text
实现 /api/analysis/start。
实现 /api/analysis/{task_id}/run。
实现 match_fields 工具。
实现 generate_chart 工具。
实现 generate_report 工具。
实现 analysis_events 事件记录。
实现 GET /api/analysis/{task_id}。
实现 GET /api/analysis/{task_id}/events。
```

验收：

```text
输入“分析各品类销售额 Top5”，系统能生成任务。
任务能调用字段匹配、聚合、图表、报告工具。
能查询完整任务状态。
能查询事件时间线。
```

### 第 3 天：LangGraph + 轻量 RAG + LLM Provider

任务：

```text
实现 AgentState。
实现 MockLLMClient。
实现 knowledge_base.jsonl。
实现 keyword_retriever。
实现 business_context 写入 Agent 状态。
实现 LangGraph 节点：profile、goal、rag、plan、match_fields、execute_tool、chart、report。
把 /run 接口改为调用 LangGraph。
```

验收：

```text
Agent 状态中包含 analysis_goal、business_context、analysis_plan、intermediate_findings。
事件能记录每个节点。
MockLLM 能根据问题生成基础计划。
RAG 能召回销售额、品类、TopN 相关知识。
```

### 第 4 天：失败治理 + 规则评估 + 极简展示

任务：

```text
实现字段不存在错误处理。
实现非数值字段聚合错误处理。
实现图表数据为空降级。
实现 RuleScorer。
实现 eval_result 写入任务状态。
实现固定 Case 评估。
实现极简 HTML 页面或保留 Swagger 演示。
补充 README 中的架构说明。
```

验收：

```text
字段不存在时不会崩溃，会返回候选字段和错误原因。
工具失败会记录事件。
报告包含 data_limitations 和 next_steps。
RuleScorer 能输出 Schema、工具成功率、报告完整度评分。
```

### 第 5 天：验证 + 文档 + 面试材料

任务：

```text
跑通 3 个演示问题。
整理 README。
整理 API 文档。
整理技术架构图说明。
整理简历项目描述。
整理面试讲解稿。
列出第二阶段计划。
```

验收：

```text
项目能从 README 启动。
演示数据可用。
核心接口可跑。
三条演示问题能输出报告。
面试时能讲清楚技术选型和优化方向。
```

---

## 19. 测试和验证要求

每个阶段都必须验证。

最低测试：

```text
文件上传测试。
字段画像测试。
groupby_aggregate 工具测试。
generate_chart 工具测试。
analysis/start 接口测试。
analysis/run 接口测试。
events 查询测试。
RuleScorer 测试。
错误降级测试。
```

推荐命令示例：

```powershell
cd E:\bgagent1\backend
python -m pytest
uvicorn app.main:app --reload
```

如果使用 curl 验证接口，需要在 README 中记录示例。

完成任何阶段前，必须给出真实验证结果，不能只说“应该可以”。

---

## 20. README 必须包含的内容

最终 README 至少包含：

```text
项目简介。
核心能力。
技术栈。
架构图文字说明。
目录结构。
启动方式。
环境变量说明。
样例数据说明。
API 使用示例。
演示问题。
MVP 已实现能力。
第二阶段计划。
已知限制。
面试讲解要点。
```

必须明确：

```text
MVP 默认使用 MockLLM。
轻量 RAG 是 JSONL 关键词检索。
DockerSandbox 是第二阶段扩展。
Redis 不可用时存在降级逻辑。
```

---

## 21. 第二阶段扩展计划

MVP 完成后再做：

```text
接入真实 LLM API。
将关键词检索升级为 BM25 + embedding + rerank。
引入 pgvector / Elasticsearch。
强化 Redis 多轮上下文和报告草稿记忆。
实现 LLM-as-Judge。
实现 React 前端过程时间线。
加入 DockerSandbox 受控代码执行。
加入趋势分析、异常检测、占比分析工具。
加入更多业务数据集。
加入固定 Case 回归评测。
加入 Docker Compose。
```

---

## 22. 面试表达对齐

开发完成后，项目应能支撑以下简历表达：

```text
基于 LangGraph 构建“目标理解 - 字段识别 - RAG 业务语义检索 - 分析计划 - 工具执行 - 图表生成 - 报告评估”的 Agent 状态流。
封装 pandas、DuckDB、Plotly 等数据分析工具，通过 Pydantic 约束参数 Schema、返回值和错误信息，降低字段错配和结果不可复用问题。
接入企业数据字典、指标口径和分析模板知识库，将业务语义检索结果写入 Agent 状态，为分析计划提供事实依据。
通过 SQLite / Redis 保存任务状态、中间发现、报告草稿和执行事件，使分析过程可追溯、可恢复、可展示。
设计规则评分器，对 Schema、工具成功率、字段合法性、图表有效性和报告完整度进行评估，为后续 LLM-as-Judge 和固定 Case 回归打基础。
```

面试必须能讲清：

```text
为什么不用大 prompt 直接分析整张表。
为什么 RAG 不负责 CSV 明细计算。
为什么 pandas 和 DuckDB 同时存在。
为什么 Tool Use 要做 Schema 约束。
为什么需要 Agent 状态字段。
为什么要记录 Trace。
为什么要区分规则评分器和 LLM-as-Judge。
为什么 DockerSandbox 放在第二阶段。
```

---

## 23. 新对话启动 Prompt

在新对话中可以直接发送：

```text
开发目录是 E:\bgagent1。请先读取 E:\bgagent1\DEVELOPMENT_GUIDE.md，并严格按照文档协助我开发“面向结构化表格数据的多步骤分析与报告生成智能体”。

请不要直接堆功能。先根据文档确认第一阶段 MVP 的目录结构、接口契约、Pydantic Schema、Agent 状态字段、工具 Schema 和验收标准，然后再开始写代码。

开发原则：
1. 先做真实可跑的数据分析闭环，再加入 LangGraph、轻量 RAG、事件 Trace 和规则评估。
2. 不允许假上传、假工具调用、假 RAG、假持久化。
3. MVP 默认使用 MockLLM，但必须保留可替换 LLM Provider 接口。
4. RAG 只做业务语义增强，不负责 CSV 明细精确计算。
5. 每个阶段必须给出真实验证结果。
6. DockerSandbox、真实向量库、真实 LLM-as-Judge、完整 React 前端放第二阶段。
```

---

## 24. 给开发 Agent 的执行要求

新对话中的开发 Agent 必须遵守：

```text
先读本文档。
先列实施计划。
先冻结接口和 Schema。
再创建项目文件。
优先完成主链路。
每完成一阶段都运行验证。
不要把未实现能力写成已实现。
不要随意改动本文档已冻结的状态字段和接口。
如果必须改动契约，先说明原因，再同步更新文档。
```

如果开发 Agent 遇到不确定问题，优先按本文档默认方案推进，不要频繁中断询问。

