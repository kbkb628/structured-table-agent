# Structured Table Agent

面向结构化表格数据的多步骤分析与报告生成后端项目。当前实现仍然严格遵守 `DEVELOPMENT_GUIDE.md` 的真实边界，但已经从最初的 MockLLM-only MVP 演进到“真实 Tongyi Qianwen Provider + 可验证 demo 交付”的阶段。

## 项目简介

这个项目面向上传后的企业结构化表格数据，目标是在真实后端链路内完成：

- 字段画像
- 业务语义增强
- 分析计划生成
- DuckDB 聚合执行
- 图表配置生成
- 结构化报告输出
- 事件时间线记录
- 规则评分与固定 case 回归
- Provider 诊断与项目运行总览展示

当前主链已经打通：

- CSV / Excel 上传与字段画像
- SQLite 元数据与任务状态持久化
- 基于 DuckDB 的真实聚合分析
- 基于 JSONL 的轻量混合检索
- 可替换的 `LLMClient` 抽象
- 真实 Tongyi Qianwen Provider 接入
- 基于 LangGraph 的最小分析状态流编排，包含显式 `route_next_step`
- 分析任务创建、执行、事件时间线查询和工具日志查询
- 品类、地区、渠道、趋势、占比、异常六类真实支持问题
- 规则评分 `eval_result` 自动写回与手动重算
- `/demo` 极简演示页
- `GET /api/project-status` 项目运行总览接口
- `scripts/demo_mvp.ps1` Windows 一键演示脚本

当前明确未实现：

- 异步队列
- embedding / 向量检索 / rerank
- DockerSandbox
- 完整 React 前端
- 生产级多 Provider 调度平台

## 技术栈

- 后端框架：FastAPI
- 状态编排：LangGraph
- 数据处理：pandas、DuckDB
- 模型约束：Pydantic
- 轻量 RAG：JSONL + hybrid keyword retriever
- 模型接口：`LLMClient`、`QwenClient`、`MockLLMClient`
- 持久化：SQLite
- 会话状态：Redis 优先，SQLite 降级
- 可观测性：SQLite 事件时间线 + `backend/app/observability`
- 测试：pytest

## 架构说明

当前真实链路如下：

1. 用户上传 CSV / Excel，服务端生成字段画像并落库
2. 用户创建分析任务，系统检索本地业务知识并生成 `analysis_goal` / `analysis_plan`
3. LangGraph 驱动字段匹配、DuckDB 聚合、下一步路由、图表生成、报告生成和规则评分
4. 关键步骤写入事件时间线，任务状态、工具日志和评估结果持久化到 SQLite
5. `/demo` 演示页与 `demo_mvp.ps1` 复用真实 API 展示任务流、provider 诊断、固定评测和 project runtime overview

## 目录结构

```text
backend/
  app/
    api/               HTTP 接口
    agent/             LangGraph 状态流
    eval/              RuleScorer 与固定回归 case
    llm/               Provider 工厂、QwenClient、MockLLMClient
    observability/     事件记录与 trace 常量
    rag/               本地 JSONL 知识库与检索
    schemas/           Pydantic 请求/响应结构
    services/          任务运行与 builder
    storage/           SQLite 与会话状态存储
    tools/             受控数据分析工具
  data/
    samples/           演示数据
    uploads/           上传文件
scripts/
  demo_mvp.ps1         Windows 一键演示脚本
  qwen_provider_smoke.ps1
docs/
  PROJECT_STATUS.md    当前项目状态与收口清单
  API_REFERENCE.md     接口说明
  RESUME_PROJECT_DESCRIPTION.md
  INTERVIEW_GUIDE.md
  superpowers/
```

## 项目文档

- [DEVELOPMENT_GUIDE.md](/e:/bgagent1/.worktrees/day1-mvp-backend/DEVELOPMENT_GUIDE.md)
  当前阶段开发边界与策略来源
- [docs/PROJECT_STATUS.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/PROJECT_STATUS.md)
  当前项目状态、真实边界与最新 smoke 证据
- [docs/API_REFERENCE.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/API_REFERENCE.md)
  后端接口说明与验证命令
- [docs/ARCHITECTURE_OVERVIEW.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/ARCHITECTURE_OVERVIEW.md)
  当前后端结构说明
- [docs/RESUME_PROJECT_DESCRIPTION.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/RESUME_PROJECT_DESCRIPTION.md)
  简历项目描述与可复用表达
- [docs/INTERVIEW_GUIDE.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/INTERVIEW_GUIDE.md)
  面试讲解稿与边界表达
- [backend/README.md](/e:/bgagent1/.worktrees/day1-mvp-backend/backend/README.md)
  后端启动、测试、Provider 配置和 Windows API 示例
- [scripts/demo_mvp.ps1](/e:/bgagent1/.worktrees/day1-mvp-backend/scripts/demo_mvp.ps1)
  一键上传样例 CSV 并跑通当前演示链路

## 快速开始

```powershell
cd E:\bgagent1\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=120 fastapi uvicorn python-multipart pandas duckdb pytest httpx
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

完整使用示例、测试命令和 API 调用方式见 [backend/README.md](/e:/bgagent1/.worktrees/day1-mvp-backend/backend/README.md)。

## 环境与数据

- Python：`3.12`
- 默认数据库：`backend/app.db`
- 样例数据：`backend/data/samples/sales_orders.csv`
- 默认上传目录：`backend/data/uploads`

LLM 相关环境变量：

- `LLM_PROVIDER=qwen|mock`
- `LLM_ALLOW_FALLBACK=true|false`
- `QWEN_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_MODEL`
- `QWEN_TIMEOUT_SECONDS`

当前 Redis 仍是推荐依赖而不是强制依赖。Redis 不可用时，系统会显式降级到 SQLite 并记录 `session_store_warning` 事件。

## 样例数据说明

当前样例数据文件是 `backend/data/samples/sales_orders.csv`，字段包括：

- `order_id`
- `customer_id`
- `order_date`
- `region`
- `channel`
- `product_category`
- `product_name`
- `quantity`
- `sales_amount`
- `discount`
- `order_status`

样例数据当前支持：

- 品类销售额 TopN
- 品类销售占比
- 品类异常检测
- 地区销售额对比
- 渠道订单数与销售额对比
- 按日期的销售趋势分析

## 一键演示

如果本地已经建好 `backend/.venv`，可以直接运行：

```powershell
cd E:\bgagent1
.\scripts\demo_mvp.ps1 -StartServer
```

脚本会：

- 自动启动本地 FastAPI 服务
- 调用 `GET /api/project-status` 获取当前项目运行总览
- 上传 `backend/data/samples/sales_orders.csv`
- 依次运行六个当前支持的演示问题
- 输出 project status 摘要、任务状态、图表数量、工具调用数量和评估分数摘要
- 输出 `provider_smoke_error_message` 等 provider smoke 失败细节字段
- 输出 `fixed_eval_average_trace_completeness`、`fixed_eval_average_report_completeness` 等 fixed eval 质量指标

## API 与验证

当前关键接口：

- `POST /api/files/upload`
- `GET /api/files/{file_id}/profile`
- `POST /api/analysis/start`
- `POST /api/analysis/{task_id}/run`
- `GET /api/analysis/{task_id}`
- `GET /api/analysis/{task_id}/events`
- `GET /api/analysis/{task_id}/tool-logs`
- `POST /api/eval/run`
- `POST /api/eval/cases/run`
- `GET /api/llm/provider-status`
- `POST /api/llm/provider-smoke`
- `GET /api/project-status`
- `GET /demo`

Windows 示例：

```powershell
cd E:\bgagent1\backend
curl.exe -X POST -F "file=@data/samples/sales_orders.csv" http://127.0.0.1:8000/api/files/upload
```

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/api/project-status"
```

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/llm/provider-smoke"
```

全量测试：

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m pytest -q
```

## 当前真实边界

当前已经真实实现的 AI / Agent 相关部分是：

- `QwenClient`：真实 Tongyi Qianwen Provider 调用
- `MockLLMClient`：显式本地回退
- `knowledge_base.jsonl + keyword_retriever`：真实本地混合检索
- `business_context`：检索结果会写入任务状态并记录 `rag_retrieved` 事件
- `SessionStore`：Redis 可用时保存完整状态与细粒度 key，不可用时降级为 SQLite + 内存锁
- `LangGraph`：当前 `/api/analysis/{task_id}/run` 已通过包含 `route_next_step` 的最小状态流执行
- `RuleScorer + fixed eval cases`：规则评分与固定 case 回归
- `GET /api/llm/provider-status` / `POST /api/llm/provider-smoke`：Provider 运行时诊断
- `GET /api/project-status`：项目运行总览
- `/demo`：极简真实 API 演示页

当前仍然没有实现的部分是：

- embedding / 向量检索 / rerank
- DockerSandbox
- 完整 React 前端
- 异步任务队列
- 生产级多 Provider 编排

## 面试讲解要点

- 为什么不能把整张表直接交给大模型做分析
- 为什么业务语义检索只负责增强，不负责 CSV 明细精确计算
- 为什么要把 DuckDB、工具调用、事件时间线、规则评分、provider 诊断和 project-status 放在同一条真实链路里
- 为什么真实 LLM 只负责目标理解、计划组织、报告表达和补充评审，而不直接替代数值计算
