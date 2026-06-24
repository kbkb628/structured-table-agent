# DockerSandbox Template Result Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make template-backed sandbox runs easier to inspect by exposing a stable summarized view of parsed template outputs in `latest_execution`.

**Architecture:** Keep the sandbox execution API and persistence schema unchanged. Derive a lightweight outward-facing result summary from stored `response_json`, expose it alongside the existing execution summary fields, and surface the new fields in demo/runtime docs without replacing the raw `parsed_output`.

**Tech Stack:** FastAPI, SQLite, existing sandbox store/runtime overview, pytest

---

### Task 1: Freeze failing tests for template result summaries

**Files:**
- Modify: `backend/tests/test_sandbox_store.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_demo_page.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add a failing sandbox store result-summary test**

```python
def test_record_sandbox_execution_surfaces_template_result_summary():
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
            "stdout": '{"template_name":"region_sales_summary","top_region":"East","top_sales_amount":1200.0,"region_count":4}',
            "stderr": "",
            "elapsed_ms": 33,
            "parsed_output": {
                "template_name": "region_sales_summary",
                "top_region": "East",
                "top_sales_amount": 1200.0,
                "region_count": 4,
            },
            "degraded": False,
            "error": None,
        },
        execution_source="sandbox_api",
    )

    latest = get_latest_sandbox_execution()

    assert latest["parsed_output_keys"] == [
        "region_count",
        "template_name",
        "top_region",
        "top_sales_amount",
    ]
    assert latest["template_result_field_count"] == 3
    assert latest["template_result_summary"]["top_region"] == "East"
```

- [ ] **Step 2: Add a failing project-status summary-field test**

```python
def test_get_project_status_surfaces_template_result_summary_fields(monkeypatch):
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
                "parsed_output_keys": ["region_count", "template_name", "top_region", "top_sales_amount"],
                "template_result_field_count": 3,
                "template_result_summary": {
                    "top_region": "East",
                    "top_sales_amount": 1200.0,
                    "region_count": 4,
                },
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
    assert latest_execution["parsed_output_keys"][-1] == "top_sales_amount"
    assert latest_execution["template_result_field_count"] == 3
    assert latest_execution["template_result_summary"]["region_count"] == 4
```

- [ ] **Step 3: Add failing demo/docs assertions**

```python
assert "parsed_output_keys" in content
assert "template_result_summary" in content
```

```python
assert "template_result_summary" in project_status
assert "parsed_output_keys" in resume_description
assert "template_result_field_count" in evidence_map
```

- [ ] **Step 4: Run focused tests to verify red**

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

- store tests fail because template result summary fields are missing, or
- demo/doc tests fail because the new result-summary fields are not surfaced yet

- [ ] **Step 5: Commit the red tests**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_sandbox_store.py backend/tests/test_project_status_api.py backend/tests/test_demo_page.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze sandbox template result summary behavior"
```

### Task 2: Implement template result summary extraction

**Files:**
- Modify: `backend/app/sandbox/store.py`

- [ ] **Step 1: Add a parsed-output summary extractor**

```python
def _summarize_response_payload(response_payload: dict) -> dict:
    parsed_output = response_payload.get("parsed_output") or {}
    if not isinstance(parsed_output, dict):
        return {
            "parsed_output_keys": [],
            "template_result_field_count": 0,
            "template_result_summary": {},
        }
```

- [ ] **Step 2: Extract scalar template fields without replacing raw parsed output**

```python
    parsed_output_keys = sorted(str(key) for key in parsed_output.keys())
    template_result_summary = {
        key: value
        for key, value in parsed_output.items()
        if key != "template_name" and isinstance(value, (str, int, float, bool))
    }
    return {
        "parsed_output_keys": parsed_output_keys,
        "template_result_field_count": len(template_result_summary),
        "template_result_summary": template_result_summary,
    }
```

- [ ] **Step 3: Merge the response summary into latest execution output**

```python
        **_summarize_request_payload(request_payload),
        **_summarize_response_payload(response_payload),
        **response_payload,
```

- [ ] **Step 4: Run focused tests to verify green**

Run the same focused command from Task 1.

Expected:

- template-backed latest execution now exposes parsed output summary fields
- existing `parsed_output` remains available unchanged

- [ ] **Step 5: Commit the summary implementation**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/sandbox/store.py backend/tests/test_sandbox_store.py backend/tests/test_project_status_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: summarize sandbox template result outputs"
```

### Task 3: Sync demo and delivery docs to the new result summary fields

**Files:**
- Modify: `backend/app/api/demo.py`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Extend demo wording**

```javascript
sandboxMetaEl.textContent = "DockerSandbox runtime summary, execution_mode, template_name, parsed_output_keys, and template_result_summary will appear here.";
```

- [ ] **Step 2: Add truthful delivery wording**

```markdown
- Latest persisted sandbox evidence now exposes `parsed_output_keys`, `template_result_field_count`, and `template_result_summary`, so template-backed runs can be inspected through normalized runtime evidence without hiding the original `parsed_output`.
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
- latest execution evidence stays truthful and easier to demo

- [ ] **Step 4: Commit doc alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/demo.py docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align sandbox template result summary evidence"
```
