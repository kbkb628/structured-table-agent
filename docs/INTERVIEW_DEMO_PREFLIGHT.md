# Interview Demo Preflight

本文用于面试演示前的最后检查，目标是在 3-10 分钟内确认服务、provider、运行态聚合和演示脚本都处于可展示状态，避免现场临时排错。
如果演示结束后需要判断当前版本是否已经适合封板，可再回看 [RELEASE_READINESS_AUDIT.md](./RELEASE_READINESS_AUDIT.md)。

## 演示前检查单

建议按下面顺序执行：

1. 启动后端服务
2. 检查 `GET /api/llm/provider-status`
3. 检查 `POST /api/llm/provider-smoke`
4. 检查 `GET /demo`
5. 检查 `GET /api/project-status`
6. 运行 `scripts/demo_mvp.ps1`

## 1. 启动后端服务

命令：

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

预期现象：

- 控制台正常启动，没有 import error
- `http://127.0.0.1:8000/docs` 能打开
- `/demo` 能返回页面

失败排查：

- 如果缺依赖，先按 [backend/README.md](../backend/README.md) 重新安装
- 如果端口冲突，先检查是否已有旧的 uvicorn 进程占用 8000

## 2. 检查 `GET /api/llm/provider-status`

命令：

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/llm/provider-status"
```

预期现象：

- 返回当前 provider 配置
- `provider` 字段存在
- `diagnostics.provider_supported` 为 `true`
- 如果要走真实模型，`diagnostics.smoke_ready` 应为 `true`

失败排查：

- 如果 `provider_supported=false`，检查 `LLM_PROVIDER`
- 如果 `has_api_key=false`，检查 `QWEN_API_KEY`、`TONGYI_API_KEY`、`DASHSCOPE_API_KEY` 或兼容变量

## 3. 检查 `POST /api/llm/provider-smoke`

命令：

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/llm/provider-smoke"
```

预期现象：

- 真实 provider 可用时，返回 `ok = true`
- 返回 `client_type`
- 返回最小 `analysis_goal`

失败排查：

- 如果返回 `error_type` 或 `error_message`，先确认 key 是否有效
- 如果是网络或 provider 侧错误，至少保留 `provider-status` 结果作为真实接入证据

## 4. 检查 `GET /demo`

命令：

```powershell
start http://127.0.0.1:8000/demo
```

预期现象：

- 页面能打开
- 页面里能看到 `LLM Provider Status`
- 页面里能看到 `Project Runtime Overview`
- 页面里能看到 latest task 和 fixed eval 区块

失败排查：

- 如果页面打不开，先回头确认 uvicorn 是否仍在运行
- 如果页面打开但按钮报错，优先查后端日志，再查 `/api/project-status`

## 5. 检查 `GET /api/project-status`

命令：

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/project-status"
```

预期现象：

- `summary.provider` 存在
- `summary.session_store` 存在
- `summary.database.tables` 存在
- 如果之前跑过任务，latest task 相关字段应可见

建议优先确认的字段：

- `project_status_latest_task_analysis_goal`
- `project_status_latest_task_latest_route_decision`
- `project_status_latest_task_top_business_context_bm25_score`
- `project_status_latest_task_checkpoint_status`
- `project_status_latest_task_eval_tool_success_rate`

失败排查：

- 如果只有空 summary，没有 latest task，说明还没跑任务；这时可继续执行 `demo_mvp.ps1`
- 如果数据库表统计异常，检查 `backend/app.db` 是否可读

## 6. 运行 `scripts/demo_mvp.ps1`

命令：

```powershell
cd E:\bgagent1
.\scripts\demo_mvp.ps1
```

预期现象：

- 能上传样例 CSV
- 能跑支持的 demo 问题
- 输出 provider 运行态字段
- 输出 latest task 摘要字段
- 输出 fixed eval 质量字段，例如 `fixed_eval_pass_rate`

失败排查：

- 如果脚本一开始失败，先检查后端是否启动
- 如果脚本卡在 provider 相关步骤，先单独跑 `/api/llm/provider-status` 和 `/api/llm/provider-smoke`
- 如果脚本有输出但 latest task 字段为空，说明任务没有成功落库，继续查 `/api/project-status` 和后端日志

## 上场前最小确认项

如果时间非常紧，至少确认下面 5 件事：

1. `uvicorn app.main:app` 已启动
2. `GET /api/llm/provider-status` 正常返回
3. `/demo` 能打开
4. `GET /api/project-status` 正常返回
5. `scripts/demo_mvp.ps1` 最近能跑出 `fixed_eval_pass_rate`

## 建议的备用说法

- 如果真实 provider 临时不可用，可以先展示 provider-status 和 provider-smoke 的报错细节，说明系统已做运行时诊断而不是静默失败
- 如果 latest task 为空，可以先展示 `/demo` 和 `project-status` 的 runtime overview，再补跑 `demo_mvp.ps1`
- 如果时间被压缩，直接按 [INTERVIEW_DEMO_CHECKLIST.md](./INTERVIEW_DEMO_CHECKLIST.md) 的 2 分钟版本进行
