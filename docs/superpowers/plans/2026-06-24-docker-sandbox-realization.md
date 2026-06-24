# DockerSandbox Realization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a truthful Docker-based controlled code execution capability that can be named directly in the resume without replacing the existing deterministic structured-table analysis chain.

**Architecture:** Introduce a dedicated Docker sandbox execution module plus a controlled `advanced_code_execution` tool and a narrow sandbox API. The existing DuckDB and tool-driven analysis loop remains the default numeric truth path; DockerSandbox is exposed as a second-phase advanced capability with explicit status, timeout, resource limits, observability, and degradation reporting.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, existing tool registry, SQLite tool logs and events, Docker CLI on Windows, existing `/api/project-status` and `/demo`

---

### Task 1: Freeze sandbox execution contract tests

**Files:**
- Create: `backend/tests/test_sandbox_executor.py`
- Create: `backend/tests/test_sandbox_tool.py`
- Create: `backend/tests/test_sandbox_api.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_demo_page.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add a red executor test for success, timeout, and unavailable Docker**

```python
from app.sandbox.executor import DockerSandboxExecutor


def test_docker_sandbox_executor_reports_success(monkeypatch, tmp_path):
    executor = DockerSandboxExecutor()

    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda command, timeout_seconds: {
            "returncode": 0,
            "stdout": '{"result": {"top_region": "East"}}',
            "stderr": "",
            "elapsed_ms": 41,
        },
    )

    result = executor.execute_python(
        code="print('ignored')",
        mounted_files=[{"host_path": str(tmp_path / "sales.csv"), "container_path": "/workspace/input/sales.csv", "read_only": True}],
        timeout_seconds=8,
    )

    assert result["status"] == "completed"
    assert result["exit_code"] == 0
    assert result["parsed_output"]["result"]["top_region"] == "East"


def test_docker_sandbox_executor_reports_timeout(monkeypatch):
    executor = DockerSandboxExecutor()

    def raise_timeout(command, timeout_seconds):
        raise TimeoutError(f"timed out after {timeout_seconds}s")

    monkeypatch.setattr(executor, "_run_process", raise_timeout)

    result = executor.execute_python(code="while True: pass", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "timeout"
    assert result["degraded"] is True
    assert result["error"]["code"] == "SANDBOX_TIMEOUT"


def test_docker_sandbox_executor_reports_docker_unavailable(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: False)

    result = executor.execute_python(code="print(1)", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "degraded"
    assert result["error"]["code"] == "DOCKER_UNAVAILABLE"
```

- [ ] **Step 2: Add a red tool test for `advanced_code_execution` validation and response shape**

```python
from app.tools.registry import invoke_tool


def test_advanced_code_execution_tool_returns_structured_tool_response(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.tools.sandbox_tool.execute_in_docker_sandbox",
        lambda file_id, python_code, timeout_seconds=None: {
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"rows": [{"region": "East", "sales_amount": 1200}]}',
            "stderr": "",
            "elapsed_ms": 55,
            "parsed_output": {"rows": [{"region": "East", "sales_amount": 1200}]},
            "degraded": False,
        },
    )

    result = invoke_tool(
        "advanced_code_execution",
        file_id="file_sandbox",
        python_code="print('hello')",
        timeout_seconds=8,
    )

    assert result.success is True
    assert result.tool_name == "advanced_code_execution"
    assert result.data["status"] == "completed"
    assert result.data["parsed_output"]["rows"][0]["region"] == "East"
```

- [ ] **Step 3: Add a red API test for sandbox status and execution**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_sandbox_status_endpoint_reports_runtime_capabilities(monkeypatch):
    monkeypatch.setattr(
        "app.api.sandbox.describe_sandbox_runtime",
        lambda: {
            "enabled": True,
            "docker_available": True,
            "image": "python:3.12-slim",
            "network_disabled": True,
            "timeout_seconds": 8,
        },
    )

    client = TestClient(app)
    response = client.get("/api/sandbox/status")

    assert response.status_code == 200
    assert response.json()["enabled"] is True
    assert response.json()["docker_available"] is True


def test_sandbox_execute_endpoint_returns_execution_result(monkeypatch):
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
        },
    )

    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "python_code": "print('ok')", "timeout_seconds": 8},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["parsed_output"]["summary"] == "ok"
```

- [ ] **Step 4: Add a red project-status and demo test for sandbox runtime evidence**

```python
def test_get_project_status_surfaces_sandbox_runtime_summary(monkeypatch):
    monkeypatch.setattr(
        "app.api.project_status._sandbox_info",
        lambda: {
            "enabled": True,
            "docker_available": True,
            "image": "python:3.12-slim",
            "network_disabled": True,
            "timeout_seconds": 8,
            "memory_limit_mb": 256,
            "latest_execution": {
                "tool_name": "advanced_code_execution",
                "status": "completed",
                "elapsed_ms": 55,
            },
        },
    )

    client = TestClient(app)
    response = client.get("/api/project-status")

    sandbox = response.json()["summary"]["sandbox"]
    assert sandbox["enabled"] is True
    assert sandbox["docker_available"] is True
    assert sandbox["latest_execution"]["tool_name"] == "advanced_code_execution"
```

```python
def test_demo_page_mentions_sandbox_runtime_blocks():
    client = TestClient(app)
    response = client.get("/demo")
    content = response.text

    assert 'id="sandbox-status-button"' in content
    assert 'id="sandbox-execute-button"' in content
    assert "Sandbox Runtime" in content
    assert "advanced_code_execution" in content
```

- [ ] **Step 5: Run focused tests to verify the contract fails before implementation**

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
    "tests/test_sandbox_executor.py",
    "tests/test_sandbox_tool.py",
    "tests/test_sandbox_api.py",
    "tests/test_project_status_api.py",
    "tests/test_demo_page.py",
    "-q",
]))
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- sandbox executor module does not exist yet
- tool registry does not expose `advanced_code_execution`
- sandbox API router does not exist yet
- `project-status` and `/demo` do not yet surface sandbox evidence

- [ ] **Step 6: Commit the red acceptance state**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_sandbox_executor.py backend/tests/test_sandbox_tool.py backend/tests/test_sandbox_api.py backend/tests/test_project_status_api.py backend/tests/test_demo_page.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze docker sandbox execution behavior"
```

### Task 2: Add sandbox config and Docker CLI executor

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/sandbox/__init__.py`
- Create: `backend/app/sandbox/executor.py`
- Create: `backend/app/sandbox/runtime.py`
- Create: `backend/tests/test_sandbox_executor.py`

- [ ] **Step 1: Add explicit DockerSandbox environment settings**

```python
DOCKER_SANDBOX_ENABLED = get_bool_env("DOCKER_SANDBOX_ENABLED", True)
DOCKER_SANDBOX_IMAGE = get_env("DOCKER_SANDBOX_IMAGE", "python:3.12-slim") or "python:3.12-slim"
DOCKER_SANDBOX_TIMEOUT_SECONDS = int(get_env("DOCKER_SANDBOX_TIMEOUT_SECONDS", "8") or "8")
DOCKER_SANDBOX_MEMORY_MB = int(get_env("DOCKER_SANDBOX_MEMORY_MB", "256") or "256")
DOCKER_SANDBOX_CPU_LIMIT = get_env("DOCKER_SANDBOX_CPU_LIMIT", "1.0") or "1.0"
DOCKER_SANDBOX_NETWORK_DISABLED = get_bool_env("DOCKER_SANDBOX_NETWORK_DISABLED", True)
DOCKER_SANDBOX_TMP_ROOT = DATA_DIR / "sandbox_runs"
```

- [ ] **Step 2: Create the Docker executor with explicit resource limits and degradation paths**

```python
class DockerSandboxExecutor:
    def docker_available(self) -> bool:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and bool(result.stdout.strip())

    def execute_python(self, code: str, mounted_files: list[dict], timeout_seconds: int) -> dict:
        if not config.DOCKER_SANDBOX_ENABLED:
            return _degraded_result("SANDBOX_DISABLED", "DockerSandbox is disabled by configuration.")
        if not self.docker_available():
            return _degraded_result("DOCKER_UNAVAILABLE", "Docker CLI is unavailable.")
        ...
```

- [ ] **Step 3: Build the container command as a read-only, network-disabled sandbox**

```python
command = [
    "docker", "run", "--rm",
    "--network", "none",
    "--memory", f"{config.DOCKER_SANDBOX_MEMORY_MB}m",
    "--cpus", str(config.DOCKER_SANDBOX_CPU_LIMIT),
    "--read-only",
    "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
    "-v", f"{job_dir.as_posix()}:/workspace/job",
    "-v", f"{input_file_path.as_posix()}:/workspace/input/source.csv:ro",
    "-w", "/workspace/job",
    config.DOCKER_SANDBOX_IMAGE,
    "python",
    "runner.py",
]
```

- [ ] **Step 4: Parse stdout as structured JSON and normalize error cases**

```python
try:
    parsed_output = json.loads(stdout) if stdout.strip() else {}
except json.JSONDecodeError:
    parsed_output = {"raw_stdout": stdout}

return {
    "status": "completed" if returncode == 0 else "failed",
    "exit_code": returncode,
    "stdout": stdout,
    "stderr": stderr,
    "elapsed_ms": elapsed_ms,
    "parsed_output": parsed_output,
    "degraded": returncode != 0,
    "error": None if returncode == 0 else {
        "code": "SANDBOX_EXECUTION_FAILED",
        "message": stderr.strip() or "Sandbox execution failed.",
    },
}
```

- [ ] **Step 5: Add runtime capability helpers for status endpoints**

```python
def describe_sandbox_runtime() -> dict:
    executor = DockerSandboxExecutor()
    return {
        "enabled": config.DOCKER_SANDBOX_ENABLED,
        "docker_available": executor.docker_available(),
        "image": config.DOCKER_SANDBOX_IMAGE,
        "network_disabled": config.DOCKER_SANDBOX_NETWORK_DISABLED,
        "timeout_seconds": config.DOCKER_SANDBOX_TIMEOUT_SECONDS,
        "memory_limit_mb": config.DOCKER_SANDBOX_MEMORY_MB,
        "cpu_limit": config.DOCKER_SANDBOX_CPU_LIMIT,
    }
```

- [ ] **Step 6: Run executor-focused tests**

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
    "tests/test_sandbox_executor.py",
    "-q",
]))
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- executor tests pass
- unavailable Docker and timeout cases degrade explicitly instead of crashing

- [ ] **Step 7: Commit the executor milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/core/config.py backend/app/sandbox/__init__.py backend/app/sandbox/executor.py backend/app/sandbox/runtime.py backend/tests/test_sandbox_executor.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: add docker sandbox executor"
```

### Task 3: Add the controlled sandbox tool and dedicated API

**Files:**
- Modify: `backend/app/schemas/tool_schema.py`
- Modify: `backend/app/tools/registry.py`
- Create: `backend/app/tools/sandbox_tool.py`
- Create: `backend/app/api/sandbox.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_sandbox_tool.py`
- Modify: `backend/tests/test_sandbox_api.py`

- [ ] **Step 1: Add tool schemas for `advanced_code_execution`**

```python
class AdvancedCodeExecutionArgs(ToolSchemaModel):
    file_id: str
    python_code: str
    timeout_seconds: int | None = None


class AdvancedCodeExecutionOutput(BaseModel):
    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    elapsed_ms: int
    parsed_output: dict[str, Any]
    degraded: bool = False
```

```python
TOOL_DATA_SCHEMAS = {
    ...
    "advanced_code_execution": AdvancedCodeExecutionOutput,
}
```

- [ ] **Step 2: Wrap the executor behind a normal tool boundary**

```python
from app.storage.file_store import get_file_record
from app.sandbox.executor import DockerSandboxExecutor
from app.schemas.tool_schema import ToolError
from app.schemas.tool_schema import ToolResponse


def advanced_code_execution(file_id: str, python_code: str, timeout_seconds: int | None = None) -> ToolResponse:
    record = get_file_record(file_id)
    if record is None:
        return ToolResponse(
            success=False,
            tool_name="advanced_code_execution",
            data=None,
            summary="sandbox execution failed",
            error=ToolError(code="FILE_NOT_FOUND", message=f"Unknown file_id: {file_id}", suggested_fields=[]),
            metadata={},
        )
    result = DockerSandboxExecutor().execute_python_against_file(
        file_path=record.stored_path,
        code=python_code,
        timeout_seconds=timeout_seconds,
    )
    return ToolResponse(
        success=result["status"] == "completed",
        tool_name="advanced_code_execution",
        data=result,
        summary="sandbox execution completed" if result["status"] == "completed" else "sandbox execution degraded",
        error=result.get("error"),
        metadata={"elapsed_ms": result["elapsed_ms"], "sandbox_status": result["status"]},
    )
```

- [ ] **Step 3: Register the tool without changing the existing LangGraph default planner**

```python
TOOL_ARG_SCHEMAS = {
    ...
    "advanced_code_execution": AdvancedCodeExecutionArgs,
}


def get_tool_registry() -> dict[str, ToolCallable]:
    return {
        ...
        "advanced_code_execution": advanced_code_execution,
    }
```

- [ ] **Step 4: Add a narrow sandbox API for direct execution and runtime status**

```python
@router.get("/api/sandbox/status")
def get_sandbox_status() -> dict:
    return describe_sandbox_runtime()


@router.post("/api/sandbox/execute")
def run_sandbox_execution(request: SandboxExecutionRequest) -> dict:
    response = advanced_code_execution(
        file_id=request.file_id,
        python_code=request.python_code,
        timeout_seconds=request.timeout_seconds,
    )
    return response.model_dump()
```

- [ ] **Step 5: Include the router in the FastAPI app**

```python
from app.api.sandbox import router as sandbox_router

...
app.include_router(sandbox_router)
```

- [ ] **Step 6: Run tool and API tests**

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
    "tests/test_sandbox_tool.py",
    "tests/test_sandbox_api.py",
    "-q",
]))
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- tool registry accepts `advanced_code_execution`
- API returns structured success and degradation payloads
- no existing analysis endpoint behavior regresses

- [ ] **Step 7: Commit the tool and API milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/schemas/tool_schema.py backend/app/tools/registry.py backend/app/tools/sandbox_tool.py backend/app/api/sandbox.py backend/app/main.py backend/tests/test_sandbox_tool.py backend/tests/test_sandbox_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: expose controlled docker sandbox execution"
```

### Task 4: Surface sandbox runtime evidence through project-status and demo

**Files:**
- Modify: `backend/app/api/project_status.py`
- Modify: `backend/app/api/demo.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_demo_page.py`

- [ ] **Step 1: Add sandbox summary to `GET /api/project-status`**

```python
def _sandbox_info() -> dict:
    runtime = describe_sandbox_runtime()
    latest_execution = _latest_tool_execution("advanced_code_execution")
    return {
        **runtime,
        "latest_execution": latest_execution,
    }


@router.get("/api/project-status")
def get_project_status() -> dict:
    ...
    return {
        "summary": {
            ...
            "sandbox": _sandbox_info(),
        }
    }
```

- [ ] **Step 2: Read latest sandbox tool log as runtime evidence instead of inventing status**

```python
def _latest_tool_execution(tool_name: str) -> dict | None:
    ...
    return {
        "tool_name": tool_name,
        "status": response_payload.get("data", {}).get("status"),
        "elapsed_ms": int(row[6] or 0),
        "success": bool(row[5]),
        "created_at": row[7],
    }
```

- [ ] **Step 3: Add demo controls and output blocks for sandbox status and execution**

```html
<button id="sandbox-status-button" class="ghost" type="button">Sandbox Status</button>
<button id="sandbox-execute-button" class="ghost" type="button">Run Sandbox</button>
```

```javascript
async function loadSandboxStatus() {
  const payload = await apiFetch("/api/sandbox/status");
  sandboxStatusOutputEl.textContent = [
    `enabled: ${payload.enabled}`,
    `docker_available: ${payload.docker_available}`,
    `image: ${payload.image}`,
    `timeout_seconds: ${payload.timeout_seconds}`,
  ].join("\n");
}
```

- [ ] **Step 4: Keep sandbox demo explicit and separate from normal analysis buttons**

```javascript
async function runSandboxExecution() {
  if (!state.fileId) {
    throw new Error("Upload or load a file before sandbox execution.");
  }
  const payload = await apiFetch("/api/sandbox/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_id: state.fileId,
      python_code: "import pandas as pd\\ndf = pd.read_csv('/workspace/input/source.csv')\\nprint(df.head(3).to_json(orient=\\'records\\'))",
      timeout_seconds: 8,
    }),
  });
  sandboxResultOutputEl.textContent = stringify(payload);
}
```

- [ ] **Step 5: Run runtime evidence tests**

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
    "tests/test_project_status_api.py",
    "tests/test_demo_page.py",
    "-q",
]))
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- `project-status` exposes truthful sandbox capability and latest execution summary
- `/demo` exposes sandbox status and execution blocks without replacing analysis flow

- [ ] **Step 6: Commit the runtime evidence milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/project_status.py backend/app/api/demo.py backend/tests/test_project_status_api.py backend/tests/test_demo_page.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: surface docker sandbox runtime evidence"
```

### Task 5: Align docs, boundaries, and full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `docs/INTERVIEW_GUIDE.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Upgrade delivery wording from "not implemented" to truthful implemented boundary**

```markdown
- DockerSandbox is now implemented as a controlled second-phase execution capability.
- It is exposed through `advanced_code_execution`, `POST /api/sandbox/execute`, `GET /api/sandbox/status`, `/demo`, and `GET /api/project-status`.
- It does not replace deterministic DuckDB and tool-based numeric analysis in the main report chain.
```

- [ ] **Step 2: Extend doc tests to require DockerSandbox runtime evidence wording**

```python
def test_delivery_docs_mention_docker_sandbox_runtime_evidence():
    content = (Path(__file__).resolve().parents[2] / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(
        encoding="utf-8"
    )

    assert "DockerSandbox" in content
    assert "advanced_code_execution" in content
    assert "/api/sandbox/execute" in content
    assert "/api/sandbox/status" in content
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
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- full suite passes
- no resume or runtime document still claims DockerSandbox is missing
- main analysis loop tests still pass unchanged

- [ ] **Step 4: Commit the documentation alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add README.md docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md docs/INTERVIEW_GUIDE.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align docker sandbox evidence with resume wording"
```
