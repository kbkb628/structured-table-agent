# DockerSandbox Trace Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make direct `POST /api/sandbox/execute` calls produce truthful persisted runtime evidence with classified failures, so sandbox execution is visible through a single authoritative runtime path.

**Architecture:** Keep DockerSandbox as a second-phase controlled capability. Add a dedicated sandbox execution persistence layer instead of overloading analysis-task tool logs, classify common execution failures inside the executor, and have sandbox status / project runtime overview read the latest persisted sandbox execution from that store.

**Tech Stack:** FastAPI, Pydantic, SQLite, existing sandbox executor, existing project-status runtime overview, pytest

---

### Task 1: Freeze failing acceptance tests for sandbox trace persistence and failure classification

**Files:**
- Create: `backend/tests/test_sandbox_store.py`
- Modify: `backend/tests/test_sandbox_executor.py`
- Modify: `backend/tests/test_sandbox_api.py`
- Modify: `backend/tests/test_project_status_api.py`

- [ ] **Step 1: Add a failing store round-trip test**

```python
from app.sandbox.store import get_latest_sandbox_execution
from app.sandbox.store import record_sandbox_execution


def test_record_sandbox_execution_round_trips_latest_execution():
    record_sandbox_execution(
        file_id="file_sandbox",
        request_payload={"python_code": "print('ok')"},
        response_payload={
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"summary": "ok"}',
            "stderr": "",
            "elapsed_ms": 33,
            "parsed_output": {"summary": "ok"},
            "degraded": False,
            "error": None,
        },
        execution_source="sandbox_api",
    )

    latest = get_latest_sandbox_execution()

    assert latest["file_id"] == "file_sandbox"
    assert latest["execution_source"] == "sandbox_api"
    assert latest["status"] == "completed"
    assert latest["parsed_output"]["summary"] == "ok"
```

- [ ] **Step 2: Add a failing executor classification test**

```python
def test_docker_sandbox_executor_classifies_syntax_error(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: True)
    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda command, timeout_seconds: {
            "returncode": 1,
            "stdout": "",
            "stderr": "SyntaxError: invalid syntax",
            "elapsed_ms": 21,
        },
    )

    result = executor.execute_python(code="if True print('x')", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "failed"
    assert result["error"]["code"] == "SANDBOX_SYNTAX_ERROR"
```

- [ ] **Step 3: Add a failing sandbox API persistence test**

```python
def test_sandbox_execute_endpoint_persists_latest_execution(monkeypatch):
    monkeypatch.setattr(
        "app.api.sandbox.execute_in_docker_sandbox",
        lambda file_id, python_code, timeout_seconds=None: {
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"summary": "ok"}',
            "stderr": "",
            "elapsed_ms": 48,
            "parsed_output": {"summary": "ok"},
            "degraded": False,
            "error": None,
        },
    )
    captured = {}
    monkeypatch.setattr(
        "app.api.sandbox.record_sandbox_execution",
        lambda **kwargs: captured.update(kwargs),
    )

    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "python_code": "print('ok')", "timeout_seconds": 8},
    )

    assert response.status_code == 200
    assert captured["file_id"] == "file_sandbox"
    assert captured["execution_source"] == "sandbox_api"
    assert captured["response_payload"]["status"] == "completed"
```

- [ ] **Step 4: Add a failing project-status latest sandbox execution test**

```python
def test_get_project_status_prefers_persisted_sandbox_execution(monkeypatch):
    monkeypatch.setattr(
        "app.api.project_status.describe_sandbox_runtime",
        lambda: {
            "enabled": True,
            "docker_available": True,
            "image": "python:3.12-slim",
            "network_disabled": True,
            "timeout_seconds": 8,
            "memory_limit_mb": 256,
            "cpu_limit": 1.0,
        },
    )
    monkeypatch.setattr(
        "app.api.project_status.get_latest_sandbox_execution",
        lambda: {
            "execution_id": "sandbox_exec_001",
            "file_id": "file_sandbox",
            "execution_source": "sandbox_api",
            "status": "failed",
            "elapsed_ms": 19,
            "error": {"code": "SANDBOX_SYNTAX_ERROR", "message": "SyntaxError: invalid syntax"},
            "created_at": "2026-06-24T10:00:00+00:00",
        },
    )

    client = TestClient(app)
    response = client.get("/api/project-status")

    sandbox = response.json()["summary"]["sandbox"]
    assert sandbox["latest_execution"]["execution_source"] == "sandbox_api"
    assert sandbox["latest_execution"]["error"]["code"] == "SANDBOX_SYNTAX_ERROR"
```

- [ ] **Step 5: Run focused tests to verify they fail first**

Run:

```powershell
Set-Location 'E:\bgagent1\.worktrees\day1-mvp-backend\backend'
@'
import sys
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend\.venv\Lib\site-packages")
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend")
import pytest
raise SystemExit(pytest.main([
    "-p", "no:cacheprovider",
    "--basetemp=E:\\bgagent1\\.worktrees\\day1-mvp-backend\\backend\\.pytest-tmp",
    "-q",
    "tests/test_sandbox_store.py",
    "tests/test_sandbox_executor.py",
    "tests/test_sandbox_api.py",
    "tests/test_project_status_api.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
```

Expected:

- `ModuleNotFoundError` for `app.sandbox.store` or
- missing persistence / classification assertions fail

- [ ] **Step 6: Commit the red test contract**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_sandbox_store.py backend/tests/test_sandbox_executor.py backend/tests/test_sandbox_api.py backend/tests/test_project_status_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze sandbox trace persistence behavior"
```

### Task 2: Add dedicated sandbox execution persistence and executor error classification

**Files:**
- Create: `backend/app/sandbox/store.py`
- Modify: `backend/app/storage/database.py`
- Modify: `backend/app/sandbox/executor.py`

- [ ] **Step 1: Add a dedicated SQLite table for sandbox execution logs**

```python
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sandbox_execution_logs (
                execution_id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                execution_source TEXT NOT NULL,
                request_json TEXT NOT NULL,
                response_json TEXT NOT NULL,
                success INTEGER NOT NULL,
                elapsed_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
```

- [ ] **Step 2: Implement a focused sandbox store module**

```python
import json
import uuid
from datetime import datetime, timezone

from app.storage.database import get_connection, init_db


def _ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def record_sandbox_execution(file_id: str, request_payload: dict, response_payload: dict, execution_source: str) -> str:
    init_db()
    execution_id = f"sandbox_exec_{uuid.uuid4().hex[:12]}"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sandbox_execution_logs (
                execution_id, file_id, execution_source, request_json, response_json, success, elapsed_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                file_id,
                execution_source,
                json.dumps(request_payload, ensure_ascii=False),
                json.dumps(response_payload, ensure_ascii=False),
                1 if response_payload.get("status") == "completed" else 0,
                int(response_payload.get("elapsed_ms", 0) or 0),
                _ts(),
            ),
        )
    return execution_id
```

- [ ] **Step 3: Add latest-execution read helper**

```python
def get_latest_sandbox_execution() -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT execution_id, file_id, execution_source, request_json, response_json, success, elapsed_ms, created_at
            FROM sandbox_execution_logs
            ORDER BY created_at DESC, rowid DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    response_payload = json.loads(row[4]) if row[4] else {}
    return {
        "execution_id": row[0],
        "file_id": row[1],
        "execution_source": row[2],
        "success": bool(row[5]),
        "elapsed_ms": int(row[6] or 0),
        "created_at": row[7],
        **response_payload,
    }
```

- [ ] **Step 4: Add explicit error classification inside the executor**

```python
def _classify_execution_failure(stderr: str) -> tuple[str, str]:
    lowered = (stderr or "").lower()
    if "syntaxerror" in lowered:
        return "SANDBOX_SYNTAX_ERROR", stderr.strip() or "Sandbox Python code has invalid syntax."
    if "importerror" in lowered or "modulenotfounderror" in lowered:
        return "SANDBOX_IMPORT_ERROR", stderr.strip() or "Sandbox code imports an unavailable module."
    if "permissionerror" in lowered or "read-only file system" in lowered:
        return "SANDBOX_PERMISSION_ERROR", stderr.strip() or "Sandbox code attempted a blocked filesystem operation."
    return "SANDBOX_EXECUTION_FAILED", stderr.strip() or "Sandbox execution failed."
```

- [ ] **Step 5: Use the classifier in failed executor results**

```python
        error_code, error_message = _classify_execution_failure(stderr)
        return {
            "status": "completed" if returncode == 0 else "failed",
            ...
            "error": None
            if returncode == 0
            else {
                "code": error_code,
                "message": error_message,
                "suggested_fields": [],
            },
        }
```

- [ ] **Step 6: Run focused tests to verify green**

Run the same focused test command from Task 1.

Expected:

- sandbox store round-trip passes
- executor syntax/import/permission classification passes
- no API contract regressions

- [ ] **Step 7: Commit the persistence and classification layer**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/storage/database.py backend/app/sandbox/store.py backend/app/sandbox/executor.py backend/tests/test_sandbox_store.py backend/tests/test_sandbox_executor.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: persist sandbox executions and classify failures"
```

### Task 3: Wire persisted sandbox evidence into API and project runtime overview

**Files:**
- Modify: `backend/app/api/sandbox.py`
- Modify: `backend/app/api/project_status.py`
- Modify: `backend/tests/test_sandbox_api.py`
- Modify: `backend/tests/test_project_status_api.py`

- [ ] **Step 1: Persist direct sandbox API executions after each run**

```python
from app.sandbox.store import record_sandbox_execution


@router.post("/api/sandbox/execute")
def run_sandbox_execution(request: SandboxExecutionRequest) -> dict:
    response = execute_in_docker_sandbox(
        file_id=request.file_id,
        python_code=request.python_code,
        timeout_seconds=request.timeout_seconds,
    )
    record_sandbox_execution(
        file_id=request.file_id,
        request_payload=request.model_dump(),
        response_payload=response,
        execution_source="sandbox_api",
    )
    return response
```

- [ ] **Step 2: Read latest sandbox execution from the dedicated store**

```python
from app.sandbox.store import get_latest_sandbox_execution


def _sandbox_info() -> dict:
    runtime = describe_sandbox_runtime()
    return {
        **runtime,
        "latest_execution": get_latest_sandbox_execution(),
    }
```

- [ ] **Step 3: Keep status endpoint response aligned with the same persisted latest execution**

```python
@router.get("/api/sandbox/status")
def get_sandbox_status() -> dict:
    return {
        **describe_sandbox_runtime(),
        "latest_execution": get_latest_sandbox_execution(),
    }
```

- [ ] **Step 4: Re-run focused sandbox and project-status tests**

Run:

```powershell
Set-Location 'E:\bgagent1\.worktrees\day1-mvp-backend\backend'
@'
import sys
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend\.venv\Lib\site-packages")
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend")
import pytest
raise SystemExit(pytest.main([
    "-p", "no:cacheprovider",
    "--basetemp=E:\\bgagent1\\.worktrees\\day1-mvp-backend\\backend\\.pytest-tmp",
    "-q",
    "tests/test_sandbox_store.py",
    "tests/test_sandbox_executor.py",
    "tests/test_sandbox_api.py",
    "tests/test_project_status_api.py",
    "tests/test_demo_page.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
```

Expected:

- focused sandbox and runtime overview tests all pass

- [ ] **Step 5: Commit API/runtime overview wiring**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/sandbox.py backend/app/api/project_status.py backend/tests/test_sandbox_api.py backend/tests/test_project_status_api.py backend/tests/test_demo_page.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: expose persisted sandbox execution evidence"
```

### Task 4: Update delivery wording and verify the full backend suite

**Files:**
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `docs/INTERVIEW_GUIDE.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add wording that direct sandbox API executions now persist latest runtime evidence**

```markdown
- Direct `POST /api/sandbox/execute` calls now persist execution evidence into a dedicated sandbox execution store.
- `GET /api/sandbox/status` and `GET /api/project-status` expose the latest persisted sandbox execution, including classified failure codes.
```

- [ ] **Step 2: Extend delivery doc tests**

```python
assert "latest persisted sandbox execution" in content
assert "SANDBOX_SYNTAX_ERROR" in content or "classified failure codes" in content
```

- [ ] **Step 3: Run full backend verification**

Run:

```powershell
Set-Location 'E:\bgagent1\.worktrees\day1-mvp-backend\backend'
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
New-Item -ItemType Directory -Force '.pytest-tmp' | Out-Null
@'
import sys
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend\.venv\Lib\site-packages")
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend")
import pytest
raise SystemExit(pytest.main([
    "-p", "no:cacheprovider",
    "--basetemp=E:\\bgagent1\\.worktrees\\day1-mvp-backend\\backend\\.pytest-tmp",
    "-q",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
```

Expected:

- full suite passes
- sandbox latest execution is now backed by dedicated persisted evidence instead of only tool-call side effects

- [ ] **Step 4: Commit docs and verification alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md docs/INTERVIEW_GUIDE.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align sandbox trace persistence evidence"
```
