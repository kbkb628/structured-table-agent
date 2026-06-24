# DockerSandbox Template Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade DockerSandbox from raw free-form code execution into a more controlled capability with reusable execution templates, tighter request limits, and clearer failure boundaries.

**Architecture:** Preserve the existing direct Python execution path, but add a small template layer that expands named analysis templates into controlled sandbox code. Add explicit input limits and additional failure classification in the executor/API boundary so demo and runtime evidence expose a more disciplined capability.

**Tech Stack:** FastAPI, Pydantic, SQLite, existing Docker sandbox executor, pytest

---

### Task 1: Freeze failing tests for sandbox templates and request hardening

**Files:**
- Create: `backend/tests/test_sandbox_templates.py`
- Modify: `backend/tests/test_sandbox_api.py`
- Modify: `backend/tests/test_demo_page.py`

- [ ] **Step 1: Add a failing template registry test**

```python
from app.sandbox.templates import build_sandbox_template_code


def test_build_region_sales_summary_template_returns_python_code():
    code = build_sandbox_template_code("region_sales_summary")

    assert "import csv" in code
    assert "json.dumps" in code
    assert "source.csv" in code
```

- [ ] **Step 2: Add a failing API template execution test**

```python
def test_sandbox_execute_endpoint_accepts_template_name(monkeypatch):
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
    monkeypatch.setattr(
        "app.api.sandbox.build_sandbox_template_code",
        lambda template_name: "print('templated')",
    )

    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "template_name": "region_sales_summary", "timeout_seconds": 8},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
```

- [ ] **Step 3: Add a failing API request-limit test**

```python
def test_sandbox_execute_endpoint_rejects_excessive_timeout():
    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "python_code": "print('ok')", "timeout_seconds": 999},
    )

    assert response.status_code == 422
```

- [ ] **Step 4: Add a failing demo-page template control test**

```python
def test_demo_page_mentions_sandbox_template_execution():
    client = TestClient(app)
    response = client.get("/demo")
    content = response.text

    assert "region_sales_summary" in content
    assert "sandbox-template-button" in content
```

- [ ] **Step 5: Run focused tests to verify red**

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
    "tests/test_sandbox_templates.py",
    "tests/test_sandbox_api.py",
    "tests/test_demo_page.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
```

Expected:

- missing `app.sandbox.templates` import error or
- missing request fields / demo controls cause test failures

- [ ] **Step 6: Commit the red tests**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_sandbox_templates.py backend/tests/test_sandbox_api.py backend/tests/test_demo_page.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze sandbox template hardening behavior"
```

### Task 2: Add sandbox templates and request validation

**Files:**
- Create: `backend/app/sandbox/templates.py`
- Modify: `backend/app/api/sandbox.py`
- Modify: `backend/app/schemas/tool_schema.py`

- [ ] **Step 1: Add a focused template builder module**

```python
def build_sandbox_template_code(template_name: str) -> str:
    templates = {
        "region_sales_summary": REGION_SALES_SUMMARY_TEMPLATE,
        "channel_sales_summary": CHANNEL_SALES_SUMMARY_TEMPLATE,
    }
    try:
        return templates[template_name]
    except KeyError as exc:
        raise ValueError(f"Unknown sandbox template: {template_name}") from exc
```

- [ ] **Step 2: Implement one truthful CSV analysis template**

```python
REGION_SALES_SUMMARY_TEMPLATE = """
import csv
import json
from collections import defaultdict

totals = defaultdict(float)
with open('/workspace/input/source.csv', 'r', encoding='utf-8-sig', newline='') as fp:
    reader = csv.DictReader(fp)
    for row in reader:
        totals[row['region']] += float(row['sales_amount'] or 0)

top_region = max(totals.items(), key=lambda item: item[1]) if totals else ('none', 0.0)
print(json.dumps({
    'template_name': 'region_sales_summary',
    'top_region': top_region[0],
    'top_sales_amount': round(top_region[1], 2),
    'region_count': len(totals),
}, ensure_ascii=False))
""".strip()
```

- [ ] **Step 3: Extend sandbox request schema to support template execution**

```python
class SandboxExecutionRequest(BaseModel):
    file_id: str
    python_code: str | None = None
    template_name: str | None = None
    timeout_seconds: int | None = None
```

- [ ] **Step 4: Add a request validator that requires exactly one execution mode**

```python
    @model_validator(mode="after")
    def validate_execution_mode(self):
        if bool(self.python_code) == bool(self.template_name):
            raise ValueError("Provide exactly one of python_code or template_name.")
        return self
```

- [ ] **Step 5: Cap timeout requests at the configured sandbox ceiling**

```python
    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout_seconds(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 1 or value > config.DOCKER_SANDBOX_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds exceeds the configured sandbox limit.")
        return value
```

- [ ] **Step 6: Route template execution through the same sandbox path**

```python
    python_code = request.python_code or build_sandbox_template_code(request.template_name or "")
    response = execute_in_docker_sandbox(
        file_id=request.file_id,
        python_code=python_code,
        timeout_seconds=request.timeout_seconds,
    )
```

- [ ] **Step 7: Run focused tests to verify green**

Run the same focused command from Task 1.

Expected:

- template builder tests pass
- API accepts `template_name`
- over-limit timeout is rejected

- [ ] **Step 8: Commit template and validation support**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/sandbox/templates.py backend/app/api/sandbox.py backend/app/schemas/tool_schema.py backend/tests/test_sandbox_templates.py backend/tests/test_sandbox_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: add controlled sandbox execution templates"
```

### Task 3: Expose template execution in demo and runtime wording

**Files:**
- Modify: `backend/app/api/demo.py`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/INTERVIEW_GUIDE.md`
- Modify: `backend/tests/test_delivery_docs.py`
- Modify: `backend/tests/test_demo_page.py`

- [ ] **Step 1: Add a dedicated sandbox template button in demo**

```html
<button id="sandbox-template-button" class="ghost" type="button">Run Sandbox Template</button>
```

- [ ] **Step 2: Change demo sandbox execution to use the named template**

```javascript
body: JSON.stringify({
  file_id: state.fileId,
  template_name: "region_sales_summary",
  timeout_seconds: 8,
}),
```

- [ ] **Step 3: Update sandbox meta text to mention template execution**

```javascript
sandboxMetaEl.textContent = "DockerSandbox runtime summary and latest template-backed execution will appear here.";
```

- [ ] **Step 4: Update delivery docs**

```markdown
- Sandbox demo execution now supports named templates such as `region_sales_summary` instead of only arbitrary inline Python.
- Sandbox timeout requests are capped by configured limits rather than accepted without boundary.
```

- [ ] **Step 5: Extend doc tests**

```python
assert "region_sales_summary" in content
assert "template-backed execution" in content or "sandbox execution templates" in content
```

- [ ] **Step 6: Run related tests and full backend verification**

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

- full backend suite passes
- demo and docs both mention controlled sandbox templates truthfully

- [ ] **Step 7: Commit demo/docs hardening**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/demo.py docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/INTERVIEW_GUIDE.md backend/tests/test_delivery_docs.py backend/tests/test_demo_page.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align sandbox template execution evidence"
```
