# Analysis Task Closed Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next real backend loop after Day 1: create an analysis task from `file_id + question`, run the task synchronously, persist task state and events, and return chart config plus structured report.

**Architecture:** Extend the existing FastAPI backend by adding a task layer above the current file/profile/tool loop. Persist task state, events, and tool-call logs in SQLite; use rule-based field matching, existing DuckDB aggregation, deterministic chart generation, and structured report assembly without introducing LangGraph, LLM, RAG, or Redis.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pandas, DuckDB, SQLite, pytest, Plotly-compatible JSON specs

---

### Task 1: Add analysis persistence and state schemas

**Files:**
- Modify: `backend/app/storage/database.py`
- Modify: `backend/app/storage/models.py`
- Create: `backend/app/storage/analysis_store.py`
- Create: `backend/app/schemas/analysis_schema.py`
- Create: `backend/app/schemas/report_schema.py`
- Create: `backend/app/schemas/event_schema.py`
- Test: `backend/tests/test_analysis_store.py`

- [ ] **Step 1: Write the failing persistence test**

```python
# backend/tests/test_analysis_store.py
from app.storage.analysis_store import create_task, get_task_state, list_task_events, record_event


def test_analysis_task_roundtrip():
    state = {
        "task_id": "task_test",
        "file_id": "file_001",
        "question": "analyse category sales top 5",
        "analysis_goal": "compare category sales",
        "file_profile": {},
        "field_understanding": {},
        "business_context": [],
        "analysis_plan": ["match fields", "aggregate sales"],
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "created",
    }

    create_task("task_test", "file_001", "analyse category sales top 5", state)
    record_event("task_test", "task_created", "create_task", "task created", {"status": "created"})

    loaded = get_task_state("task_test")
    events = list_task_events("task_test")

    assert loaded is not None
    assert loaded["task_id"] == "task_test"
    assert loaded["status"] == "created"
    assert events[0]["event_type"] == "task_created"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_analysis_store.py -v`
Expected: FAIL with `ModuleNotFoundError` because the analysis store and schemas do not exist yet.

- [ ] **Step 3: Implement minimal task persistence**

```python
# backend/app/storage/models.py
from dataclasses import dataclass


@dataclass(slots=True)
class FileRecord:
    file_id: str
    filename: str
    stored_path: str
    row_count: int
    column_count: int
    columns_json: str
    created_at: str


@dataclass(slots=True)
class AnalysisTaskRecord:
    task_id: str
    file_id: str
    question: str
    status: str
    state_json: str
    created_at: str
    updated_at: str
```

```python
# backend/app/storage/database.py
import sqlite3

from app.core.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                file_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                column_count INTEGER NOT NULL,
                columns_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_tasks (
                task_id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                question TEXT NOT NULL,
                status TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_events (
                event_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                node TEXT NOT NULL,
                message TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_call_logs (
                log_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                request_json TEXT NOT NULL,
                response_json TEXT NOT NULL,
                success INTEGER NOT NULL,
                elapsed_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
```

```python
# backend/app/schemas/report_schema.py
from pydantic import BaseModel


class KeyFinding(BaseModel):
    finding: str
    evidence: str
    source_tool: str


class FinalReport(BaseModel):
    title: str
    analysis_goal: str
    key_findings: list[KeyFinding]
    chart_explanations: list[str]
    business_suggestions: list[str]
    data_limitations: list[str]
    next_steps: list[str]
```

```python
# backend/app/schemas/event_schema.py
from typing import Any

from pydantic import BaseModel


class AnalysisEvent(BaseModel):
    event_id: str
    event_type: str
    node: str
    message: str
    payload: dict[str, Any]
    created_at: str


class AnalysisEventList(BaseModel):
    task_id: str
    events: list[AnalysisEvent]
```

```python
# backend/app/schemas/analysis_schema.py
from typing import Any

from pydantic import BaseModel

from app.schemas.event_schema import AnalysisEvent
from app.schemas.report_schema import FinalReport


class AnalysisStartRequest(BaseModel):
    file_id: str
    question: str


class AnalysisStartResponse(BaseModel):
    task_id: str
    status: str
    analysis_goal: str
    analysis_plan: list[str]


class AnalysisTaskState(BaseModel):
    task_id: str
    file_id: str
    question: str
    analysis_goal: str
    file_profile: dict[str, Any]
    field_understanding: dict[str, Any]
    business_context: list[dict[str, Any]]
    analysis_plan: list[str]
    current_step: str
    completed_steps: list[str]
    intermediate_findings: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    chart_specs: list[dict[str, Any]]
    draft_report: dict[str, Any]
    final_report: dict[str, Any]
    eval_result: dict[str, Any]
    events: list[AnalysisEvent]
    errors: list[dict[str, Any]]
    status: str
```

```python
# backend/app/storage/analysis_store.py
import json
import uuid
from datetime import datetime, timezone

from app.storage.database import get_connection, init_db


def _ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_task(task_id: str, file_id: str, question: str, state: dict) -> None:
    init_db()
    now = _ts()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO analysis_tasks (
                task_id, file_id, question, status, state_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, file_id, question, state["status"], json.dumps(state, ensure_ascii=False), now, now),
        )


def update_task_state(task_id: str, state: dict) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE analysis_tasks
            SET status = ?, state_json = ?, updated_at = ?
            WHERE task_id = ?
            """,
            (state["status"], json.dumps(state, ensure_ascii=False), _ts(), task_id),
        )


def get_task_state(task_id: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT state_json FROM analysis_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
    return json.loads(row[0]) if row else None


def record_event(task_id: str, event_type: str, node: str, message: str, payload: dict) -> dict:
    init_db()
    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "node": node,
        "message": message,
        "payload": payload,
        "created_at": _ts(),
    }
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analysis_events (event_id, task_id, event_type, node, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                task_id,
                event["event_type"],
                event["node"],
                event["message"],
                json.dumps(event["payload"], ensure_ascii=False),
                event["created_at"],
            ),
        )
    return event


def list_task_events(task_id: str) -> list[dict]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_id, event_type, node, message, payload_json, created_at
            FROM analysis_events
            WHERE task_id = ?
            ORDER BY created_at ASC
            """,
            (task_id,),
        ).fetchall()

    return [
        {
            "event_id": row[0],
            "event_type": row[1],
            "node": row[2],
            "message": row[3],
            "payload": json.loads(row[4]),
            "created_at": row[5],
        }
        for row in rows
    ]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_analysis_store.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/database.py backend/app/storage/models.py backend/app/storage/analysis_store.py backend/app/schemas/analysis_schema.py backend/app/schemas/report_schema.py backend/app/schemas/event_schema.py backend/tests/test_analysis_store.py
git commit -m "feat: add analysis task persistence"
```

### Task 2: Add rule-based field matching and chart/report tools

**Files:**
- Create: `backend/app/tools/match_fields.py`
- Create: `backend/app/tools/chart_tool.py`
- Create: `backend/app/tools/report_tool.py`
- Test: `backend/tests/test_match_fields.py`
- Test: `backend/tests/test_chart_and_report_tools.py`

- [ ] **Step 1: Write the failing tool tests**

```python
# backend/tests/test_match_fields.py
from app.tools.match_fields import match_fields


def test_match_fields_detects_region_sales_question():
    file_profile = {
        "columns": [
            {"name": "region", "type": "string"},
            {"name": "sales_amount", "type": "number"},
            {"name": "channel", "type": "string"},
        ]
    }

    result = match_fields("analyse sales by region", file_profile)

    assert result["dimension_field"] == "region"
    assert result["metric_field"] == "sales_amount"
    assert result["aggregation"] == "sum"
```

```python
# backend/tests/test_chart_and_report_tools.py
from app.tools.chart_tool import generate_chart
from app.tools.report_tool import generate_report


def test_generate_chart_returns_bar_spec():
    rows = [
        {"region": "East", "sales_amount_sum": 1200},
        {"region": "West", "sales_amount_sum": 800},
    ]

    result = generate_chart(
        title="Sales by Region",
        x_field="region",
        y_field="sales_amount_sum",
        rows=rows,
    )

    assert result["chart_type"] == "bar"
    assert result["plotly_spec"]["data"][0]["type"] == "bar"


def test_generate_report_uses_tool_numbers():
    report = generate_report(
        question="analyse sales by region",
        analysis_goal="compare region sales",
        tool_result={
            "tool_name": "groupby_aggregate",
            "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
        },
        chart_spec={"chart_type": "bar"},
    )

    assert report["analysis_goal"] == "compare region sales"
    assert report["key_findings"][0]["source_tool"] == "groupby_aggregate"
    assert "1200" in report["key_findings"][0]["evidence"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_match_fields.py tests/test_chart_and_report_tools.py -v`
Expected: FAIL because the tools do not exist yet.

- [ ] **Step 3: Implement the tools**

```python
# backend/app/tools/match_fields.py
def match_fields(question: str, file_profile: dict) -> dict:
    lowered = question.lower()
    column_names = [column["name"] for column in file_profile["columns"]]

    def pick_dimension() -> str | None:
        keyword_pairs = [
            ("category", "product_category"),
            ("region", "region"),
            ("channel", "channel"),
        ]
        for keyword, field_name in keyword_pairs:
            if keyword in lowered and field_name in column_names:
                return field_name
        return None

    def pick_metric() -> tuple[str | None, str]:
        if "order" in lowered and "count" in lowered:
            return ("order_id" if "order_id" in column_names else None, "count")
        if "sales" in lowered and "sales_amount" in column_names:
            return ("sales_amount", "sum")
        return (None, "sum")

    dimension_field = pick_dimension()
    metric_field, aggregation = pick_metric()

    return {
        "dimension_field": dimension_field,
        "metric_field": metric_field,
        "aggregation": aggregation,
        "candidate_fields": column_names,
    }
```

```python
# backend/app/tools/chart_tool.py
def generate_chart(title: str, x_field: str, y_field: str, rows: list[dict]) -> dict:
    return {
        "chart_type": "bar",
        "plotly_spec": {
            "data": [
                {
                    "type": "bar",
                    "x": [row[x_field] for row in rows],
                    "y": [row[y_field] for row in rows],
                }
            ],
            "layout": {"title": title},
        },
    }
```

```python
# backend/app/tools/report_tool.py
def generate_report(question: str, analysis_goal: str, tool_result: dict, chart_spec: dict) -> dict:
    rows = tool_result["data"]["rows"]
    top_row = rows[0] if rows else {}
    top_dimension = next((value for key, value in top_row.items() if not key.endswith(("_sum", "_avg", "_count", "_min", "_max"))), "unknown")
    top_metric = next((value for key, value in top_row.items() if key.endswith(("_sum", "_avg", "_count", "_min", "_max"))), 0)

    return {
        "title": f"Analysis Report: {question}",
        "analysis_goal": analysis_goal,
        "key_findings": [
            {
                "finding": f"{top_dimension} performs best in the current result set",
                "evidence": f"The top row in the aggregation result is {top_dimension} with value {top_metric}",
                "source_tool": tool_result["tool_name"],
            }
        ],
        "chart_explanations": [f"Bar chart generated for {chart_spec['chart_type']} view."],
        "business_suggestions": ["Review the top-performing segment and compare it against weaker segments."],
        "data_limitations": ["This report reflects the uploaded CSV and the matched fields only."],
        "next_steps": ["Validate whether additional segmentation is needed for deeper analysis."],
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_match_fields.py tests/test_chart_and_report_tools.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/tools/match_fields.py backend/app/tools/chart_tool.py backend/app/tools/report_tool.py backend/tests/test_match_fields.py backend/tests/test_chart_and_report_tools.py
git commit -m "feat: add field matching and report tools"
```

### Task 3: Add synchronous analysis runner with events and tool logging

**Files:**
- Create: `backend/app/services/analysis_runner.py`
- Modify: `backend/app/storage/analysis_store.py`
- Test: `backend/tests/test_analysis_runner.py`

- [ ] **Step 1: Write the failing runner test**

```python
# backend/tests/test_analysis_runner.py
import json
from pathlib import Path

from app.services.analysis_runner import run_analysis_task
from app.storage.analysis_store import create_task, get_task_state
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord


def test_run_analysis_task_updates_state_and_events(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_task",
        "filename": "sales_orders.csv",
        "row_count": 2,
        "column_count": 3,
        "columns": [
            {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
        ],
        "created_at": "2026-06-09T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_task",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    create_task(
        "task_runner",
        "file_task",
        "analyse sales by region",
        {
            "task_id": "task_runner",
            "file_id": "file_task",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [],
            "analysis_plan": ["match fields", "aggregate", "chart", "report"],
            "current_step": "created",
            "completed_steps": [],
            "intermediate_findings": [],
            "tool_results": [],
            "chart_specs": [],
            "draft_report": {},
            "final_report": {},
            "eval_result": {},
            "events": [],
            "errors": [],
            "status": "created",
        },
    )

    result = run_analysis_task("task_runner")
    stored = get_task_state("task_runner")

    assert result["status"] == "completed"
    assert stored["status"] == "completed"
    assert stored["field_understanding"]["dimension_field"] == "region"
    assert stored["tool_results"][0]["tool_name"] == "groupby_aggregate"
    assert stored["chart_specs"][0]["chart_type"] == "bar"
    assert stored["final_report"]["analysis_goal"] == "compare region sales"
    assert any(event["event_type"] == "task_completed" for event in stored["events"])
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_analysis_runner.py -v`
Expected: FAIL because the analysis runner does not exist yet.

- [ ] **Step 3: Implement the runner and tool-call logging**

```python
# backend/app/storage/analysis_store.py
import json
import uuid
from datetime import datetime, timezone

from app.storage.database import get_connection, init_db


def _ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_task(task_id: str, file_id: str, question: str, state: dict) -> None:
    init_db()
    now = _ts()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO analysis_tasks (
                task_id, file_id, question, status, state_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, file_id, question, state["status"], json.dumps(state, ensure_ascii=False), now, now),
        )


def update_task_state(task_id: str, state: dict) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE analysis_tasks
            SET status = ?, state_json = ?, updated_at = ?
            WHERE task_id = ?
            """,
            (state["status"], json.dumps(state, ensure_ascii=False), _ts(), task_id),
        )


def get_task_state(task_id: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT state_json FROM analysis_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
    return json.loads(row[0]) if row else None


def record_event(task_id: str, event_type: str, node: str, message: str, payload: dict) -> dict:
    init_db()
    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "node": node,
        "message": message,
        "payload": payload,
        "created_at": _ts(),
    }
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analysis_events (event_id, task_id, event_type, node, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                task_id,
                event["event_type"],
                event["node"],
                event["message"],
                json.dumps(event["payload"], ensure_ascii=False),
                event["created_at"],
            ),
        )
    return event


def list_task_events(task_id: str) -> list[dict]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_id, event_type, node, message, payload_json, created_at
            FROM analysis_events
            WHERE task_id = ?
            ORDER BY created_at ASC
            """,
            (task_id,),
        ).fetchall()

    return [
        {
            "event_id": row[0],
            "event_type": row[1],
            "node": row[2],
            "message": row[3],
            "payload": json.loads(row[4]),
            "created_at": row[5],
        }
        for row in rows
    ]


def record_tool_call(task_id: str, tool_name: str, request: dict, response: dict) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tool_call_logs (log_id, task_id, tool_name, request_json, response_json, success, elapsed_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"log_{uuid.uuid4().hex[:12]}",
                task_id,
                tool_name,
                json.dumps(request, ensure_ascii=False),
                json.dumps(response, ensure_ascii=False),
                1 if response.get("success") else 0,
                int(response.get("metadata", {}).get("elapsed_ms", 0)),
                _ts(),
            ),
        )
```

```python
# backend/app/services/analysis_runner.py
from app.storage.analysis_store import get_task_state, list_task_events, record_event, record_tool_call, update_task_state
from app.tools.chart_tool import generate_chart
from app.tools.duckdb_tools import groupby_aggregate
from app.tools.match_fields import match_fields
from app.tools.report_tool import generate_report


def run_analysis_task(task_id: str) -> dict:
    state = get_task_state(task_id)
    if state is None:
        raise ValueError(f"Task {task_id} not found")

    state["status"] = "running"
    state["current_step"] = "match_fields"
    update_task_state(task_id, state)

    field_result = match_fields(state["question"], state["file_profile"])
    state["field_understanding"] = field_result
    record_event(task_id, "fields_matched", "match_fields", "matched analysis fields", field_result)

    tool_request = {
        "file_id": state["file_id"],
        "group_by": field_result["dimension_field"],
        "metric_column": field_result["metric_field"],
        "aggregation": field_result["aggregation"],
        "sort_order": "desc",
        "limit": 5,
    }
    record_event(task_id, "tool_called", "groupby_aggregate", "calling groupby_aggregate", tool_request)
    tool_response = groupby_aggregate(**tool_request)
    record_tool_call(task_id, "groupby_aggregate", tool_request, tool_response.model_dump())

    if not tool_response.success:
        state["tool_results"].append(tool_response.model_dump())
        state["errors"].append(tool_response.model_dump())
        state["status"] = "failed"
        record_event(task_id, "tool_failed", "groupby_aggregate", "groupby_aggregate failed", tool_response.model_dump())
        state["events"] = list_task_events(task_id)
        update_task_state(task_id, state)
        return state

    state["tool_results"].append(tool_response.model_dump())
    state["completed_steps"].append("groupby_aggregate")
    record_event(task_id, "tool_succeeded", "groupby_aggregate", "groupby_aggregate succeeded", tool_response.model_dump())

    rows = tool_response.data["rows"]
    y_field = next(key for key in rows[0].keys() if key != field_result["dimension_field"])
    chart_spec = generate_chart(
        title=f"{field_result['dimension_field']} vs {y_field}",
        x_field=field_result["dimension_field"],
        y_field=y_field,
        rows=rows,
    )
    state["chart_specs"].append(chart_spec)
    state["completed_steps"].append("generate_chart")
    record_event(task_id, "chart_generated", "generate_chart", "generated bar chart", chart_spec)

    report = generate_report(
        question=state["question"],
        analysis_goal=state["analysis_goal"],
        tool_result=tool_response.model_dump(),
        chart_spec=chart_spec,
    )
    state["final_report"] = report
    state["completed_steps"].append("generate_report")
    state["current_step"] = "completed"
    state["status"] = "completed"
    record_event(task_id, "report_generated", "generate_report", "generated final report", report)
    record_event(task_id, "task_completed", "run_analysis_task", "analysis task completed", {"status": "completed"})

    state["events"] = list_task_events(task_id)
    update_task_state(task_id, state)
    return state
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_analysis_runner.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/analysis_runner.py backend/app/storage/analysis_store.py backend/tests/test_analysis_runner.py
git commit -m "feat: add synchronous analysis runner"
```

### Task 4: Add analysis APIs and endpoint tests

**Files:**
- Create: `backend/app/api/analysis.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Write the failing API tests**

```python
# backend/tests/test_analysis_api.py
import json

from fastapi.testclient import TestClient

from app.main import app
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord


def test_start_analysis_creates_task(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("product_category,sales_amount\n electronics,1200\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_api",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=1,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
                ]
            ),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    client = TestClient(app)
    response = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api", "question": "analyse category sales top 5"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert response.json()["analysis_goal"] != ""
    assert len(response.json()["analysis_plan"]) > 0
```

```python
# backend/tests/test_analysis_api.py
def test_run_analysis_returns_completed_state(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_api_run",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(
                [
                    {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                ]
            ),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    client = TestClient(app)
    start = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api_run", "question": "analyse sales by region"},
    )
    task_id = start.json()["task_id"]

    run = client.post(f"/api/analysis/{task_id}/run")
    status = client.get(f"/api/analysis/{task_id}")
    events = client.get(f"/api/analysis/{task_id}/events")

    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert status.json()["task_id"] == task_id
    assert len(events.json()["events"]) > 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_analysis_api.py -v`
Expected: FAIL because analysis routes do not exist yet.

- [ ] **Step 3: Implement the analysis APIs**

```python
# backend/app/api/analysis.py
import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.analysis_schema import AnalysisStartRequest, AnalysisStartResponse, AnalysisTaskState
from app.schemas.event_schema import AnalysisEventList
from app.services.analysis_runner import run_analysis_task
from app.storage.analysis_store import create_task, get_task_state, list_task_events, record_event
from app.storage.file_store import get_file_record

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _build_goal_and_plan(question: str) -> tuple[str, list[str]]:
    lowered = question.lower()
    if "category" in lowered and "sales" in lowered:
        return ("compare product category sales performance", ["match fields", "aggregate category sales", "generate chart", "generate report"])
    if "region" in lowered and "sales" in lowered:
        return ("compare regional sales performance", ["match fields", "aggregate regional sales", "generate chart", "generate report"])
    if "channel" in lowered and ("sales" in lowered or "order" in lowered):
        return ("compare channel order and sales performance", ["match fields", "aggregate channel metrics", "generate chart", "generate report"])
    return ("perform grouped metric analysis on the uploaded file", ["match fields", "aggregate metric", "generate chart", "generate report"])


@router.post("/start", response_model=AnalysisStartResponse)
def start_analysis(request: AnalysisStartRequest) -> AnalysisStartResponse:
    file_record = get_file_record(request.file_id)
    if file_record is None:
        raise HTTPException(status_code=404, detail="File not found.")

    import json
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    file_profile = {
        "file_id": file_record.file_id,
        "filename": file_record.filename,
        "row_count": file_record.row_count,
        "column_count": file_record.column_count,
        "columns": json.loads(file_record.columns_json),
        "created_at": file_record.created_at,
    }
    analysis_goal, analysis_plan = _build_goal_and_plan(request.question)
    state = {
        "task_id": task_id,
        "file_id": request.file_id,
        "question": request.question,
        "analysis_goal": analysis_goal,
        "file_profile": file_profile,
        "field_understanding": {},
        "business_context": [],
        "analysis_plan": analysis_plan,
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "created",
    }
    create_task(task_id, request.file_id, request.question, state)
    record_event(task_id, "task_created", "start_analysis", "task created", {"status": "created"})
    record_event(task_id, "goal_understood", "start_analysis", "analysis goal generated", {"analysis_goal": analysis_goal})
    record_event(task_id, "plan_generated", "start_analysis", "analysis plan generated", {"analysis_plan": analysis_plan})
    return AnalysisStartResponse(task_id=task_id, status="created", analysis_goal=analysis_goal, analysis_plan=analysis_plan)


@router.post("/{task_id}/run", response_model=AnalysisTaskState)
def run_analysis(task_id: str) -> AnalysisTaskState:
    state = get_task_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return AnalysisTaskState(**run_analysis_task(task_id))


@router.get("/{task_id}", response_model=AnalysisTaskState)
def get_analysis(task_id: str) -> AnalysisTaskState:
    state = get_task_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    state["events"] = list_task_events(task_id)
    return AnalysisTaskState(**state)


@router.get("/{task_id}/events", response_model=AnalysisEventList)
def get_analysis_events(task_id: str) -> AnalysisEventList:
    state = get_task_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return AnalysisEventList(task_id=task_id, events=list_task_events(task_id))
```

```python
# backend/app/main.py
from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.files import router as files_router
from app.core.config import UPLOAD_DIR
from app.storage.database import init_db

app = FastAPI(title="Structured Table Analysis MVP")


@app.on_event("startup")
def startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


app.include_router(files_router)
app.include_router(analysis_router)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_analysis_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/analysis.py backend/app/main.py backend/tests/test_analysis_api.py
git commit -m "feat: add analysis task APIs"
```

### Task 5: Final verification for the closed loop

**Files:**
- Modify: `backend/README.md`
- Test: `backend/tests/test_analysis_store.py`
- Test: `backend/tests/test_match_fields.py`
- Test: `backend/tests/test_chart_and_report_tools.py`
- Test: `backend/tests/test_analysis_runner.py`
- Test: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Update README with analysis task usage**

```md
# Day 1 and Day 2 MVP Backend

## Scope

- CSV upload
- File profiling
- SQLite metadata persistence
- DuckDB groupby aggregation
- Analysis task creation and execution
- Event timeline query

## Analysis flow

1. Upload a CSV file with `/api/files/upload`
2. Create a task with `/api/analysis/start`
3. Run the task with `/api/analysis/{task_id}/run`
4. Query task state with `/api/analysis/{task_id}`
5. Query event timeline with `/api/analysis/{task_id}/events`
```

- [ ] **Step 2: Run the full backend test suite**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest -v`
Expected: PASS with all Day 1 and analysis-task tests passing.

- [ ] **Step 3: Verify a full manual API flow**

Run: `cd backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
Expected: server starts successfully.

Then verify:
- upload a CSV through `/docs`
- call `/api/analysis/start`
- call `/api/analysis/{task_id}/run`
- inspect `/api/analysis/{task_id}`
- inspect `/api/analysis/{task_id}/events`

Expected:
- task reaches `completed`
- `field_understanding`, `tool_results`, `chart_specs`, `final_report`, and `events` are populated

- [ ] **Step 4: Commit the documentation update**

```bash
git add backend/README.md
git commit -m "docs: document analysis task closed loop"
```

- [ ] **Step 5: Report exact verification evidence**

Report:
- full pytest result summary
- whether the local docs flow worked
- any known deviations from `DEVELOPMENT_GUIDE.md`
