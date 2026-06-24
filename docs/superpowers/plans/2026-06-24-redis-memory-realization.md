# Redis Memory Realization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the current Redis-first session storage into a truthful multi-turn analysis memory subsystem that stores turn history, maintains a sliding window plus summary memory, and feeds that memory back into analysis goal and plan generation for later tasks on the same file.

**Architecture:** Keep the current `POST /api/analysis/start` -> `task_builder` -> `SessionStore` startup path unchanged at the API level, but add a file-scoped memory layer beside the existing task-scoped snapshot keys. Persist recent turn memories and a compressed summary in Redis, mirror them into SQLite-backed task state for inspection, inject them into `generate_analysis_goal()` and `generate_analysis_plan()`, and surface runtime evidence through `GET /api/project-status` and `/demo`.

**Tech Stack:** Python 3.12, FastAPI, Redis-first session store with SQLite fallback, pytest, existing `QwenClient` / `MockLLMClient`, existing `/api/project-status` and `/demo`

---

### Task 1: Freeze memory acceptance tests before implementation

**Files:**
- Modify: `backend/tests/test_session_store.py`
- Modify: `backend/tests/test_task_builder.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_mock_llm.py`
- Modify: `backend/tests/test_qwen_client.py`

- [ ] **Step 1: Add red tests for file-scoped turn memory persistence and compaction**

```python
def test_session_store_persists_file_memory_and_sliding_window(monkeypatch):
    fake_client = FakeRedisClient()
    monkeypatch.setattr(SessionStore, "_connect", lambda self: fake_client)
    store = SessionStore()

    for index in range(1, 5):
        store.append_turn_memory(
            file_id="file_memory_case",
            task_id=f"task_memory_{index}",
            question=f"analyse question {index}",
            analysis_goal=f"goal {index}",
            analysis_plan=[f"plan {index}"],
            final_report={"title": f"Report {index}"},
            max_recent_turns=2,
        )

    memory = store.load_file_memory("file_memory_case")

    assert memory["scope"]["file_id"] == "file_memory_case"
    assert memory["stats"]["recent_turn_count"] == 2
    assert [turn["task_id"] for turn in memory["recent_turns"]] == ["task_memory_3", "task_memory_4"]
    assert memory["summary_memory"]["turn_count"] == 2
    assert "question 1" in memory["summary_memory"]["summary_text"]
```

- [ ] **Step 2: Add a red test for `task_builder` reading historical memory into state and LLM calls**

```python
def test_create_analysis_task_injects_file_memory_into_goal_and_plan(tmp_path, monkeypatch):
    class MemoryAwareStubLLMClient:
        def __init__(self):
            self.goal_memory = None
            self.plan_memory = None

        def generate_analysis_goal(self, question, file_profile, business_context, memory_context):
            self.goal_memory = memory_context
            return "memory aware goal"

        def generate_analysis_plan(self, analysis_goal, file_profile, business_context, memory_context):
            self.plan_memory = memory_context
            return ["memory aware plan"]

        def generate_report(self, analysis_goal, intermediate_findings, chart_specs, business_context):
            return {}

        def judge_report(self, question, final_report, tool_results):
            return {}

    stub = MemoryAwareStubLLMClient()
    monkeypatch.setattr("app.services.task_builder.get_llm_client", lambda: stub)

    file_profile = {
        "file_id": "file_builder_memory",
        "filename": "sales_orders.csv",
        "row_count": 1,
        "column_count": 2,
        "columns": [{"name": "region", "type": "string"}, {"name": "sales_amount", "type": "number"}],
        "created_at": "2026-06-24T00:00:00+00:00",
    }

    SessionStore().save_file_memory(
        "file_builder_memory",
        {
            "scope": {"file_id": "file_builder_memory"},
            "recent_turns": [{"task_id": "task_prev", "question": "analyse sales by region", "analysis_goal": "compare region sales"}],
            "summary_memory": {"summary_text": "Previous analysis focused on region sales.", "turn_count": 1},
            "stats": {"recent_turn_count": 1, "summary_turn_count": 1, "memory_enabled": True},
        },
    )

    task_id, state = create_analysis_task(
        file_id="file_builder_memory",
        question="analyse sales by region again",
        source_node="test_builder",
        file_profile=file_profile,
        task_id="task_builder_memory",
    )

    assert task_id == "task_builder_memory"
    assert state["memory_context"]["recent_turns"][0]["task_id"] == "task_prev"
    assert state["memory_context"]["summary_memory"]["summary_text"] == "Previous analysis focused on region sales."
    assert stub.goal_memory["recent_turns"][0]["task_id"] == "task_prev"
    assert stub.plan_memory["summary_memory"]["turn_count"] == 1
```

- [ ] **Step 3: Add a red test for project-status runtime memory evidence**

```python
def test_get_project_status_surfaces_memory_runtime_evidence():
    task_id = "task_project_status_memory"
    state = {
        "task_id": task_id,
        "file_id": "file_project_status_memory",
        "question": "analyse sales by region again",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {},
        "business_context": [],
        "analysis_plan": ["match fields"],
        "memory_context": {
            "scope": {"file_id": "file_project_status_memory"},
            "recent_turns": [{"task_id": "task_prev", "question": "analyse sales by region"}],
            "summary_memory": {"summary_text": "Previous analysis focused on regional sales.", "turn_count": 2},
            "stats": {"recent_turn_count": 1, "summary_turn_count": 2, "memory_enabled": True},
        },
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "llm_judgement": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "created",
    }
    create_task(task_id, state["file_id"], state["question"], state)
    update_task_state(task_id, state)

    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    latest_task = response.json()["summary"]["latest_task"]
    assert latest_task["memory"]["memory_enabled"] is True
    assert latest_task["memory"]["recent_turn_count"] == 1
    assert latest_task["memory"]["summary_turn_count"] == 2
    assert latest_task["memory"]["summary_text"] == "Previous analysis focused on regional sales."
```

- [ ] **Step 4: Add red tests for LLM signature changes**

```python
def test_mock_llm_goal_uses_memory_context_note():
    client = MockLLMClient()
    goal = client.generate_analysis_goal(
        question="analyse sales by region",
        file_profile={"columns": [{"name": "region", "type": "string"}]},
        business_context=[{"title": "Region"}],
        memory_context={
            "recent_turns": [{"question": "analyse sales by region last week"}],
            "summary_memory": {"summary_text": "Historical focus: regional sales comparison."},
            "stats": {"recent_turn_count": 1, "summary_turn_count": 1, "memory_enabled": True},
        },
    )

    assert "historical focus" in goal.lower()
```

```python
def test_qwen_client_sends_memory_context_in_goal_request(monkeypatch):
    captured_payload = {}

    def _fake_urlopen(request, timeout):
        captured_payload.update(json.loads(request.data.decode("utf-8")))
        return StubResponse(200, _chat_payload(json.dumps({"analysis_goal": "Compare regional sales"})))

    monkeypatch.setattr("app.llm.qwen_client.urlopen", _fake_urlopen)
    client = QwenClient(api_key="test-key", base_url="https://example.com/v1", model="qwen-plus")
    client.generate_analysis_goal(
        question="analyse sales by region",
        file_profile={"columns": [{"name": "region"}]},
        business_context=[{"title": "Region"}],
        memory_context={"summary_memory": {"summary_text": "Previous regional sales analysis."}, "recent_turns": []},
    )

    user_payload = json.loads(captured_payload["messages"][1]["content"])
    assert "memory_context" in user_payload
    assert user_payload["memory_context"]["summary_memory"]["summary_text"] == "Previous regional sales analysis."
```

- [ ] **Step 5: Run focused tests to verify they fail for the expected reason**

Run:

```powershell
Set-Location 'E:\bgagent1\.worktrees\day1-mvp-backend\backend'
@'
import sys
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend\.venv\Lib\site-packages")
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend")
import pytest
raise SystemExit(pytest.main([
    "tests/test_session_store.py",
    "tests/test_task_builder.py",
    "tests/test_project_status_api.py",
    "tests/test_mock_llm.py",
    "tests/test_qwen_client.py",
    "-q",
]))
'@ | "C:\Program Files\LibreOffice\program\python.exe" -
```

Expected:

- failures because `append_turn_memory()` / `load_file_memory()` / `save_file_memory()` do not exist yet
- failures because `memory_context` is not present in task state or project status
- failures because LLM client signatures do not yet accept `memory_context`

- [ ] **Step 6: Commit the red acceptance state**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_session_store.py backend/tests/test_task_builder.py backend/tests/test_project_status_api.py backend/tests/test_mock_llm.py backend/tests/test_qwen_client.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze redis memory realization behavior"
```

### Task 2: Add Redis file-memory storage, window pruning, and summary compaction

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/storage/session_store.py`
- Modify: `backend/tests/test_session_store.py`

- [ ] **Step 1: Add explicit memory config knobs**

```python
MEMORY_ENABLED = get_bool_env("MEMORY_ENABLED", True)
MEMORY_MAX_RECENT_TURNS = int(get_env("MEMORY_MAX_RECENT_TURNS", "3") or "3")
MEMORY_SUMMARY_MAX_CHARS = int(get_env("MEMORY_SUMMARY_MAX_CHARS", "480") or "480")
```

- [ ] **Step 2: Extend `SessionStore` key layout for file-scoped memory**

```python
    def _build_file_memory_keys(self, file_id: str) -> dict[str, str]:
        return {
            "memory_snapshot": f"file_memory:{file_id}",
            "memory_recent_turns": f"file_memory_recent_turns:{file_id}",
            "memory_summary": f"file_memory_summary:{file_id}",
        }
```

- [ ] **Step 3: Add helper methods for summary compaction and default memory payload**

```python
    def _default_file_memory(self, file_id: str) -> dict:
        return {
            "scope": {"file_id": file_id},
            "recent_turns": [],
            "summary_memory": {"summary_text": "", "turn_count": 0},
            "stats": {"recent_turn_count": 0, "summary_turn_count": 0, "memory_enabled": True},
        }

    def _build_summary_text(self, archived_turns: list[dict], current_summary: str, max_chars: int) -> str:
        fragments = [current_summary.strip()] if current_summary.strip() else []
        for turn in archived_turns:
            fragments.append(
                f"Q: {turn.get('question', '')}; Goal: {turn.get('analysis_goal', '')}; Report: {(turn.get('final_report') or {}).get('title', '')}"
            )
        summary = " | ".join(fragment for fragment in fragments if fragment).strip()
        return summary[:max_chars]
```

- [ ] **Step 4: Implement Redis-backed file memory save/load/append methods**

```python
    def save_file_memory(self, file_id: str, memory: dict) -> bool:
        client = self._connect()
        snapshot = {
            "scope": memory.get("scope") or {"file_id": file_id},
            "recent_turns": memory.get("recent_turns") or [],
            "summary_memory": memory.get("summary_memory") or {"summary_text": "", "turn_count": 0},
            "stats": memory.get("stats") or {},
        }
        snapshot["stats"] = {
            "recent_turn_count": len(snapshot["recent_turns"]),
            "summary_turn_count": int(snapshot["summary_memory"].get("turn_count", 0) or 0),
            "memory_enabled": True,
        }
        if client is not None:
            keys = self._build_file_memory_keys(file_id)
            client.set(keys["memory_snapshot"], json.dumps(snapshot, ensure_ascii=False))
            client.set(keys["memory_recent_turns"], json.dumps(snapshot["recent_turns"], ensure_ascii=False))
            client.set(keys["memory_summary"], json.dumps(snapshot["summary_memory"], ensure_ascii=False))
            return True
        return False

    def load_file_memory(self, file_id: str) -> dict:
        client = self._connect()
        if client is None:
            return self._default_file_memory(file_id)
        payload = client.get(self._build_file_memory_keys(file_id)["memory_snapshot"])
        if not payload:
            return self._default_file_memory(file_id)
        memory = json.loads(payload)
        if "stats" not in memory:
            memory["stats"] = {
                "recent_turn_count": len(memory.get("recent_turns") or []),
                "summary_turn_count": int((memory.get("summary_memory") or {}).get("turn_count", 0) or 0),
                "memory_enabled": True,
            }
        return memory

    def append_turn_memory(
        self,
        file_id: str,
        task_id: str,
        question: str,
        analysis_goal: str,
        analysis_plan: list[str],
        final_report: dict,
        max_recent_turns: int,
        max_summary_chars: int = 480,
    ) -> dict:
        memory = self.load_file_memory(file_id)
        turn = {
            "task_id": task_id,
            "question": question,
            "analysis_goal": analysis_goal,
            "analysis_plan": analysis_plan,
            "final_report": final_report,
        }
        all_recent_turns = [*(memory.get("recent_turns") or []), turn]
        archived_turns = all_recent_turns[:-max_recent_turns] if len(all_recent_turns) > max_recent_turns else []
        recent_turns = all_recent_turns[-max_recent_turns:]
        previous_summary = (memory.get("summary_memory") or {}).get("summary_text", "")
        summary_turn_count = int((memory.get("summary_memory") or {}).get("turn_count", 0) or 0) + len(archived_turns)
        new_memory = {
            "scope": {"file_id": file_id},
            "recent_turns": recent_turns,
            "summary_memory": {
                "summary_text": self._build_summary_text(archived_turns, previous_summary, max_summary_chars),
                "turn_count": summary_turn_count,
            },
            "stats": {
                "recent_turn_count": len(recent_turns),
                "summary_turn_count": summary_turn_count,
                "memory_enabled": True,
            },
        }
        self.save_file_memory(file_id, new_memory)
        return new_memory
```

- [ ] **Step 5: Run the storage-focused tests**

Run:

```powershell
Set-Location 'E:\bgagent1\.worktrees\day1-mvp-backend\backend'
@'
import sys
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend\.venv\Lib\site-packages")
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend")
import pytest
raise SystemExit(pytest.main(["tests/test_session_store.py", "-q"]))
'@ | "C:\Program Files\LibreOffice\program\python.exe" -
```

Expected:

- new file-memory tests pass
- existing snapshot and lock tests remain green

- [ ] **Step 6: Commit the storage milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/core/config.py backend/app/storage/session_store.py backend/tests/test_session_store.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: add redis file memory storage"
```

### Task 3: Inject memory into analysis startup state and LLM goal/plan generation

**Files:**
- Modify: `backend/app/llm/base.py`
- Modify: `backend/app/llm/mock_client.py`
- Modify: `backend/app/llm/qwen_client.py`
- Modify: `backend/app/llm/prompt_templates.py`
- Modify: `backend/app/services/task_builder.py`
- Modify: `backend/app/schemas/analysis_schema.py`
- Modify: `backend/tests/test_task_builder.py`
- Modify: `backend/tests/test_mock_llm.py`
- Modify: `backend/tests/test_qwen_client.py`
- Modify: `backend/tests/test_analysis_api.py`
- Modify: `backend/tests/test_analysis_runner.py`
- Modify: `backend/tests/test_llm_api.py`

- [ ] **Step 1: Extend the LLM base interface with `memory_context`**

```python
class LLMClient(ABC):
    @abstractmethod
    def generate_analysis_goal(
        self,
        question: str,
        file_profile: dict,
        business_context: list[dict],
        memory_context: dict,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
        memory_context: dict,
    ) -> list[str]:
        raise NotImplementedError
```

- [ ] **Step 2: Make the mock client consume memory context truthfully**

```python
    def _memory_note(self, memory_context: dict) -> str:
        summary_text = ((memory_context.get("summary_memory") or {}).get("summary_text") or "").strip()
        recent_turns = memory_context.get("recent_turns") or []
        if summary_text:
            return f" Historical focus: {summary_text}"
        if recent_turns:
            return f" Historical focus: {recent_turns[-1].get('question', '')}."
        return ""

    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict], memory_context: dict) -> str:
        del file_profile
        lowered = question.lower()
        titles = self._context_titles(business_context)
        context_note = f" Context: {', '.join(titles)}." if titles else ""
        memory_note = self._memory_note(memory_context)
        if "region" in lowered and "sales" in lowered:
            return REGION_TEMPLATE + context_note + memory_note
        return FALLBACK_TEMPLATE + context_note + memory_note
```

- [ ] **Step 3: Pass memory context through Qwen payloads and prompts**

```python
GOAL_SYSTEM_PROMPT = (
    "You are an analytics planning assistant. "
    "Return JSON only with the key analysis_goal. "
    "Use provided memory_context only as historical planning context. "
    "Do not fabricate numeric results."
)
```

```python
        payload = self._chat_json(
            GOAL_SYSTEM_PROMPT,
            {
                "question": question,
                "file_profile": file_profile,
                "business_context": business_context,
                "memory_context": memory_context,
            },
        )
```

- [ ] **Step 4: Load file memory in `task_builder` and persist it into analysis state**

```python
def build_analysis_state(
    task_id: str,
    file_id: str,
    question: str,
    file_profile: dict,
    llm_client: LLMClient | None = None,
) -> tuple[dict, list[dict], str, list[str]]:
    client = llm_client or get_llm_client()
    session_store = SessionStore()
    memory_context = session_store.load_file_memory(file_id)
    business_context = retrieve_business_context(question, file_profile)["items"]
    analysis_goal = client.generate_analysis_goal(question, file_profile, business_context, memory_context)
    analysis_plan = client.generate_analysis_plan(analysis_goal, file_profile, business_context, memory_context)

    state = {
        "task_id": task_id,
        "file_id": file_id,
        "question": question,
        "analysis_goal": analysis_goal,
        "file_profile": file_profile,
        "field_understanding": {},
        "business_context": business_context,
        "memory_context": memory_context,
        "analysis_plan": analysis_plan,
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "llm_judgement": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "created",
    }
```

- [ ] **Step 5: Add `memory_context` to the response schema and API expectations**

```python
class AnalysisTaskState(BaseModel):
    task_id: str
    file_id: str
    question: str
    analysis_goal: str
    file_profile: dict[str, Any]
    field_understanding: dict[str, Any]
    business_context: list[dict[str, Any]]
    memory_context: dict[str, Any] = Field(default_factory=dict)
    analysis_plan: list[str]
    ...
```

- [ ] **Step 6: Update all test doubles to the new signature**

```python
class FailingGoalLLMClient:
    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict], memory_context: dict) -> str:
        del question
        del file_profile
        del business_context
        del memory_context
        raise QwenResponseError("simulated provider failure")

    def generate_analysis_plan(self, analysis_goal: str, file_profile: dict, business_context: list[dict], memory_context: dict) -> list[str]:
        del analysis_goal
        del file_profile
        del business_context
        del memory_context
        return []
```

- [ ] **Step 7: Run startup and LLM-focused tests**

Run:

```powershell
Set-Location 'E:\bgagent1\.worktrees\day1-mvp-backend\backend'
@'
import sys
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend\.venv\Lib\site-packages")
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend")
import pytest
raise SystemExit(pytest.main([
    "tests/test_task_builder.py",
    "tests/test_mock_llm.py",
    "tests/test_qwen_client.py",
    "tests/test_analysis_api.py",
    "tests/test_analysis_runner.py",
    "tests/test_llm_api.py",
    "-q",
]))
'@ | "C:\Program Files\LibreOffice\program\python.exe" -
```

Expected:

- memory-aware builder tests pass
- API tests continue to pass with `memory_context` present in persisted state responses
- Qwen payload tests prove `memory_context` is serialized

- [ ] **Step 8: Commit the memory-injection milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/llm/base.py backend/app/llm/mock_client.py backend/app/llm/qwen_client.py backend/app/llm/prompt_templates.py backend/app/services/task_builder.py backend/app/schemas/analysis_schema.py backend/tests/test_task_builder.py backend/tests/test_mock_llm.py backend/tests/test_qwen_client.py backend/tests/test_analysis_api.py backend/tests/test_analysis_runner.py backend/tests/test_llm_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: inject redis memory into analysis planning"
```

### Task 4: Surface runtime memory evidence in project overview and demo

**Files:**
- Modify: `backend/app/api/project_status.py`
- Modify: `backend/app/api/demo.py`
- Modify: `backend/tests/test_project_status_api.py`

- [ ] **Step 1: Add memory metrics to `latest_task` summary**

```python
    memory_context = state.get("memory_context") or {}
    memory_summary = memory_context.get("summary_memory") or {}
    memory_stats = memory_context.get("stats") or {}
    recent_turns = memory_context.get("recent_turns") or []
    latest_memory_turn = recent_turns[-1] if recent_turns else {}
    ...
        "memory": {
            "memory_enabled": bool(memory_stats.get("memory_enabled")),
            "recent_turn_count": len(recent_turns),
            "summary_turn_count": int(memory_summary.get("turn_count", 0) or 0),
            "summary_text": memory_summary.get("summary_text"),
            "latest_memory_task_id": latest_memory_turn.get("task_id"),
            "latest_memory_question": latest_memory_turn.get("question"),
        },
```

- [ ] **Step 2: Add file-memory runtime summary to `session_store` block**

```python
def _session_store_info() -> dict:
    ...
    sample_memory = store.load_file_memory("__project_status_probe__")
    return {
        "preferred_backend": "redis",
        "active_backend": "redis" if redis_available else "sqlite",
        "redis_available": redis_available,
        "degraded_to_sqlite": not redis_available,
        "redis_url": redis_url,
        "memory_capabilities": {
            "memory_enabled": config.MEMORY_ENABLED,
            "max_recent_turns": config.MEMORY_MAX_RECENT_TURNS,
            "summary_max_chars": config.MEMORY_SUMMARY_MAX_CHARS,
            "probe_recent_turn_count": len(sample_memory.get("recent_turns") or []),
        },
        "event_summary": {...},
    }
```

- [ ] **Step 3: Add a read-only memory card to `/demo`**

```javascript
      const latestTaskMemory = latestTask?.memory || {};
      latestTaskMemoryPillEl.textContent = latestTask ? "Memory ready" : "No tasks";
      latestTaskMemoryMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `recent_turns: ${latestTaskMemory.recent_turn_count ?? 0}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskMemoryOutputEl.textContent = latestTask ? [
        `memory_enabled: ${latestTaskMemory.memory_enabled ?? false}`,
        `recent_turn_count: ${latestTaskMemory.recent_turn_count ?? 0}`,
        `summary_turn_count: ${latestTaskMemory.summary_turn_count ?? 0}`,
        `latest_memory_task_id: ${latestTaskMemory.latest_memory_task_id || "none"}`,
        `latest_memory_question: ${latestTaskMemory.latest_memory_question || "none"}`,
        `summary_text: ${latestTaskMemory.summary_text || "none"}`,
      ].join("\\n") : "No latest task memory summary loaded yet.";
```

- [ ] **Step 4: Run the runtime-evidence tests**

Run:

```powershell
Set-Location 'E:\bgagent1\.worktrees\day1-mvp-backend\backend'
@'
import sys
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend\.venv\Lib\site-packages")
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend")
import pytest
raise SystemExit(pytest.main(["tests/test_project_status_api.py", "-q"]))
'@ | "C:\Program Files\LibreOffice\program\python.exe" -
```

Expected:

- project-status tests pass with memory evidence exposed
- no existing retrieval / tool / eval assertions regress

- [ ] **Step 5: Commit the runtime-evidence milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/project_status.py backend/app/api/demo.py backend/tests/test_project_status_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: surface redis memory runtime evidence"
```

### Task 5: Append completed tasks into file memory and verify the full backend suite

**Files:**
- Modify: `backend/app/services/analysis_runner.py`
- Modify: `backend/tests/test_analysis_runner.py`
- Modify: `backend/tests/test_analysis_api.py`
- Modify: `backend/tests/test_delivery_docs.py`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`

- [ ] **Step 1: Append successful task outcomes into file memory at the end of analysis**

```python
    if state["status"] == "completed":
        SessionStore().append_turn_memory(
            file_id=state["file_id"],
            task_id=task_id,
            question=state["question"],
            analysis_goal=state["analysis_goal"],
            analysis_plan=state.get("analysis_plan") or [],
            final_report=state.get("final_report") or {},
            max_recent_turns=config.MEMORY_MAX_RECENT_TURNS,
            max_summary_chars=config.MEMORY_SUMMARY_MAX_CHARS,
        )
```

- [ ] **Step 2: Add an end-to-end regression proving a second task sees the first task in memory**

```python
def test_start_analysis_second_task_reads_memory_from_first_completed_task(tmp_path):
    client = TestClient(app)
    upload = client.post("/api/files/upload-sample")
    file_id = upload.json()["file_id"]

    first_start = client.post("/api/analysis/start", json={"file_id": file_id, "question": "analyse sales by region"})
    first_task_id = first_start.json()["task_id"]
    first_run = client.post(f"/api/analysis/{first_task_id}/run")
    assert first_run.status_code == 200

    second_start = client.post("/api/analysis/start", json={"file_id": file_id, "question": "analyse sales by region again"})
    assert second_start.status_code == 200

    second_state = client.get(f"/api/analysis/{second_start.json()['task_id']}").json()
    assert second_state["memory_context"]["recent_turns"]
    assert second_state["memory_context"]["recent_turns"][-1]["task_id"] == first_task_id
```

- [ ] **Step 3: Tighten delivery docs to mention real Redis memory mechanics**

```python
def test_resume_project_description_mentions_real_redis_memory():
    content = (Path(__file__).resolve().parents[2] / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(encoding="utf-8")

    assert "Redis" in content
    assert "sliding window" in content or "滑动窗口" in content
    assert "summary memory" in content or "摘要记忆" in content
    assert "memory_context" in content
```

- [ ] **Step 4: Run the full backend suite**

Run:

```powershell
Set-Location 'E:\bgagent1\.worktrees\day1-mvp-backend\backend'
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
@'
import sys
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend\.venv\Lib\site-packages")
sys.path.insert(0, r"E:\bgagent1\.worktrees\day1-mvp-backend\backend")
import pytest
raise SystemExit(pytest.main(["-q"]))
'@ | "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- full suite passes
- no stale `.pytest-tmp` directory remains in the worktree

- [ ] **Step 5: Commit the phase completion**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/services/analysis_runner.py backend/tests/test_analysis_runner.py backend/tests/test_analysis_api.py backend/tests/test_delivery_docs.py docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align redis memory evidence with resume wording"
```
