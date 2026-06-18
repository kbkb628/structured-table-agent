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
- category sales anomaly detection
- region sales comparison
- channel order-count and sales-amount comparison
- sales trend analysis by order date
- local hybrid JSONL retrieval for business context
- replaceable `LLMClient` abstraction with:
  - `QwenClient` for real Tongyi Qianwen calls
  - `MockLLMClient` for explicit fallback and local/offline runs
- provider factory with configurable `LLM_PROVIDER`, `QWEN_API_KEY` / `TONGYI_API_KEY` / `DASHSCOPE_API_KEY`, `QWEN_BASE_URL`, `QWEN_MODEL`, and fallback switch
- provider diagnostics through `/api/llm/provider-status`, `/api/llm/provider-smoke`, and `scripts/qwen_provider_smoke.ps1`
  - structured `diagnostics` including provider support, key-source kind, smoke readiness, warnings, and recommendations
- project runtime overview through `/api/project-status`
- Qwen-driven analysis goal generation and analysis plan generation during task creation
- LangGraph-based orchestration with explicit `validate_tool_result` and `route_next_step` nodes for `/api/analysis/{task_id}/run`
- deterministic pandas / DuckDB / chart / report-tool chain kept as the numeric ground truth
- LLM-assisted final report layer and supplementary `llm_judgement` persistence
- explicit task failure recording for non-executable field matches
- automatic `eval_result` persistence after completed runs
- manual re-run through `POST /api/eval/run`
- minimal local demo page at `/demo` over the real backend APIs

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

Redis remains a recommended dependency rather than a hard requirement. When Redis is unavailable, task state explicitly degrades to SQLite-backed storage and the timeline records a `session_store_warning` event. When Redis is available, the current implementation also persists `draft_report`, `final_report`, `llm_judgement`, `intermediate_findings`, `business_context`, a compact `context_checkpoint`, and `task_lock` into granular keys alongside the full task snapshot. If the main `analysis_state` snapshot is missing but these granular keys still exist, the backend rebuilds the task view from SQLite state plus the granular Redis payloads and records a `session_state_recovered` event in the task timeline. The latest recovery detail is also surfaced through `GET /api/project-status`, `/demo`, and `scripts/demo_mvp.ps1` with `project_status_session_store_latest_recovered_recovery_source`, `project_status_session_store_latest_recovered_segment_count`, and `project_status_session_store_latest_recovered_segments`. When Redis is unavailable, duplicate in-process runs of the same task are still blocked by a memory lock.

## LLM configuration

Environment variables:

- `LLM_PROVIDER=qwen|mock`
- `LLM_ALLOW_FALLBACK=true|false`
- `QWEN_API_KEY`
- `TONGYI_API_KEY`
- `DASHSCOPE_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_MODEL`
- `QWEN_TIMEOUT_SECONDS`

Recommended real-provider setup on Windows PowerShell:

```powershell
$env:LLM_PROVIDER = "qwen"
$env:TONGYI_API_KEY = "your-key"
$env:QWEN_MODEL = "qwen-plus"
```

If `LLM_PROVIDER=qwen` and no key is available, the backend raises an explicit configuration error by default. It only falls back to `MockLLMClient` when `LLM_ALLOW_FALLBACK=true`.
Supported key names are `QWEN_API_KEY`, `TONGYI_API_KEY`, `DASHSCOPE_API_KEY`, and `OPENAI_API_KEY*` compatibility variables.

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

The runner executes the six currently supported case families on `data/samples/sales_orders.csv`:

- category sales TopN
- category sales share
- category sales anomaly detection
- region sales comparison
- channel order-count and sales performance
- sales trend by order date

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
8. Inspect provider resolution with `/api/llm/provider-status`
9. Run a minimal provider smoke check with `/api/llm/provider-smoke`

The persisted timeline returned by `/api/analysis/{task_id}/events` is routed through `app/observability/event_logger.py`, while SQLite remains the storage backend.

The current graph is still intentionally small, but it now includes:

- explicit `validate_tool_result` failure handling
- explicit `route_next_step` multi-metric routing
- LLM-assisted final report generation
- supplementary `llm_judgement` persistence

There is also a lightweight local demo page at `/demo`. It is not a separate frontend project or a React app. It is a single FastAPI-served HTML page that reuses the existing upload, analysis, task-state, event, and tool-log APIs for local demos.

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
- `analyse category sales anomalies`
- `analyse sales by region`
- `analyse sales trend by order date`
- `analyse channel order count and sales performance`

## Local demo page

After the backend starts, open:

```text
http://127.0.0.1:8000/demo
```

The page supports:

- uploading a CSV or Excel file
- loading the built-in `sales_orders.csv` sample into the same upload flow
- entering or choosing a supported analysis question
- running the real analysis task flow
- inspecting live LLM provider status and running a provider smoke check
- loading the project runtime overview from `/api/project-status`
- inspecting the session store runtime mode exposed by `/api/project-status`, including whether Redis is active or the backend is degraded to SQLite
- running the fixed eval regression summary from the same demo page
- viewing final report output, task snapshot, event timeline, and tool logs

## One-command demo

From the repository root on Windows:

```powershell
cd E:\bgagent1
.\scripts\demo_mvp.ps1 -StartServer
```

The script uploads the sample CSV, queries `GET /api/project-status`, checks `GET /api/llm/provider-status` and `POST /api/llm/provider-smoke`, runs the current supported demo question set, and prints a compact JSON summary including provider diagnostics, smoke failure details when present, and fixed-eval quality metrics.

Key summary fields exposed by the script include:

- `project_status_provider`
- `project_status_session_store_preferred_backend`
- `project_status_session_store_active_backend`
- `project_status_session_store_redis_available`
- `project_status_session_store_degraded_to_sqlite`
- `project_status_session_store_redis_url`
- `project_status_session_store_warning_count`
- `project_status_session_store_recovered_count`
- `project_status_session_store_latest_warning_task_id`
- `project_status_session_store_latest_warning_at`
- `project_status_session_store_latest_recovered_task_id`
- `project_status_session_store_latest_recovered_at`
- `project_status_session_store_latest_recovered_recovery_source`
- `project_status_session_store_latest_recovered_segment_count`
- `project_status_session_store_latest_recovered_segments`
- `project_status_latest_task_has_business_context`
- `project_status_latest_task_supported_by_tools`
- `project_status_latest_task_has_findings`
- `project_status_latest_task_has_eval_result`
- `project_status_latest_task_eval_overall_score`
- `project_status_latest_task_eval_suggestion_count`
- `project_status_latest_task_eval_schema_valid`
- `project_status_latest_task_eval_tool_success_rate`
- `project_status_latest_task_eval_tool_elapsed_ms_total`
- `project_status_latest_task_eval_field_validity`
- `project_status_latest_task_eval_chart_validity`
- `project_status_latest_task_eval_report_completeness`
- `project_status_latest_task_eval_trace_completeness`
- `project_status_latest_task_pending_metric_count`
- `project_status_latest_task_latest_event_type`
- `project_status_latest_task_has_context_checkpoint`
- `project_status_latest_task_has_draft_report`
- `project_status_latest_task_has_final_report`
- `project_status_latest_task_eval_has_dimension_scores`
- `project_status_latest_task_latest_event_at`
- `project_status_latest_task_llm_issue_count`
- `project_status_latest_task_route_decision_count`
- `project_status_latest_task_continued_route_decision_count`
- `project_status_latest_task_finished_route_decision_count`
- `project_status_latest_task_latest_route_decision`
- `project_status_latest_task_chart_spec_count`
- `project_status_latest_task_key_finding_count`
- `project_status_latest_task_next_step_count`
- `project_status_latest_task_business_context_count`
- `project_status_latest_task_top_business_context_title`
- `project_status_latest_task_top_business_context_score`
- `project_status_latest_task_top_business_context_related_field_count`
- `project_status_latest_task_top_business_context_has_score_breakdown`
- `project_status_latest_task_top_business_context_keyword_score`
- `project_status_latest_task_top_business_context_field_score`
- `project_status_latest_task_top_business_context_phrase_score`
- `project_status_latest_task_top_business_context_bm25_score`
- `project_status_latest_task_checkpoint_current_step`
- `project_status_latest_task_checkpoint_status`
- `project_status_latest_task_checkpoint_pending_metric_count`
- `project_status_latest_task_checkpoint_finding_count`
- `project_status_latest_task_checkpoint_business_context_title_count`
- `project_status_latest_task_checkpoint_business_context_titles`
- `project_status_latest_task_checkpoint_latest_error_code`
- `project_status_latest_task_analysis_goal`
- `project_status_latest_task_analysis_plan_count`
- `project_status_latest_task_current_step`
- `project_status_latest_task_finding_count`
- `project_status_latest_task_dimension_field`
- `project_status_latest_task_match_analysis_type`
- `project_status_latest_task_candidate_field_count`
- `project_status_latest_task_match_warning_count`
- `project_status_latest_task_planned_tool_sequence`
- `project_status_latest_task_tool_result_count`
- `project_status_latest_task_retried_tool_result_count`
- `project_status_latest_task_retry_attempts_total`
- `project_status_latest_task_latest_tool_name`
- `project_status_latest_task_total_tool_elapsed_ms`
- `project_status_latest_task_error_count`
- `project_status_latest_task_latest_error_message`
- `project_status_latest_task_has_degradation`
- `provider_smoke_error_message`
- `fixed_eval_retried_tool_calls`
- `fixed_eval_retry_attempts_total`
- `fixed_eval_average_tool_elapsed_ms_total`
- `fixed_eval_average_trace_completeness`
- `fixed_eval_average_report_completeness`
- `fixed_eval_average_chart_validity`
- `fixed_eval_average_field_validity`

Additional runtime-summary fields that are also exposed by the script include:

- `project_status_demo_available`
- `project_status_demo_path`
- `project_status_latest_task_id`
- `project_status_latest_task_status`
- `project_status_latest_task_updated_at`
- `project_status_latest_task_has_llm_judgement`
- `project_status_latest_task_judgement_issue_count`
- `project_status_latest_task_tool_call_log_count`
- `project_status_latest_task_eval_issue_count`
- `project_status_latest_task_planned_tool_call_count`
- `project_status_latest_task_event_count`
- `project_status_latest_task_business_suggestion_count`
- `project_status_latest_task_data_limitation_count`
- `project_status_latest_task_checkpoint_draft_report_status`
- `project_status_latest_task_completed_step_count`
- `project_status_latest_task_metric_count`
- `project_status_latest_task_successful_tool_result_count`
- `project_status_latest_task_failed_tool_result_count`
- `project_status_latest_task_latest_retry_status`
- `project_status_latest_task_latest_error_code`
- `project_status_files_exists`
- `project_status_tasks_exists`
- `project_status_analysis_events_exists`
- `project_status_tool_call_logs_exists`
- `project_status_eval_results_exists`
- `project_status_files`
- `project_status_tasks`
- `project_status_analysis_events`
- `project_status_tool_call_logs`
- `project_status_eval_results`
- `provider_status_allow_fallback`
- `provider_status_has_api_key`
- `provider_status_key_source`
- `provider_status_base_url`
- `provider_status_model`
- `provider_status_timeout_seconds`
- `provider_status_provider_supported`
- `provider_status_key_source_kind`
- `provider_status_smoke_ready`
- `provider_status_warnings`
- `provider_status_recommendations`
- `provider_smoke_ok`
- `provider_smoke_client_type`
- `provider_smoke_error_type`
- `fixed_eval_pass_rate`
- `fixed_eval_passed_cases`
- `fixed_eval_total_cases`
- `fixed_eval_average_tool_success_rate`

These `project_status_latest_task_match_analysis_type`, `project_status_latest_task_candidate_field_count`, `project_status_latest_task_match_warning_count`, and `project_status_latest_task_planned_tool_sequence` fields come from the persisted `field_understanding` block produced by `match_fields`. They show real structured matching and schema-bounded planning evidence rather than any automatic schema repair capability.

The `project_status_latest_task_eval_suggestion_count`, `project_status_latest_task_eval_schema_valid`, `project_status_latest_task_eval_tool_success_rate`, `project_status_latest_task_eval_tool_elapsed_ms_total`, `project_status_latest_task_eval_field_validity`, `project_status_latest_task_eval_chart_validity`, `project_status_latest_task_eval_report_completeness`, and `project_status_latest_task_eval_trace_completeness` fields come directly from the persisted `eval_result` generated by `RuleScorer`. They expose the current rule-based quality signal as runtime evidence instead of only keeping it inside the task state JSON.

The `project_status_latest_task_checkpoint_status`, `project_status_latest_task_checkpoint_pending_metric_count`, `project_status_latest_task_checkpoint_finding_count`, `project_status_latest_task_checkpoint_business_context_title_count`, and `project_status_latest_task_checkpoint_business_context_titles` fields come from the compact `context_checkpoint` that `SessionStore` already persists into granular Redis keys and mirrors into task state. They expose the latest checkpoint snapshot as runtime evidence for resumability and process tracing.

The `project_status_latest_task_top_business_context_keyword_score`, `project_status_latest_task_top_business_context_field_score`, `project_status_latest_task_top_business_context_phrase_score`, and `project_status_latest_task_top_business_context_bm25_score` fields come from the persisted `score_breakdown` of the local hybrid retriever. They expose how keyword overlap, field alignment, phrase hits, and BM25-style normalization contributed to the top retrieved business context item.

## Windows API examples

Start the server:

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Create a real-provider session:

```powershell
$env:LLM_PROVIDER = "qwen"
$env:TONGYI_API_KEY = "your-key"
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

Inspect provider resolution and run a smoke check:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/llm/provider-status"
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/llm/provider-smoke"
.\scripts\qwen_provider_smoke.ps1
```

Expected failure examples:

- if the matched dimension or metric fields do not exist, the task returns `status = failed`
- the failure reason is written into `errors`
- the event timeline contains `task_failed`
- if `LLM_PROVIDER=qwen` but no key is available, provider selection fails explicitly unless fallback is enabled
- if the same task is already running, `/api/analysis/{task_id}/run` returns `409`
