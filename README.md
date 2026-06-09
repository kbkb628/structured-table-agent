# Structured Table Agent

面向结构化表格数据的多步骤分析与报告生成后端原型，当前实现严格停留在 `DEVELOPMENT_GUIDE.md` 约束下的真实 MVP 边界内。

当前主线已经打通：

- CSV 上传与字段画像
- SQLite 元数据与任务状态持久化
- 基于 DuckDB 的真实聚合分析
- 分析任务创建、执行、事件时间线查询
- 品类、地区、渠道三类演示问题闭环
- 规则评分 `eval_result` 自动写回与手动重算

当前明确未实现：

- LangGraph
- RAG / 本地知识库检索
- Redis 会话态
- 异步队列
- 真实 LLM Provider

## 项目结构

- [DEVELOPMENT_GUIDE.md](/e:/bgagent1/.worktrees/day1-mvp-backend/DEVELOPMENT_GUIDE.md)
  当前阶段开发边界与策略来源
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
