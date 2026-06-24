# DockerSandbox Capability Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make DockerSandbox capability boundaries explicit and truthful by enforcing Python code length limits and surfacing supported templates plus runtime ceilings through status endpoints, demo output, and delivery docs.

**Architecture:** Keep DockerSandbox as a second-phase controlled execution path rather than part of the main DuckDB analysis chain. Add one new config boundary for inline Python length, expose runtime capability metadata from the sandbox runtime descriptor, validate requests at API/schema boundaries, and keep the same persisted latest-execution evidence path already used by `/api/sandbox/status` and `/api/project-status`.

**Tech Stack:** FastAPI, Pydantic, SQLite, existing Docker sandbox runtime/store, pytest

---

### Task 1: Freeze failing tests for sandbox capability boundary exposure

**Files:**
- Modify: `backend/tests/test_sandbox_api.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_demo_page.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add a failing sandbox status capability test**

```python
def test_sandbox_status_endpoint_reports_runtime_capability_boundaries(monkeypatch):
    monkeypatch.setattr(
        "app.api.sandbox.describe_sandbox_runtime",
        lambda: {
            "enabled": True,
            "docker_available": True,
            "image": "python:3.12-slim",
            "network_disabled": True,
            "timeout_seconds": 8,
            "max_timeout_seconds": 8,
            "max_code_chars": 4000,
            "supported_templates": ["region_sales_summary", "channel_sales_summary"],
        },
    )

    client = TestClient(app)
    response = client.get("/api/sandbox/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["max_timeout_seconds"] == 8
    assert payload["max_code_chars"] == 4000
    assert payload["supported_templates"] == ["region_sales_summary", "channel_sales_summary"]
```

- [ ] **Step 2: Add a failing sandbox API code-length validation test**

```python
def test_sandbox_execute_endpoint_rejects_excessive_python_code(monkeypatch):
    monkeypatch.setattr("app.api.sandbox.config.DOCKER_SANDBOX_MAX_CODE_CHARS", 12)

    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "python_code": "print('code too long')", "timeout_seconds": 8},
    )

    assert response.status_code == 422
```

- [ ] **Step 3: Add a failing project-status sandbox summary test**

```python
def test_get_project_status_surfaces_sandbox_capability_boundaries(monkeypatch):
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
            "latest_execution": None,
        },
    )

    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    sandbox = response.json()["summary"]["sandbox"]
    assert sandbox["max_timeout_seconds"] == 8
    assert sandbox["max_code_chars"] == 4000
    assert "region_sales_summary" in sandbox["supported_templates"]
```

- [ ] **Step 4: Add a failing demo/docs truthfulness check**

```python
def test_demo_page_mentions_sandbox_capability_boundaries():
    client = TestClient(app)
    response = client.get("/demo")
    content = response.text

    assert "supported_templates" in content
    assert "max_code_chars" in content
```

```python
assert "supported_templates" in project_status
assert "max_code_chars" in project_status
assert "supported_templates" in resume_description
assert "max_code_chars" in evidence_map
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

- sandbox status assertions fail because capability fields are not exposed yet, or
- code-length validation test fails because the request is still accepted, or
- docs/demo do not mention the new capability boundary fields

- [ ] **Step 6: Commit the red tests**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_sandbox_api.py backend/tests/test_project_status_api.py backend/tests/test_demo_page.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze sandbox capability boundary behavior"
```

### Task 2: Implement runtime boundary exposure and request validation

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/sandbox/templates.py`
- Modify: `backend/app/sandbox/runtime.py`
- Modify: `backend/app/api/sandbox.py`
- Modify: `backend/app/schemas/tool_schema.py`

- [ ] **Step 1: Add a dedicated code-length ceiling in config**

```python
DOCKER_SANDBOX_MAX_CODE_CHARS = int(get_env("DOCKER_SANDBOX_MAX_CODE_CHARS", "4000") or "4000")
```

- [ ] **Step 2: Add a reusable supported-template listing helper**

```python
SANDBOX_TEMPLATES = {
    "region_sales_summary": REGION_SALES_SUMMARY_TEMPLATE,
    "channel_sales_summary": CHANNEL_SALES_SUMMARY_TEMPLATE,
}


def list_sandbox_templates() -> list[str]:
    return list(SANDBOX_TEMPLATES.keys())
```

- [ ] **Step 3: Expose runtime boundaries from the sandbox runtime descriptor**

```python
    return {
        "enabled": config.DOCKER_SANDBOX_ENABLED,
        "docker_available": executor.docker_available(),
        "image": config.DOCKER_SANDBOX_IMAGE,
        "network_disabled": config.DOCKER_SANDBOX_NETWORK_DISABLED,
        "timeout_seconds": config.DOCKER_SANDBOX_TIMEOUT_SECONDS,
        "max_timeout_seconds": config.DOCKER_SANDBOX_TIMEOUT_SECONDS,
        "max_code_chars": config.DOCKER_SANDBOX_MAX_CODE_CHARS,
        "supported_templates": list_sandbox_templates(),
        "memory_limit_mb": config.DOCKER_SANDBOX_MEMORY_MB,
        "cpu_limit": config.DOCKER_SANDBOX_CPU_LIMIT,
    }
```

- [ ] **Step 4: Validate inline Python code length in the API request model**

```python
    @field_validator("python_code")
    @classmethod
    def validate_python_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) > config.DOCKER_SANDBOX_MAX_CODE_CHARS:
            raise ValueError("python_code exceeds the configured sandbox code limit.")
        return value
```

- [ ] **Step 5: Mirror the same boundary in the tool schema**

```python
    @field_validator("python_code")
    @classmethod
    def validate_python_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) > config.DOCKER_SANDBOX_MAX_CODE_CHARS:
            raise ValueError("python_code exceeds the configured sandbox code limit.")
        return value
```

- [ ] **Step 6: Run focused tests to verify green**

Run the same focused command from Task 1.

Expected:

- `/api/sandbox/status` exposes supported templates plus limits
- excessive inline Python is rejected with `422`
- `/api/project-status` carries the same sandbox capability boundary fields

- [ ] **Step 7: Commit runtime boundary support**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/core/config.py backend/app/sandbox/templates.py backend/app/sandbox/runtime.py backend/app/api/sandbox.py backend/app/schemas/tool_schema.py backend/tests/test_sandbox_api.py backend/tests/test_project_status_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: expose sandbox capability boundaries"
```

### Task 3: Reflect the new runtime evidence in demo and delivery docs

**Files:**
- Modify: `backend/app/api/demo.py`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `backend/tests/test_demo_page.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Adjust demo sandbox copy so capability boundaries are visible**

```javascript
sandboxMetaEl.textContent = "DockerSandbox runtime summary, supported_templates, max_timeout_seconds, and max_code_chars will appear here.";
```

- [ ] **Step 2: Keep sandbox status rendering naturally exposing the new fields**

```javascript
      sandboxStatusOutputEl.textContent = [
        `image: ${payload.image}`,
        `timeout_seconds: ${payload.timeout_seconds ?? "none"}`,
        `max_timeout_seconds: ${payload.max_timeout_seconds ?? "none"}`,
        `max_code_chars: ${payload.max_code_chars ?? "none"}`,
        `supported_templates: ${(payload.supported_templates || []).join(", ") || "none"}`,
      ].join("\n");
```

- [ ] **Step 3: Add truthful documentation wording**

```markdown
- `GET /api/sandbox/status` now exposes `supported_templates`, `max_timeout_seconds`, and `max_code_chars` so the sandbox boundary is explicit.
- Inline `python_code` requests are accepted only within the configured code-length ceiling; named templates remain the more controlled execution path.
```

- [ ] **Step 4: Re-run related tests and full backend verification**

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

- related sandbox/runtime/docs tests pass
- full backend suite stays green

- [ ] **Step 5: Commit demo/doc alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/demo.py docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md backend/tests/test_demo_page.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align sandbox capability boundary evidence"
```
