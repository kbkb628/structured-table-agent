# Sandbox Runtime Evidence Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a stable outward-facing sandbox runtime evidence field set across `demo_mvp.ps1`, `demo_mvp_contract.json`, tests, and delivery docs so demo outputs stay truthful and reviewable.

**Architecture:** Keep the existing sandbox runtime source of truth in `GET /api/project-status` and `GET /api/sandbox/status`, then project a narrow stable subset into the demo script JSON contract. Use tests to freeze the exact script field names and doc coverage, then make the smallest script and documentation changes needed to align with already implemented backend evidence.

**Tech Stack:** PowerShell, JSON contract file, FastAPI delivery docs, pytest

---

### Task 1: Freeze the new demo-script sandbox evidence contract with failing tests

**Files:**
- Modify: `backend/tests/test_demo_script_consistency.py`
- Modify: `backend/tests/test_delivery_docs.py`
- Test: `scripts/demo_mvp.ps1`
- Test: `scripts/demo_mvp_contract.json`

- [ ] **Step 1: Add failing assertions for sandbox fields in the demo script**

```python
def test_demo_script_mentions_project_status_summary_output():
    script = _read_demo_script()

    assert "project_status_sandbox_enabled" in script
    assert "project_status_sandbox_docker_available" in script
    assert "project_status_sandbox_supported_templates" in script
    assert "project_status_sandbox_max_timeout_seconds" in script
    assert "project_status_sandbox_max_code_chars" in script
    assert "project_status_sandbox_latest_execution_mode" in script
    assert "project_status_sandbox_latest_template_name" in script
    assert "project_status_sandbox_latest_python_code_char_count" in script
    assert "project_status_sandbox_latest_parsed_output_keys" in script
    assert "project_status_sandbox_latest_template_result_field_count" in script
    assert "project_status_sandbox_latest_error_code" in script
```

- [ ] **Step 2: Add failing assertions for the contract file**

```python
def test_demo_script_contract_matches_pscustomobject_output_shape():
    contract = _load_demo_contract()
    object_fields = _extract_pscustomobject_fields(_read_demo_script())

    assert "project_status_sandbox_enabled" in object_fields[1]
    assert "project_status_sandbox_latest_execution_mode" in object_fields[1]
    assert "project_status_sandbox_latest_template_name" in object_fields[1]
    assert "project_status_sandbox_latest_python_code_char_count" in object_fields[1]
    assert "project_status_sandbox_latest_parsed_output_keys" in object_fields[1]
    assert "project_status_sandbox_latest_template_result_field_count" in object_fields[1]
    assert "project_status_sandbox_latest_error_code" in object_fields[1]

    assert "project_status_sandbox_enabled" in contract["documented_summary_fields"]
    assert "project_status_sandbox_latest_execution_mode" in contract["documented_summary_fields"]
    assert "project_status_sandbox_latest_template_name" in contract["documented_summary_fields"]
    assert "project_status_sandbox_latest_python_code_char_count" in contract["documented_summary_fields"]
```

- [ ] **Step 3: Add failing delivery-doc coverage assertions**

```python
def test_delivery_docs_mention_docker_sandbox_runtime_evidence():
    repo_root = Path(__file__).resolve().parents[2]
    resume_description = (repo_root / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(encoding="utf-8")
    interview_guide = (repo_root / "docs" / "INTERVIEW_GUIDE.md").read_text(encoding="utf-8")
    evidence_map = (repo_root / "docs" / "RESUME_EVIDENCE_MAP.md").read_text(encoding="utf-8")
    project_status = (repo_root / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")

    assert "project_status_sandbox_enabled" in project_status
    assert "project_status_sandbox_latest_execution_mode" in project_status
    assert "project_status_sandbox_latest_template_name" in resume_description
    assert "project_status_sandbox_latest_python_code_char_count" in evidence_map
    assert "project_status_sandbox_latest_parsed_output_keys" in interview_guide
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
    "tests/test_demo_script_consistency.py",
    "tests/test_delivery_docs.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- `test_demo_script_mentions_project_status_summary_output` fails because script does not yet export sandbox fields
- `test_demo_script_contract_matches_pscustomobject_output_shape` fails because contract does not yet freeze them
- at least one delivery-doc assertion fails because docs do not yet mention the demo script field names

- [ ] **Step 5: Commit the red tests**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_demo_script_consistency.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze sandbox runtime evidence script fields"
```

### Task 2: Export stable sandbox runtime evidence fields from the demo script and contract

**Files:**
- Modify: `scripts/demo_mvp.ps1`
- Modify: `scripts/demo_mvp_contract.json`

- [ ] **Step 1: Add sandbox summary field extraction to the demo script**

```powershell
project_status_sandbox_enabled = $projectStatusAfterRuns.summary.sandbox.enabled
project_status_sandbox_docker_available = $projectStatusAfterRuns.summary.sandbox.docker_available
project_status_sandbox_supported_templates = $projectStatusAfterRuns.summary.sandbox.supported_templates
project_status_sandbox_max_timeout_seconds = $projectStatusAfterRuns.summary.sandbox.max_timeout_seconds
project_status_sandbox_max_code_chars = $projectStatusAfterRuns.summary.sandbox.max_code_chars
project_status_sandbox_latest_execution_mode = $projectStatusAfterRuns.summary.sandbox.latest_execution.execution_mode
project_status_sandbox_latest_template_name = $projectStatusAfterRuns.summary.sandbox.latest_execution.template_name
project_status_sandbox_latest_python_code_char_count = $projectStatusAfterRuns.summary.sandbox.latest_execution.python_code_char_count
project_status_sandbox_latest_parsed_output_keys = $projectStatusAfterRuns.summary.sandbox.latest_execution.parsed_output_keys
project_status_sandbox_latest_template_result_field_count = $projectStatusAfterRuns.summary.sandbox.latest_execution.template_result_field_count
project_status_sandbox_latest_error_code = $projectStatusAfterRuns.summary.sandbox.latest_execution.error.code
```

- [ ] **Step 2: Freeze the same field names in the JSON contract**

```json
"project_status_sandbox_enabled",
"project_status_sandbox_docker_available",
"project_status_sandbox_supported_templates",
"project_status_sandbox_max_timeout_seconds",
"project_status_sandbox_max_code_chars",
"project_status_sandbox_latest_execution_mode",
"project_status_sandbox_latest_template_name",
"project_status_sandbox_latest_python_code_char_count",
"project_status_sandbox_latest_parsed_output_keys",
"project_status_sandbox_latest_template_result_field_count",
"project_status_sandbox_latest_error_code"
```

- [ ] **Step 3: Run focused tests to verify green**

Run the same focused command from Task 1.

Expected:

- demo script tests pass with the frozen sandbox output field list
- contract consistency tests pass
- doc tests may still fail until documentation is updated in Task 3

- [ ] **Step 4: Commit the script and contract alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add scripts/demo_mvp.ps1 scripts/demo_mvp_contract.json backend/tests/test_demo_script_consistency.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: export sandbox runtime evidence in demo script"
```

### Task 3: Align delivery docs with the stable script field set

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/API_REFERENCE.md`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/INTERVIEW_GUIDE.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add truthful script-output wording to the docs**

```markdown
The demo script now exports stable sandbox runtime evidence fields including
`project_status_sandbox_enabled`,
`project_status_sandbox_supported_templates`,
`project_status_sandbox_max_timeout_seconds`,
`project_status_sandbox_max_code_chars`,
`project_status_sandbox_latest_execution_mode`,
`project_status_sandbox_latest_template_name`,
`project_status_sandbox_latest_python_code_char_count`,
`project_status_sandbox_latest_parsed_output_keys`,
`project_status_sandbox_latest_template_result_field_count`, and
`project_status_sandbox_latest_error_code`.
```

- [ ] **Step 2: Keep wording inside the real capability boundary**

```markdown
These fields summarize existing sandbox runtime evidence already surfaced by
`GET /api/project-status` and `GET /api/sandbox/status`; they do not imply the
sandbox replaces the default LangGraph + tool-chain execution path.
```

- [ ] **Step 3: Re-run focused tests**

Run the same focused command from Task 1.

Expected:

- `tests/test_demo_script_consistency.py` passes
- `tests/test_delivery_docs.py` passes

- [ ] **Step 4: Run full backend verification**

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
- no existing delivery-doc assertions regress

- [ ] **Step 5: Commit the documentation alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add README.md backend/README.md docs/API_REFERENCE.md docs/PROJECT_STATUS.md docs/INTERVIEW_GUIDE.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align sandbox runtime evidence script outputs"
```
