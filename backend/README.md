# Hardened Backend With Real Qwen Provider

## Scope

- CSV and Excel upload
- File profiling
- SQLite metadata persistence
- DuckDB groupby aggregation
- Analysis task creation and execution
- Event timeline query
- Rule-based task evaluation
- Real Tongyi Qianwen provider integration through a replaceable `LLMClient`

## Truthful project boundary

Currently implemented:

- category sales TopN analysis
- category sales share analysis
- region sales comparison
- channel order-count and sales-amount comparison
- local hybrid JSONL retrieval for business context
- replaceable `LLMClient` abstraction with:
  - `QwenClient` for real Tongyi Qianwen calls
  - `MockLLMClient` for explicit fallback and local/offline runs
- provider factory with configurable `LLM_PROVIDER`, `QWEN_API_KEY`, `QWEN_BASE_URL`, `QWEN_MODEL`, and fallback switch
- Qwen-driven analysis goal generation and analysis plan generation during task creation
- LangGraph-based orchestration with explicit `validate_tool_result` and `route_next_step` nodes for `/api/analysis/{task_id}/run`
- deterministic pandas / DuckDB / chart / report-tool chain kept as the numeric ground truth
- LLM-assisted final report layer and supplementary `llm_judgement` persistence
- explicit task failure recording for non-executable field matches
- automatic `eval_result` persistence after completed runs
- manual re-run through `POST /api/eval/run`

Not implemented yet:

- async queue execution
- embedding / vector retrieval / rerank
- DockerSandbox
- full React frontend
- full production-grade multi-provider management

## Runtime boundary

The project now supports real external LLM access, but only in the layers that should belong to an LLM:

- goal understanding
- analysis plan generation
- final narrative report generation
- supplementary report judgement

The project still does **not** let the LLM fabricate numeric analysis. Deterministic tool outputs remain the source of truth for:

- field matching execution inputs
- grouped aggregation
- chart data
- numeric evidence quoted in the final report

The retrieval layer is now stronger than the original pure-keyword MVP. It uses local hybrid scoring over JSONL knowledge items with keyword overlap, phrase-hit boosting, field-alignment boosting, and BM25-style normalization. This is still a lightweight local retrieval layer, not a full embedding or rerank stack.

Redis remains a recommended dependency rather than a hard requirement. When Redis is unavailable, task state explicitly degrades to SQLite-backed storage and the timeline records a `session_store_warning` event. When Redis is available, the current implementation also persists `draft_report`, `intermediate_findings`, `business_context`, a compact `context_checkpoint`, and `task_lock` into granular keys alongside the full task snapshot. When Redis is unavailable, duplicate in-process runs of the same task are still blocked by a memory lock.

## LLM configuration

Environment variables:

- `LLM_PROVIDER=qwen|mock`
- `LLM_ALLOW_FALLBACK=true|false`
- `QWEN_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_MODEL`
- `QWEN_TIMEOUT_SECONDS`

Recommended real-provider setup on Windows PowerShell:

```powershell
$env:LLM_PROVIDER = "qwen"
$env:QWEN_API_KEY = "your-key"
$env:QWEN_MODEL = "qwen-plus"
```

If `LLM_PROVIDER=qwen` and no key is available, the backend raises an explicit configuration error by default. It only falls back to `MockLLMClient` when `LLM_ALLOW_FALLBACK=true`.

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
.\.venv\Scripts\python.exe -m pytest -q
```

## Fixed eval cases

Run the predefined regression set against the real backend flow:

```powershell
cd E:\bgagent1\backend
@'
from app.eval.eval_cases import run_fixed_eval_cases
import json
print(json.dumps(run_fixed_eval_cases(), ensure_ascii=False, indent=2))
'@ | .\.venv\Scripts\python.exe -
```

The runner executes the four currently supported case families on `data/samples/sales_orders.csv`:

- category sales TopN
- category sales share
- region sales comparison
- channel order-count and sales performance

The summary also exposes evaluation aggregates derived from the real `RuleScorer` output:

- `average_tool_success_rate`
- `average_tool_elapsed_ms_total`
- `average_trace_completeness`
- `average_report_completeness`
- `average_chart_validity`
- `average_field_validity`
- `retried_tool_calls`
- `retry_attempts_total`

The same regression summary is also available through `POST /api/eval/cases/run`.

## Analysis flow

1. Upload a CSV file with `/api/files/upload`
2. Create a task with `/api/analysis/start`
3. Run the task with `/api/analysis/{task_id}/run`
4. Query task state with `/api/analysis/{task_id}`
5. Query event timeline with `/api/analysis/{task_id}/events`
6. Query tool call logs with `/api/analysis/{task_id}/tool-logs`
7. Re-run evaluation with `/api/eval/run`

The persisted timeline returned by `/api/analysis/{task_id}/events` is routed through `app/observability/event_logger.py`, while SQLite remains the storage backend.

The current graph is still intentionally small, but it now includes:

- explicit `validate_tool_result` failure handling
- explicit `route_next_step` multi-metric routing
- LLM-assisted final report generation
- supplementary `llm_judgement` persistence

`/api/analysis/start` returns:

- `analysis_goal`
- `analysis_plan`

`GET /api/analysis/{task_id}` now includes:

- `context_checkpoint`
- `tool_call_logs`
- `pending_metrics`
- `pending_tool_calls`
- `llm_judgement`

## Demo questions

- `analyse category sales top 5`
- `analyse category sales share`
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

Create a real-provider session:

```powershell
$env:LLM_PROVIDER = "qwen"
$env:QWEN_API_KEY = "your-key"
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

Expected failure examples:

- if the matched dimension or metric fields do not exist, the task returns `status = failed`
- the failure reason is written into `errors`
- the event timeline contains `task_failed`
- if `LLM_PROVIDER=qwen` but no key is available, provider selection fails explicitly unless fallback is enabled
- if the same task is already running, `/api/analysis/{task_id}/run` returns `409`
