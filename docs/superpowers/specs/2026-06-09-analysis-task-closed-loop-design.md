# 分析任务闭环设计

## 1. 目标

在现有 Day 1 MVP 基础上，新增一条真实可跑的分析任务闭环，使系统能够围绕已上传的结构化 CSV 文件执行自然语言分析请求，并通过 API 返回可追溯的任务状态、事件时间线、图表配置和结构化报告。

本阶段目标是补齐以下能力：

- `POST /api/analysis/start`
- `POST /api/analysis/{task_id}/run`
- `GET /api/analysis/{task_id}`
- `GET /api/analysis/{task_id}/events`
- `match_fields`
- `generate_chart`
- `generate_report`
- `analysis_tasks`、`analysis_events`、`tool_call_logs` 的最小 SQLite 持久化

## 2. 范围边界

本阶段严格保持在“真实分析任务闭环”内，不提前接入以下能力：

- `LangGraph`
- `MockLLM`
- `RAG`
- `Redis`
- `RuleScorer`
- 异步任务队列
- React 前端

本阶段的核心是：以同步执行方式把已有 `file profile + groupby_aggregate` 扩展成完整分析任务链路。

## 3. 核心实现策略

采用同步执行型闭环：

- `POST /api/analysis/start` 只负责创建任务、生成规则化 `analysis_goal` 和 `analysis_plan`
- `POST /api/analysis/{task_id}/run` 同步执行整条任务链，并直接返回完整任务状态
- 任务执行过程通过 SQLite 中的事件记录进行回放，而不是依赖后台异步执行

该策略的优点：

- 实现边界清晰，验证成本低
- 与指导文档“先做真实闭环，再逐步增强”为一致方向
- 不为了提前模拟任务系统而引入不必要复杂度

## 4. 模块设计

### `app/api/analysis.py`

提供以下接口：

- `POST /api/analysis/start`
- `POST /api/analysis/{task_id}/run`
- `GET /api/analysis/{task_id}`
- `GET /api/analysis/{task_id}/events`

### `app/schemas/analysis_schema.py`

定义：

- 创建任务请求
- 创建任务响应
- 任务状态响应

### `app/schemas/report_schema.py`

定义结构化报告 schema：

- `title`
- `analysis_goal`
- `key_findings`
- `chart_explanations`
- `business_suggestions`
- `data_limitations`
- `next_steps`

### `app/schemas/event_schema.py`

定义事件和事件列表响应 schema：

- `event_id`
- `event_type`
- `node`
- `message`
- `payload`
- `created_at`

### `app/storage/models.py`

在现有 `files` 之外新增：

- `analysis_tasks`
- `analysis_events`
- `tool_call_logs`

### `app/storage/analysis_store.py`

负责：

- 创建任务
- 更新任务完整状态
- 读取任务完整状态
- 写入事件
- 查询事件列表
- 写入工具调用日志

### `app/tools/match_fields.py`

负责从“问题 + 字段画像”中识别：

- 维度字段
- 指标字段
- 聚合方式

本阶段使用规则匹配，不引入 LLM。

### `app/tools/chart_tool.py`

负责根据聚合结果生成 `Plotly spec`。

本阶段先仅支持柱状图。

### `app/tools/report_tool.py`

负责根据问题、聚合结果、图表配置生成结构化报告。

约束：

- 报告中的数字必须直接来自工具结果
- 不允许编造数值

### `app/services/analysis_runner.py`

负责串联整条同步任务链：

1. 读取任务与文件画像
2. 生成 `analysis_goal`
3. 生成 `analysis_plan`
4. 执行 `match_fields`
5. 执行 `groupby_aggregate`
6. 执行 `generate_chart`
7. 执行 `generate_report`
8. 持久化完整状态与事件

## 5. 任务状态结构

本阶段沿用指导文档中已冻结的字段命名，但只真实填充当前阶段会用到的字段。

真实填充字段：

- `task_id`
- `file_id`
- `question`
- `analysis_goal`
- `file_profile`
- `field_understanding`
- `analysis_plan`
- `current_step`
- `completed_steps`
- `intermediate_findings`
- `tool_results`
- `chart_specs`
- `final_report`
- `events`
- `errors`
- `status`

当前阶段保留但默认空值的字段：

- `business_context`
- `draft_report`
- `eval_result`

这样既不破坏指导文档中的稳定命名，也不会假装系统已经具备 `RAG` 或 `Eval` 能力。

## 6. 数据流

### 6.1 创建任务

`POST /api/analysis/start`

流程：

1. 校验 `file_id`
2. 读取文件画像
3. 根据问题生成规则化 `analysis_goal`
4. 根据问题和画像生成规则化 `analysis_plan`
5. 初始化任务状态
6. 写入 `analysis_tasks`
7. 记录 `task_created`、`goal_understood`、`plan_generated`
8. 返回创建结果

### 6.2 执行任务

`POST /api/analysis/{task_id}/run`

流程：

1. 读取任务状态与文件画像
2. 执行 `match_fields`
3. 记录 `fields_matched`
4. 调用 `groupby_aggregate`
5. 记录 `tool_called` / `tool_succeeded` / `tool_failed`
6. 基于工具结果生成图表配置
7. 记录 `chart_generated`
8. 基于工具结果和图表配置生成结构化报告
9. 记录 `report_generated`
10. 更新完整任务状态
11. 记录 `task_completed` 或 `task_failed`

### 6.3 查询任务状态

`GET /api/analysis/{task_id}`

返回完整任务状态。

### 6.4 查询事件时间线

`GET /api/analysis/{task_id}/events`

返回任务事件时间线。

## 7. 错误处理

本阶段必须处理：

- `file_id` 不存在
- `task_id` 不存在
- `match_fields` 无法识别维度字段
- `match_fields` 无法识别指标字段
- `groupby_aggregate` 执行失败
- 图表生成失败
- 报告生成失败

处理原则：

- 不允许静默失败
- 所有失败都必须写入 `errors`
- 所有失败都必须记录到 `analysis_events`
- 工具失败不允许伪造成功状态
- 图表失败时允许保留文字报告和统计结果

## 8. 事件类型

本阶段最小事件类型：

- `task_created`
- `goal_understood`
- `plan_generated`
- `fields_matched`
- `tool_called`
- `tool_succeeded`
- `tool_failed`
- `chart_generated`
- `report_generated`
- `task_completed`
- `task_failed`

## 9. 报告结构

报告保持结构化，至少包含：

- `title`
- `analysis_goal`
- `key_findings`
- `chart_explanations`
- `business_suggestions`
- `data_limitations`
- `next_steps`

报告数字必须来自 `tool_results`，不能由代码或模板凭空生成数值。

## 10. 验收标准

本阶段完成时，至少满足：

- 使用真实 `file_id + question` 调用 `POST /api/analysis/start` 能创建任务
- 返回的 `analysis_goal` 与 `analysis_plan` 不为空
- `POST /api/analysis/{task_id}/run` 能完成一次真实执行
- `GET /api/analysis/{task_id}` 能返回完整状态
- `GET /api/analysis/{task_id}/events` 能返回事件时间线
- 完整状态中至少包含：
  - `field_understanding`
  - `tool_results`
  - `chart_specs`
  - `final_report`
  - `events`
- 至少能真实跑通以下问题中的一类，最好三类都能跑通：
  - 品类销售额 Top5
  - 地区销售额对比
  - 渠道订单数量与销售额表现

## 11. 非目标声明

本阶段不得声称已实现：

- Agent 动态决策
- `LangGraph` 状态流
- `RAG` 增强规划
- LLM 驱动的目标理解或报告生成
- 规则评分器
- LLM-as-Judge

## 12. 与现有实现的衔接

本阶段必须直接复用现有 Day 1 能力：

- 文件上传与字段画像
- SQLite 文件元数据存储
- 统一 `ToolResponse`
- `groupby_aggregate`

避免重新实现已有闭环，优先在既有骨架上向上叠加任务层。
