# Day 1 MVP Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Day 1 MVP backend closed loop from the development guide: upload a real sales-order CSV, generate and persist a real file profile, and run a real `groupby_aggregate` tool over the uploaded CSV.

**Architecture:** Implement a small FastAPI backend under `backend/` with clear module boundaries for HTTP, schemas, persistence, and tools. Persist file metadata and profile JSON in SQLite, use pandas for CSV profiling, and use DuckDB for deterministic aggregation so Day 2 can extend the same skeleton without restructuring.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pandas, DuckDB, SQLite, pytest, uv

---

### Task 1: Bootstrap the backend project skeleton

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/exceptions.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/tools/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write the failing startup test**

```python
# backend/tests/conftest.py
from fastapi.testclient import TestClient

from app.main import app


def create_client() -> TestClient:
    return TestClient(app)
```

- [ ] **Step 2: Run test import to verify it fails**

Run: `cd backend && uv run python -c "from tests.conftest import create_client"`
Expected: FAIL with `ModuleNotFoundError` because `app.main` does not exist yet.

- [ ] **Step 3: Write the minimal project files**

```toml
# backend/pyproject.toml
[project]
name = "bgagent1-backend"
version = "0.1.0"
description = "Day 1 MVP backend for structured table analysis agent"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0,<1.0.0",
  "uvicorn>=0.30.0,<1.0.0",
  "python-multipart>=0.0.9,<1.0.0",
  "pandas>=2.2.0,<3.0.0",
  "duckdb>=1.0.0,<2.0.0",
]

[dependency-groups]
dev = [
  "pytest>=8.2.0,<9.0.0",
  "httpx>=0.27.0,<1.0.0",
]
```

```python
# backend/app/core/config.py
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "samples"
DB_PATH = BASE_DIR / "app.db"
```

```python
# backend/app/core/exceptions.py
class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)
```

```python
# backend/app/main.py
from fastapi import FastAPI

from app.core.config import UPLOAD_DIR

app = FastAPI(title="Structured Table Analysis MVP")


@app.on_event("startup")
def startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Install dependencies and verify import succeeds**

Run: `cd backend && uv sync`
Expected: environment created successfully.

Run: `cd backend && uv run python -c "from tests.conftest import create_client; print(type(create_client()).__name__)"`
Expected: prints `TestClient`.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app backend/tests/conftest.py
git commit -m "chore: bootstrap day1 backend skeleton"
```

### Task 2: Add SQLite persistence for uploaded file metadata

**Files:**
- Create: `backend/app/storage/database.py`
- Create: `backend/app/storage/models.py`
- Create: `backend/app/storage/file_store.py`
- Create: `backend/tests/test_file_store.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing file-store test**

```python
# backend/tests/test_file_store.py
from app.storage.file_store import save_file_record, get_file_record
from app.storage.models import FileRecord


def test_file_record_roundtrip(tmp_path):
    record = FileRecord(
        file_id="file_test",
        filename="sales_orders.csv",
        stored_path=str(tmp_path / "sales_orders.csv"),
        row_count=3,
        column_count=2,
        columns_json="[]",
        created_at="2026-06-08T18:00:00",
    )

    save_file_record(record)
    loaded = get_file_record("file_test")

    assert loaded is not None
    assert loaded.file_id == "file_test"
    assert loaded.filename == "sales_orders.csv"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && uv run pytest tests/test_file_store.py -v`
Expected: FAIL because `app.storage.file_store` and related persistence code do not exist.

- [ ] **Step 3: Implement minimal SQLite persistence**

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
```

```python
# backend/app/storage/file_store.py
from app.storage.database import get_connection
from app.storage.models import FileRecord


def save_file_record(record: FileRecord) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO files (
                file_id, filename, stored_path, row_count, column_count, columns_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.file_id,
                record.filename,
                record.stored_path,
                record.row_count,
                record.column_count,
                record.columns_json,
                record.created_at,
            ),
        )


def get_file_record(file_id: str) -> FileRecord | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT file_id, filename, stored_path, row_count, column_count, columns_json, created_at
            FROM files
            WHERE file_id = ?
            """,
            (file_id,),
        ).fetchone()

    return FileRecord(*row) if row else None
```

```python
# backend/app/main.py
from fastapi import FastAPI

from app.core.config import UPLOAD_DIR
from app.storage.database import init_db

app = FastAPI(title="Structured Table Analysis MVP")


@app.on_event("startup")
def startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend && uv run pytest tests/test_file_store.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/storage backend/tests/test_file_store.py
git commit -m "feat: add sqlite file metadata store"
```

### Task 3: Implement CSV profiling schemas and utility

**Files:**
- Create: `backend/app/schemas/file_schema.py`
- Create: `backend/app/tools/data_profile.py`
- Create: `backend/tests/test_data_profile.py`

- [ ] **Step 1: Write the failing profile test**

```python
# backend/tests/test_data_profile.py
from pathlib import Path

from app.tools.data_profile import build_file_profile


def test_build_file_profile_returns_expected_shape(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount,order_status\n"
        "electronics,1200,completed\n"
        "office,800,cancelled\n",
        encoding="utf-8",
    )

    profile = build_file_profile(csv_path)

    assert profile.row_count == 2
    assert profile.column_count == 3
    assert profile.columns[0].name == "product_category"
    assert profile.columns[1].type == "number"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && uv run pytest tests/test_data_profile.py -v`
Expected: FAIL because the profiling schema and utility are missing.

- [ ] **Step 3: Implement the schemas and profile utility**

```python
# backend/app/schemas/file_schema.py
from pydantic import BaseModel


class ColumnProfile(BaseModel):
    name: str
    type: str
    missing_rate: float
    sample_values: list[str]
    unique_count: int


class FileProfile(BaseModel):
    file_id: str
    filename: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    created_at: str
```

```python
# backend/app/tools/data_profile.py
from pathlib import Path

import pandas as pd

from app.schemas.file_schema import ColumnProfile, FileProfile


def _map_dtype(dtype: str) -> str:
    if "int" in dtype or "float" in dtype:
        return "number"
    return "string"


def build_file_profile(csv_path: Path, file_id: str = "", created_at: str = "", filename: str | None = None) -> FileProfile:
    df = pd.read_csv(csv_path)
    columns: list[ColumnProfile] = []
    for column_name in df.columns:
        series = df[column_name]
        samples = [str(value) for value in series.dropna().head(3).tolist()]
        columns.append(
            ColumnProfile(
                name=column_name,
                type=_map_dtype(str(series.dtype)),
                missing_rate=round(float(series.isna().mean()), 4),
                sample_values=samples,
                unique_count=int(series.nunique(dropna=True)),
            )
        )

    return FileProfile(
        file_id=file_id,
        filename=filename or csv_path.name,
        row_count=int(len(df)),
        column_count=int(len(df.columns)),
        columns=columns,
        created_at=created_at,
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend && uv run pytest tests/test_data_profile.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/file_schema.py backend/app/tools/data_profile.py backend/tests/test_data_profile.py
git commit -m "feat: add csv profiling utility"
```

### Task 4: Implement file upload and profile query APIs

**Files:**
- Create: `backend/app/api/files.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/storage/file_store.py`
- Modify: `backend/app/core/exceptions.py`
- Create: `backend/tests/test_files_api.py`

- [ ] **Step 1: Write the failing API tests**

```python
# backend/tests/test_files_api.py
from fastapi.testclient import TestClient

from app.main import app


def test_upload_csv_returns_profile(tmp_path):
    client = TestClient(app)
    response = client.post(
        "/api/files/upload",
        files={"file": ("sales_orders.csv", "product_category,sales_amount\nelectronics,1000\n", "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "sales_orders.csv"
    assert body["row_count"] == 1
    assert body["column_count"] == 2
    assert body["columns"][0]["name"] == "product_category"


def test_get_profile_returns_persisted_profile():
    client = TestClient(app)
    upload_response = client.post(
        "/api/files/upload",
        files={"file": ("sales_orders.csv", "product_category,sales_amount\nelectronics,1000\n", "text/csv")},
    )
    file_id = upload_response.json()["file_id"]

    profile_response = client.get(f"/api/files/{file_id}/profile")

    assert profile_response.status_code == 200
    assert profile_response.json()["file_id"] == file_id
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_files_api.py -v`
Expected: FAIL because the routes are not registered.

- [ ] **Step 3: Implement the file APIs**

```python
# backend/app/storage/file_store.py
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import UPLOAD_DIR
from app.storage.database import get_connection
from app.storage.models import FileRecord


def persist_uploaded_file(filename: str, content: bytes) -> Path:
    stored_path = UPLOAD_DIR / filename
    stored_path.write_bytes(content)
    return stored_path


def make_file_id() -> str:
    return f"file_{uuid.uuid4().hex[:12]}"


def make_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
```

```python
# backend/app/api/files.py
import json

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.file_schema import FileProfile
from app.storage.file_store import (
    get_file_record,
    make_file_id,
    make_timestamp,
    persist_uploaded_file,
    save_file_record,
)
from app.storage.models import FileRecord
from app.tools.data_profile import build_file_profile

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileProfile)
async def upload_file(file: UploadFile = File(...)) -> FileProfile:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_id = make_file_id()
    stored_name = f"{file_id}_{file.filename}"
    full_path = persist_uploaded_file(stored_name, content)
    created_at = make_timestamp()
    profile = build_file_profile(full_path, file_id=file_id, created_at=created_at, filename=file.filename)

    save_file_record(
        FileRecord(
            file_id=profile.file_id,
            filename=profile.filename,
            stored_path=str(full_path),
            row_count=profile.row_count,
            column_count=profile.column_count,
            columns_json=json.dumps([item.model_dump() for item in profile.columns], ensure_ascii=False),
            created_at=profile.created_at,
        )
    )
    return profile


@router.get("/{file_id}/profile", response_model=FileProfile)
def get_profile(file_id: str) -> FileProfile:
    record = get_file_record(file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="File profile not found.")

    return FileProfile(
        file_id=record.file_id,
        filename=record.filename,
        row_count=record.row_count,
        column_count=record.column_count,
        columns=json.loads(record.columns_json),
        created_at=record.created_at,
    )
```

```python
# backend/app/main.py
from fastapi import FastAPI

from app.api.files import router as files_router
from app.core.config import UPLOAD_DIR
from app.storage.database import init_db

app = FastAPI(title="Structured Table Analysis MVP")


@app.on_event("startup")
def startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


app.include_router(files_router)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_files_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/files.py backend/app/main.py backend/app/storage/file_store.py backend/tests/test_files_api.py
git commit -m "feat: add csv upload and profile endpoints"
```

### Task 5: Add unified ToolResponse and DuckDB aggregation tool

**Files:**
- Create: `backend/app/schemas/tool_schema.py`
- Create: `backend/app/tools/duckdb_tools.py`
- Create: `backend/tests/test_duckdb_tools.py`

- [ ] **Step 1: Write the failing aggregation test**

```python
# backend/tests/test_duckdb_tools.py
import json
from pathlib import Path

from app.storage.file_store import save_file_record
from app.storage.models import FileRecord
from app.tools.duckdb_tools import groupby_aggregate


def test_groupby_aggregate_returns_top5(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "electronics,1200\n"
        "office,800\n"
        "electronics,500\n",
        encoding="utf-8",
    )

    save_file_record(
        FileRecord(
            file_id="file_agg",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=3,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
                ],
                ensure_ascii=False,
            ),
            created_at="2026-06-08T18:00:00",
        )
    )

    result = groupby_aggregate(
        file_id="file_agg",
        group_by="product_category",
        metric_column="sales_amount",
        aggregation="sum",
        sort_order="desc",
        limit=5,
    )

    assert result.success is True
    assert result.data["rows"][0]["product_category"] == "electronics"
    assert result.data["rows"][0]["sales_amount_sum"] == 1700
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && uv run pytest tests/test_duckdb_tools.py -v`
Expected: FAIL because the tool schema and DuckDB tool do not exist.

- [ ] **Step 3: Implement unified ToolResponse and aggregation**

```python
# backend/app/schemas/tool_schema.py
from typing import Any

from pydantic import BaseModel


class ToolError(BaseModel):
    code: str
    message: str
    suggested_fields: list[str] = []


class ToolResponse(BaseModel):
    success: bool
    tool_name: str
    data: dict[str, Any] | None
    summary: str
    error: ToolError | None
    metadata: dict[str, Any]
```

```python
# backend/app/tools/duckdb_tools.py
import json
import time

import duckdb

from app.schemas.tool_schema import ToolError, ToolResponse
from app.storage.file_store import get_file_record


ALLOWED_AGGREGATIONS = {"sum", "avg", "count", "min", "max"}
ALLOWED_SORT_ORDERS = {"asc", "desc"}


def groupby_aggregate(
    file_id: str,
    group_by: str,
    metric_column: str,
    aggregation: str,
    sort_order: str,
    limit: int = 10,
) -> ToolResponse:
    started = time.perf_counter()
    if aggregation not in ALLOWED_AGGREGATIONS:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(code="INVALID_AGGREGATION", message=f"Unsupported aggregation: {aggregation}", suggested_fields=[]),
            metadata={"elapsed_ms": 0},
        )
    if sort_order not in ALLOWED_SORT_ORDERS:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(code="INVALID_SORT_ORDER", message=f"Unsupported sort_order: {sort_order}", suggested_fields=[]),
            metadata={"elapsed_ms": 0},
        )

    record = get_file_record(file_id)
    if record is None:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(code="FILE_NOT_FOUND", message=f"File {file_id} was not found", suggested_fields=[]),
            metadata={"elapsed_ms": 0},
        )

    columns = {item["name"]: item for item in json.loads(record.columns_json)}
    if group_by not in columns:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(code="FIELD_NOT_FOUND", message=f"Field {group_by} was not found", suggested_fields=list(columns.keys())),
            metadata={"elapsed_ms": 0},
        )
    if metric_column not in columns:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(code="FIELD_NOT_FOUND", message=f"Field {metric_column} was not found", suggested_fields=list(columns.keys())),
            metadata={"elapsed_ms": 0},
        )
    if columns[metric_column]["type"] != "number" and aggregation in {"sum", "avg", "min", "max"}:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="NON_NUMERIC_METRIC",
                message=f"Field {metric_column} must be numeric for {aggregation}",
                suggested_fields=[],
            ),
            metadata={"elapsed_ms": 0},
        )

    sql = f'''
        SELECT "{group_by}" AS "{group_by}", {aggregation}("{metric_column}") AS "{metric_column}_{aggregation}"
        FROM read_csv_auto(?)
        GROUP BY 1
        ORDER BY 2 {sort_order.upper()}
        LIMIT ?
    '''
    rows = duckdb.execute(sql, [record.stored_path, limit]).fetchdf().to_dict(orient="records")
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ToolResponse(
        success=True,
        tool_name="groupby_aggregate",
        data={"rows": rows},
        summary="aggregate rows grouped by the requested dimension",
        error=None,
        metadata={
            "columns_used": [group_by, metric_column],
            "row_count": len(rows),
            "elapsed_ms": elapsed_ms,
        },
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend && uv run pytest tests/test_duckdb_tools.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/tool_schema.py backend/app/tools/duckdb_tools.py backend/tests/test_duckdb_tools.py
git commit -m "feat: add duckdb aggregation tool"
```

### Task 6: Add sample data, README, and final Day 1 verification

**Files:**
- Create: `backend/data/samples/sales_orders.csv`
- Create: `backend/README.md`
- Modify: `backend/tests/test_files_api.py`

- [ ] **Step 1: Add sample data that matches the guide**

```csv
order_id,customer_id,order_date,region,channel,product_category,product_name,quantity,sales_amount,discount,order_status
ORD001,C001,2026-06-01,East,Online,electronics,earbuds,2,1200,0.05,completed
ORD002,C002,2026-06-01,North,Retail,office,printer_paper,5,300,0.00,completed
ORD003,C003,2026-06-02,South,Distributor,home,desk_lamp,1,260,0.10,refunded
ORD004,C004,2026-06-02,West,Online,apparel,sports_jacket,1,450,0.15,cancelled
ORD005,C005,2026-06-03,East,Retail,food,coffee_beans,3,180,0.00,completed
ORD006,C006,2026-06-03,North,Online,electronics,mechanical_keyboard,1,700,0.08,completed
```

- [ ] **Step 2: Add a minimal README for Day 1**

```md
# Day 1 MVP Backend

## Scope

- CSV upload
- File profiling
- SQLite metadata persistence
- DuckDB groupby aggregation

## Setup

~~~powershell
cd E:\bgagent1\backend
uv sync
uv run uvicorn app.main:app --reload
~~~

## pip alternative

~~~powershell
cd E:\bgagent1\backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload
~~~

## Tests

~~~powershell
cd E:\bgagent1\backend
uv run pytest
~~~
```

- [ ] **Step 3: Run the full Day 1 verification**

Run: `cd backend && uv run pytest tests/test_file_store.py tests/test_data_profile.py tests/test_files_api.py tests/test_duckdb_tools.py -v`
Expected: all tests PASS.

Run: `cd backend && uv run uvicorn app.main:app --reload`
Expected: server starts successfully and Swagger is available at `http://127.0.0.1:8000/docs`.

- [ ] **Step 4: Record the delivery status in git**

```bash
git add backend/data/samples/sales_orders.csv backend/README.md
git commit -m "docs: add day1 sample data and verification notes"
```

- [ ] **Step 5: Stop and report real verification output**

Report:
- exact pytest result summary
- whether Swagger started successfully
- any deviations from `DEVELOPMENT_GUIDE.md`

