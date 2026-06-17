# Hardened MVP Backend

## Scope

- CSV upload
- File profiling
- SQLite metadata persistence
- DuckDB groupby aggregation
- Analysis task creation and execution
- Event timeline query
- Rule-based task evaluation

## Truthful MVP boundary

Currently implemented:

- category sales TopN analysis
- region sales comparison
- channel order-count and sales-amount comparison
- JSONL keyword retrieval for business context
- replaceable MockLLM goal and plan generation
- LangGraph-based linear orchestration for `/api/analysis/{task_id}/run`
- explicit task failure recording for non-executable field matches
- automatic `eval_result` persistence after completed runs
- manual re-run through `POST /api/eval/run`

Not implemented yet:

- Redis session state
- async queue execution
- real LLM provider integration
- embedding / BM25 / rerank

Redis remains a recommended dependency rather than a hard requirement in the current MVP. When Redis is unavailable, task state explicitly degrades to SQLite-backed storage and the timeline records a `session_store_warning` event.

## Setup with uv

```powershell
cd E:\bgagent1\backend
uv sync
uv run uvicorn app.main:app --reload
```

## pip alternative

```powershell
cd E:\bgagent1\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=120 fastapi uvicorn python-multipart pandas duckdb pytest httpx
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Tests

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m pytest
```

## Fixed eval cases

Run the predefined regression set against the real MVP flow:

```powershell
cd E:\bgagent1\backend
@'
from app.eval.eval_cases import run_fixed_eval_cases
import json
print(json.dumps(run_fixed_eval_cases(), ensure_ascii=False, indent=2))
'@ | .\.venv\Scripts\python.exe -
```

The runner executes the three currently supported case families on `data/samples/sales_orders.csv`:

- category sales TopN
- region sales comparison
- channel order-count and sales performance

## Analysis flow

1. Upload a CSV file with `/api/files/upload`
2. Create a task with `/api/analysis/start`
3. Run the task with `/api/analysis/{task_id}/run`
4. Query task state with `/api/analysis/{task_id}`
5. Query event timeline with `/api/analysis/{task_id}/events`
6. Re-run evaluation with `/api/eval/run`

The persisted timeline returned by `/api/analysis/{task_id}/events` is now routed through `app/observability/event_logger.py`, while SQLite remains the storage backend.

`/api/analysis/start` now returns:

- `analysis_goal`
- `analysis_plan`
- `business_context`

## Demo questions

- `analyse category sales top 5`
- `analyse sales by region`
- `analyse channel order count and sales performance`

## One-command demo

From the repository root on Windows:

```powershell
cd E:\bgagent1
.\scripts\demo_mvp.ps1 -StartServer
```

The script uploads the sample CSV, runs all three demo questions, and prints a compact JSON summary.

## Windows API examples

Start the server:

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Upload the sample CSV with `curl.exe`:

```powershell
curl.exe -X POST -F "file=@data/samples/sales_orders.csv" http://127.0.0.1:8000/api/files/upload
```

Create an analysis task:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/analysis/start" `
  -ContentType "application/json" `
  -Body '{"file_id":"file_xxx","question":"analyse sales by region"}'
```

Run the task:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/analysis/task_xxx/run"
```

Query task state and event timeline:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/analysis/task_xxx"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/analysis/task_xxx/events"
```

Re-run rule evaluation:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/eval/run" `
  -ContentType "application/json" `
  -Body '{"task_id":"task_xxx"}'
```

Expected failure example:

- if the matched dimension or metric fields do not exist, the task returns `status = failed`
- the failure reason is written into `errors`
- the event timeline contains `task_failed`
