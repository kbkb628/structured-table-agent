# Structured Table Agent

面向结构化表格数据的多步骤分析与报告生成后端原型，当前实现严格停留在 `DEVELOPMENT_GUIDE.md` 约束下的真实 MVP 边界内。

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

当前默认使用 `MockLLM` 和本地 JSONL 关键词检索，所有数值结论都必须来自真实工具结果，不依赖模型臆造。

当前主线已经打通：

- CSV 上传与字段画像
- SQLite 元数据与任务状态持久化
- 基于 DuckDB 的真实聚合分析
- 基于 JSONL 的轻量关键词业务语义检索
- 可替换的 MockLLM 目标与计划生成
- 基于 LangGraph 的最小分析状态流编排
- 分析任务创建、执行、事件时间线查询
- 品类、地区、渠道三类演示问题闭环
- 规则评分 `eval_result` 自动写回与手动重算

当前明确未实现：

- Redis 会话态
- 异步队列
- 真实 LLM Provider
- embedding / BM25 / rerank

## 技术栈

- 后端框架：FastAPI
- 状态编排：LangGraph
- 数据处理：pandas、DuckDB
- 模型约束：Pydantic
- 轻量 RAG：JSONL + keyword retriever
- 模型接口：`LLMClient` + `MockLLMClient`
- 持久化：SQLite
- 可观测性：SQLite 事件时间线 + `backend/app/observability`
- 测试：pytest

## 架构说明

当前 MVP 采用以下真实链路：

1. 用户上传 CSV，服务端生成字段画像并落库
2. 用户创建分析任务，系统检索本地业务知识并生成目标/计划
3. LangGraph 驱动字段匹配、DuckDB 聚合、图表生成、报告生成和规则评分
4. 每个关键步骤写入事件时间线，任务状态和评估结果持久化到 SQLite
5. 固定回归评测可用同一条真实链路批量执行 3 个支持 case

## 目录结构

```text
backend/
  app/
    api/               HTTP 接口
    agent/             LangGraph 状态流
    eval/              RuleScorer 与固定回归 case
    llm/               可替换 LLM 接口与 MockLLM
    observability/     事件记录与 trace 常量
    rag/               本地 JSONL 知识库与检索
    schemas/           Pydantic 请求/响应结构
    services/          任务运行与共享 builder
    storage/           SQLite 与文件存储
    tools/             受控数据分析工具
  data/
    samples/           演示数据
    uploads/           上传文件
scripts/
  demo_mvp.ps1         Windows 一键演示脚本
docs/
  PROJECT_STATUS.md    当前项目状态与收口清单
  superpowers/         设计和实施文档
```

## 项目结构

- [DEVELOPMENT_GUIDE.md](/e:/bgagent1/.worktrees/day1-mvp-backend/DEVELOPMENT_GUIDE.md)
  当前阶段开发边界与策略来源
- [docs/PROJECT_STATUS.md](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/PROJECT_STATUS.md)
  当前项目状态、MVP 边界与收口清单
- [backend/README.md](/e:/bgagent1/.worktrees/day1-mvp-backend/backend/README.md)
  后端启动、测试、Windows API 示例
- [scripts/demo_mvp.ps1](/e:/bgagent1/.worktrees/day1-mvp-backend/scripts/demo_mvp.ps1)
  一键上传样例 CSV 并跑通三类演示问题
- [docs/superpowers/specs](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/superpowers/specs)
  已落库的设计文档
- [docs/superpowers/plans](/e:/bgagent1/.worktrees/day1-mvp-backend/docs/superpowers/plans)
  已落库的实施计划

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

当前没有额外环境变量要求；MVP 默认走本地 `MockLLM` 和 SQLite。

## 一键演示

如果本地已经建好 `backend/.venv`，可以直接运行：

```powershell
cd E:\bgagent1
.\scripts\demo_mvp.ps1 -StartServer
```

脚本会：

- 自动启动本地 FastAPI 服务
- 上传 `backend/data/samples/sales_orders.csv`
- 依次运行品类、地区、渠道三类分析问题
- 输出任务状态、图表数量、工具调用数量和评估分数摘要

## API 与验证

当前核心接口：

- `POST /api/files/upload`
- `GET /api/files/{file_id}/profile`
- `POST /api/analysis/start`
- `POST /api/analysis/{task_id}/run`
- `GET /api/analysis/{task_id}`
- `GET /api/analysis/{task_id}/events`
- `POST /api/eval/run`

全量测试：

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m pytest -v
```

固定回归评测：

```powershell
cd E:\bgagent1\backend
@'
from app.eval.eval_cases import run_fixed_eval_cases
import json
print(json.dumps(run_fixed_eval_cases(), ensure_ascii=False, indent=2))
'@ | .\.venv\Scripts\python.exe -
```

## 当前 MVP 边界

当前已经实现的 AI 相关部分是：

- `MockLLMClient`：基于规则的可替换目标/计划生成器
- `knowledge_base.jsonl + keyword_retriever`：真实本地 JSONL 检索
- `business_context`：检索结果会写入任务状态并记录 `rag_retrieved` 事件
- `LangGraph`：当前 `/api/analysis/{task_id}/run` 已通过最小线性状态流执行
- `RuleScorer + fixed eval cases`：规则评分与固定 case 回归

当前仍然没有实现的部分是：

- 外部真实 LLM API
- 向量检索或重排
- Redis 记忆和异步任务

## 已知限制

- 只支持 CSV 上传，不支持 Excel
- 分析问题当前只在品类、地区、渠道三类英文问法上做了真实支持
- 图表当前只输出 Plotly 柱状图配置，不包含前端渲染页面
- 当前事件时间线以 SQLite 为主，不包含外部 tracing 平台

## 第二阶段计划

- 接入真实 LLM Provider
- 升级为 embedding / BM25 / rerank 检索
- 增加 Redis 会话记忆与异步任务执行
- 引入 DockerSandbox
- 引入 LLM-as-Judge
- 补完整 React 前端

## 面试讲解要点

- 为什么不能把整张表直接塞给大模型做分析
- 为什么业务语义检索只负责增强，不负责 CSV 明细精确计算
- 为什么要把 DuckDB、工具调用、事件时间线和规则评分放在同一条真实链路里
- 为什么当前阶段坚持 MockLLM 和轻量 RAG，而不是提前混入第二阶段能力
