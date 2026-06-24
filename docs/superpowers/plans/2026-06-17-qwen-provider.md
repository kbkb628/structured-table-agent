# Qwen Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real Tongyi Qianwen LLM provider that can drive task goal/plan generation and LLM-based report layers through the existing `LLMClient` abstraction, while keeping explicit fallback behavior and truthful project boundaries.

**Architecture:** Introduce configuration-backed provider selection and a small factory that returns either `QwenClient` or `MockLLMClient`. Route task creation and report/evaluation stages through the configured provider without replacing deterministic pandas, DuckDB, chart, persistence, or rule-scoring logic.

**Tech Stack:** Python 3.12, FastAPI, pytest, stdlib `urllib`, existing Pydantic schemas and LangGraph orchestration

---

### Task 1: Freeze provider test coverage

**Files:**
- Create: `backend/tests/test_llm_provider_factory.py`
- Modify: `backend/tests/test_task_builder.py`
- Test: `backend/tests/test_llm_provider_factory.py`
- Test: `backend/tests/test_task_builder.py`

- [ ] **Step 1: Write the failing provider-factory tests**

```python
from pytest import raises

from app.llm.factory import LLMConfigurationError, get_llm_client
from app.llm.mock_client import MockLLMClient
from app.llm.qwen_client import QwenClient


def test_get_llm_client_returns_mock_when_provider_is_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    client = get_llm_client()

    assert isinstance(client, MockLLMClient)


def test_get_llm_client_returns_qwen_when_provider_is_qwen(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("QWEN_API_KEY", "test-key")

    client = get_llm_client()

    assert isinstance(client, QwenClient)


def test_get_llm_client_raises_when_qwen_key_is_missing(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    with raises(LLMConfigurationError):
        get_llm_client()


def test_get_llm_client_falls_back_to_mock_when_enabled(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("LLM_ALLOW_FALLBACK", "true")
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    client = get_llm_client()

    assert isinstance(client, MockLLMClient)
```

- [ ] **Step 2: Write the failing task-builder provider integration test**

```python
class StubLLMClient:
    def generate_analysis_goal(self, question, file_profile, business_context):
        return "qwen goal"

    def generate_analysis_plan(self, analysis_goal, file_profile, business_context):
        return ["qwen plan step"]

    def generate_report(self, intermediate_findings, chart_specs, business_context):
        return {}

    def judge_report(self, question, final_report, tool_results):
        return {}


def test_create_analysis_task_uses_configured_llm_client(...):
    ...
    monkeypatch.setattr("app.services.task_builder.get_llm_client", lambda: StubLLMClient())
    ...
    assert state["analysis_goal"] == "qwen goal"
    assert state["analysis_plan"] == ["qwen plan step"]
```

- [ ] **Step 3: Run the targeted tests to verify they fail**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_llm_provider_factory.py tests/test_task_builder.py -q
```

Expected:
- import failure for `app.llm.factory` or `app.llm.qwen_client`
- or failure because `task_builder` does not use `get_llm_client`

- [ ] **Step 4: Commit the red test state only if the repository policy requires it**

```bash
git status --short
```

Expected:
- only test files are modified or added

### Task 2: Implement configuration and provider factory

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/llm/factory.py`
- Modify: `backend/app/llm/__init__.py`
- Test: `backend/tests/test_llm_provider_factory.py`

- [ ] **Step 1: Add configuration helpers for provider selection**

```python
import os
from pathlib import Path


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


LLM_PROVIDER = (get_env("LLM_PROVIDER", "qwen") or "qwen").lower()
LLM_ALLOW_FALLBACK = (get_env("LLM_ALLOW_FALLBACK", "false") or "false").lower() == "true"
QWEN_API_KEY = get_env("QWEN_API_KEY") or get_env("DASHSCOPE_API_KEY")
QWEN_BASE_URL = get_env("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_MODEL = get_env("QWEN_MODEL", "qwen-plus")
QWEN_TIMEOUT_SECONDS = float(get_env("QWEN_TIMEOUT_SECONDS", "30") or "30")
```

- [ ] **Step 2: Implement provider factory with explicit configuration errors**

```python
from app.core import config
from app.llm.mock_client import MockLLMClient
from app.llm.qwen_client import QwenClient


class LLMConfigurationError(RuntimeError):
    pass


def get_llm_client():
    provider = config.LLM_PROVIDER
    if provider == "mock":
        return MockLLMClient()
    if provider != "qwen":
        raise LLMConfigurationError(f"Unsupported LLM provider: {provider}")
    if not config.QWEN_API_KEY:
        if config.LLM_ALLOW_FALLBACK:
            return MockLLMClient()
        raise LLMConfigurationError("QWEN_API_KEY or DASHSCOPE_API_KEY is required when LLM_PROVIDER=qwen.")
    return QwenClient(...)
```

- [ ] **Step 3: Export the factory symbols**

```python
from app.llm.base import LLMClient
from app.llm.factory import LLMConfigurationError, get_llm_client
from app.llm.mock_client import MockLLMClient
from app.llm.qwen_client import QwenClient

__all__ = ["LLMClient", "LLMConfigurationError", "MockLLMClient", "QwenClient", "get_llm_client"]
```

- [ ] **Step 4: Run the provider-factory tests and verify they pass**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_llm_provider_factory.py -q
```

Expected:
- all tests in `test_llm_provider_factory.py` pass

- [ ] **Step 5: Commit the factory milestone**

```bash
git add backend/app/core/config.py backend/app/llm/__init__.py backend/app/llm/factory.py backend/tests/test_llm_provider_factory.py
git commit -m "feat: add llm provider factory"
```

### Task 3: Implement Qwen client with structured parsing

**Files:**
- Create: `backend/app/llm/qwen_client.py`
- Modify: `backend/app/llm/prompt_templates.py`
- Create: `backend/tests/test_qwen_client.py`
- Test: `backend/tests/test_qwen_client.py`

- [ ] **Step 1: Write the failing Qwen client tests**

```python
from pytest import raises

from app.llm.qwen_client import QwenClient, QwenResponseError


def test_qwen_client_parses_goal_response():
    ...


def test_qwen_client_parses_plan_response():
    ...


def test_qwen_client_raises_on_invalid_json():
    with raises(QwenResponseError):
        ...
```

- [ ] **Step 2: Run the targeted Qwen client tests to verify failure**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_qwen_client.py -q
```

Expected:
- import or implementation failures

- [ ] **Step 3: Implement a minimal HTTP-backed Qwen client**

```python
class QwenClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: float = 30):
        ...

    def _chat_json(self, system_prompt: str, user_payload: dict) -> dict:
        ...

    def generate_analysis_goal(...):
        ...

    def generate_analysis_plan(...):
        ...

    def generate_report(...):
        ...

    def judge_report(...):
        ...
```

- [ ] **Step 4: Re-run the Qwen client tests and verify they pass**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_qwen_client.py -q
```

Expected:
- all tests in `test_qwen_client.py` pass

- [ ] **Step 5: Commit the Qwen client milestone**

```bash
git add backend/app/llm/qwen_client.py backend/app/llm/prompt_templates.py backend/tests/test_qwen_client.py
git commit -m "feat: add qwen llm client"
```

### Task 4: Route task creation through the provider factory

**Files:**
- Modify: `backend/app/services/task_builder.py`
- Modify: `backend/tests/test_task_builder.py`
- Test: `backend/tests/test_task_builder.py`

- [ ] **Step 1: Replace direct mock construction with factory resolution**

```python
from app.llm.factory import get_llm_client


def build_analysis_state(..., llm_client: LLMClient | None = None):
    client = llm_client or get_llm_client()
    ...
```

- [ ] **Step 2: Keep explicit dependency injection for tests and eval cases**

```python
def create_analysis_task(..., llm_client: LLMClient | None = None):
    ...
```

- [ ] **Step 3: Run targeted task-builder tests and verify they pass**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_task_builder.py -q
```

Expected:
- all task-builder tests pass

- [ ] **Step 4: Commit the task-builder integration milestone**

```bash
git add backend/app/services/task_builder.py backend/tests/test_task_builder.py
git commit -m "feat: use configured llm provider for task creation"
```

### Task 5: Add LLM-assisted report and judgement layers

**Files:**
- Modify: `backend/app/agent/nodes.py`
- Modify: `backend/app/agent/state.py`
- Create: `backend/tests/test_analysis_runner.py`
- Test: `backend/tests/test_analysis_runner.py`

- [ ] **Step 1: Write failing tests for LLM-assisted report persistence**

```python
def test_generate_report_node_uses_llm_summary_when_available(...):
    ...


def test_evaluate_report_node_records_llm_judgement(...):
    ...
```

- [ ] **Step 2: Run the targeted graph-node tests to verify failure**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_analysis_runner.py -q
```

Expected:
- failures because no LLM-assisted report or judgement layer exists

- [ ] **Step 3: Implement a minimal LLM-assisted report augmentation path**

```python
baseline_report = report_response.data or {}
llm_report = get_llm_client().generate_report(...)
state["final_report"] = llm_report or baseline_report
```

- [ ] **Step 4: Implement supplementary LLM judgement persistence**

```python
state["llm_judgement"] = get_llm_client().judge_report(
    state["question"],
    state["final_report"],
    state["tool_results"],
)
```

- [ ] **Step 5: Re-run the graph-node tests and verify they pass**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_analysis_runner.py -q
```

Expected:
- all targeted report/evaluation tests pass

- [ ] **Step 6: Commit the report-layer milestone**

```bash
git add backend/app/agent/nodes.py backend/app/agent/state.py backend/tests/test_analysis_runner.py
git commit -m "feat: add llm-assisted report layers"
```

### Task 6: Update docs and verify end-to-end behavior

**Files:**
- Modify: `backend/README.md`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/INTERVIEW_GUIDE.md`
- Test: full backend test suite

- [ ] **Step 1: Update the truth boundary in docs**

```text
- real Tongyi Qianwen provider integration completed
- configurable mock fallback remains available
- deterministic numeric computation remains tool-grounded
```

- [ ] **Step 2: Run the full backend suite**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest -q
```

Expected:
- zero failures

- [ ] **Step 3: Run one real-provider smoke verification if credentials are available**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
$env:LLM_PROVIDER='qwen'
.\.venv\Scripts\python.exe - <<'PY'
from app.llm.factory import get_llm_client
client = get_llm_client()
print(type(client).__name__)
PY
```

Expected:
- prints `QwenClient`

- [ ] **Step 4: Commit the final documentation and verification milestone**

```bash
git add backend/README.md docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/INTERVIEW_GUIDE.md
git commit -m "docs: update llm provider project boundary"
```
