# DockerSandbox Failure Classification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten DockerSandbox runtime evidence by classifying blocked network behavior and resource-killed container exits into explicit failure codes instead of the generic `SANDBOX_EXECUTION_FAILED`.

**Architecture:** Keep DockerSandbox as a second-phase controlled execution module and leave its API shape unchanged. Extend only the executor-side stderr and exit-code classification rules, then sync the new runtime evidence wording into delivery docs and tests so status, demo, and interview materials stay truthful.

**Tech Stack:** FastAPI, existing Docker sandbox executor, SQLite-backed runtime evidence, pytest

---

### Task 1: Freeze failing tests for new sandbox failure classes

**Files:**
- Modify: `backend/tests/test_sandbox_executor.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add a failing network-blocked classification test**

```python
def test_docker_sandbox_executor_classifies_network_error(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: True)
    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda command, timeout_seconds: {
            "returncode": 1,
            "stdout": "",
            "stderr": "requests.exceptions.ConnectionError: [Errno -2] Name or service not known",
            "elapsed_ms": 18,
        },
    )

    result = executor.execute_python(code="import requests", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "failed"
    assert result["error"]["code"] == "SANDBOX_NETWORK_ERROR"
```

- [ ] **Step 2: Add a failing resource-killed classification test**

```python
def test_docker_sandbox_executor_classifies_resource_killed_container(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: True)
    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda command, timeout_seconds: {
            "returncode": 137,
            "stdout": "",
            "stderr": "Killed",
            "elapsed_ms": 25,
        },
    )

    result = executor.execute_python(code="x = '1' * 10_000_000", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "failed"
    assert result["error"]["code"] == "SANDBOX_RESOURCE_KILLED"
```

- [ ] **Step 3: Add failing doc assertions for the new evidence codes**

```python
assert "SANDBOX_NETWORK_ERROR" in resume_description
assert "SANDBOX_RESOURCE_KILLED" in resume_description
assert "SANDBOX_NETWORK_ERROR" in interview_guide
assert "SANDBOX_RESOURCE_KILLED" in evidence_map
assert "SANDBOX_NETWORK_ERROR" in project_status
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
    "tests/test_sandbox_executor.py",
    "tests/test_delivery_docs.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- executor tests fail with `SANDBOX_EXECUTION_FAILED` instead of the new specific codes, or
- doc tests fail because the new evidence codes are not documented yet

- [ ] **Step 5: Commit the red tests**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_sandbox_executor.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze sandbox failure classification behavior"
```

### Task 2: Implement executor classification for network and resource-killed failures

**Files:**
- Modify: `backend/app/sandbox/executor.py`

- [ ] **Step 1: Extend classifier to detect blocked network behavior**

```python
    if (
        "connectionerror" in lowered
        or "name or service not known" in lowered
        or "temporary failure in name resolution" in lowered
        or "failed to establish a new connection" in lowered
    ):
        return "SANDBOX_NETWORK_ERROR", stderr.strip() or "Sandbox code attempted a blocked network operation."
```

- [ ] **Step 2: Extend classifier to detect resource-killed container exits**

```python
def _classify_execution_failure(stderr: str, returncode: int | None = None) -> tuple[str, str]:
    lowered = (stderr or "").lower()
    if returncode in {137, 143} or "killed" in lowered or "oomkilled" in lowered:
        return "SANDBOX_RESOURCE_KILLED", stderr.strip() or "Sandbox execution was killed by runtime resource limits."
```

- [ ] **Step 3: Pass the return code into the classifier**

```python
            else {
                "code": _classify_execution_failure(stderr, returncode)[0],
                "message": _classify_execution_failure(stderr, returncode)[1],
                "suggested_fields": [],
            },
```

- [ ] **Step 4: Run focused tests to verify green**

Run the same focused command from Task 1.

Expected:

- executor tests classify blocked network and resource-killed exits explicitly
- no doc assertions fail after runtime wording is updated in Task 3

- [ ] **Step 5: Commit the executor implementation**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/sandbox/executor.py backend/tests/test_sandbox_executor.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: classify sandbox network and resource failures"
```

### Task 3: Sync truthful runtime wording into delivery docs

**Files:**
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `docs/INTERVIEW_GUIDE.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add the new failure codes to DockerSandbox evidence sections**

```markdown
- Latest persisted sandbox evidence now also includes `SANDBOX_NETWORK_ERROR` for blocked outbound calls and `SANDBOX_RESOURCE_KILLED` for runtime-enforced container termination.
```

- [ ] **Step 2: Keep the interview boundary truthful**

```markdown
- These new failure classes improve runtime observability but do not change the product boundary: DockerSandbox is still a controlled second-phase execution path, not the default analysis engine.
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
- delivery docs and interview materials now mention the new runtime evidence codes truthfully

- [ ] **Step 4: Commit doc alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md docs/INTERVIEW_GUIDE.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align sandbox failure classification evidence"
```
