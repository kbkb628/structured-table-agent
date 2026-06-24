# DockerSandbox Evidence Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make persisted `latest_execution` evidence more truthful and easier to demo by surfacing execution mode, template identity, and code-size summary instead of only raw response payload fields.

**Architecture:** Keep the existing sandbox execution store schema unchanged and derive a stable outward-facing summary from stored `request_json`. Add a small extraction layer in the sandbox store so `/api/sandbox/status`, `GET /api/project-status`, and `/demo` can expose `execution_mode`, `template_name`, and `python_code_char_count` without leaking raw code into runtime summaries.

**Tech Stack:** FastAPI, SQLite, existing sandbox store/runtime overview, pytest

---

### Task 1: Freeze failing tests for persisted sandbox evidence summaries

**Files:**
- Modify: `backend/tests/test_sandbox_store.py`
- Modify: `backend/tests/test_sandbox_api.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_demo_page.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add a failing sandbox store summary test**

```python
def test_record_sandbox_execution_surfaces_execution_summary_fields():
    record_sandbox_execution(
        file_id="file_sandbox_template",
        request_payload={
            "python_code": "print('templated')",
            "template_name": "region_sales_summary",
            "timeout_seconds": 8,
        },
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

    assert latest["execution_mode"] == "template"
    assert latest["template_name"] == "region_sales_summary"
    assert latest["python_code_char_count"] == len("print('templated')")
```

- [ ] **Step 2: Add a failing sandbox API persistence-shape test**

```python
def test_sandbox_execute_endpoint_persists_execution_mode_summary(monkeypatch):
    monkeypatch.setattr(
        "app.api.sandbox.execute_in_docker_sandbox",
        lambda file_id, python_code, timeout_seconds=None: {
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"summary": "ok"}',
            "stderr": "",
            "elapsed_ms": 40,
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
        json={"file_id": "file_sandbox", "template_name": "region_sales_summary", "timeout_seconds": 8},
    )

    assert response.status_code == 200
    assert captured["request_payload"]["template_name"] == "region_sales_summary"
```

- [ ] **Step 3: Add failing runtime summary tests for project-status and demo**

```python
def test_get_project_status_surfaces_sandbox_execution_summary_fields(monkeypatch):
    monkeypatch.setattr(
        "app.api.project_status._sandbox_info",
        lambda: {
            "enabled": True,
            "docker_available": True,
            "image": "python:3.12-slim",
            "network_disabled": True,
            "timeout_seconds": 8,
            "max_timeout_seconds": 8,
            "max_code_chars": 4000,
            "supported_templates": ["region_sales_summary", "channel_sales_summary"],
            "latest_execution": {
                "execution_id": "sandbox_exec_001",
                "file_id": "file_sandbox",
                "execution_source": "sandbox_api",
                "execution_mode": "template",
                "template_name": "region_sales_summary",
                "python_code_char_count": 18,
                "status": "completed",
                "elapsed_ms": 19,
                "created_at": "2026-06-24T10:00:00+00:00",
            },
        },
    )

    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    latest_execution = response.json()["summary"]["sandbox"]["latest_execution"]
    assert latest_execution["execution_mode"] == "template"
    assert latest_execution["template_name"] == "region_sales_summary"
    assert latest_execution["python_code_char_count"] == 18
```

```python
assert "execution_mode" in content
assert "python_code_char_count" in content
```

- [ ] **Step 4: Add failing delivery-doc assertions**

```python
assert "execution_mode" in project_status
assert "template_name" in resume_description
assert "python_code_char_count" in evidence_map
```

- [ ] **Step 5: Run focused tests to verify red**

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
    "tests/test_sandbox_store.py",
    "tests/test_sandbox_api.py",
    "tests/test_project_status_api.py",
    "tests/test_demo_page.py",
    "tests/test_delivery_docs.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- store tests fail because summary fields are not exposed yet, or
- demo/doc tests fail because the new evidence-summary fields are not mentioned yet

- [ ] **Step 6: Commit the red tests**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_sandbox_store.py backend/tests/test_sandbox_api.py backend/tests/test_project_status_api.py backend/tests/test_demo_page.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze sandbox evidence summary behavior"
```

### Task 2: Implement persisted sandbox evidence summary extraction

**Files:**
- Modify: `backend/app/sandbox/store.py`

- [ ] **Step 1: Add a focused request-summary extractor**

```python
def _summarize_request_payload(request_payload: dict) -> dict:
    python_code = request_payload.get("python_code") or ""
    template_name = request_payload.get("template_name")
    return {
        "execution_mode": "template" if template_name else "inline_python",
        "template_name": template_name,
        "python_code_char_count": len(python_code),
    }
```

- [ ] **Step 2: Merge the summary into persisted latest execution output**

```python
    request_payload = json.loads(row[3]) if row[3] else {}
    response_payload = json.loads(row[4]) if row[4] else {}
    return {
        "execution_id": row[0],
        "file_id": row[1],
        "execution_source": row[2],
        "success": bool(row[5]),
        "elapsed_ms": int(row[6] or 0),
        "created_at": row[7],
        **_summarize_request_payload(request_payload),
        **response_payload,
    }
```

- [ ] **Step 3: Run focused tests to verify green**

Run the same focused command from Task 1.

Expected:

- latest sandbox execution now exposes execution summary fields
- no API contract breaks for existing response fields

- [ ] **Step 4: Commit the store summary implementation**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/sandbox/store.py backend/tests/test_sandbox_store.py backend/tests/test_sandbox_api.py backend/tests/test_project_status_api.py backend/tests/test_demo_page.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: summarize persisted sandbox execution evidence"
```

### Task 3: Sync demo and delivery docs to the new runtime evidence fields

**Files:**
- Modify: `backend/app/api/demo.py`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Make demo sandbox wording mention the new summary fields**

```javascript
sandboxMetaEl.textContent = "DockerSandbox runtime summary, supported_templates, execution_mode, template_name, and python_code_char_count will appear here.";
```

- [ ] **Step 2: Add truthful doc wording**

```markdown
- Latest persisted sandbox evidence now exposes `execution_mode`, `template_name`, and `python_code_char_count`, so demos can distinguish template-backed execution from inline Python without exposing raw code bodies.
```

- [ ] **Step 3: Re-run focused tests and full backend verification**

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
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- full backend suite passes
- runtime evidence wording remains truthful and controlled

- [ ] **Step 4: Commit doc alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/demo.py docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align sandbox evidence summary fields"
```
