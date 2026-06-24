# LLM-As-Judge Realization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the current lightweight `llm_judgement` into a truthful structured LLM-as-Judge subsystem that evaluates report quality against packed evidence, persists dedicated judge outputs, and exposes explicit degradation behavior through APIs and runtime overview.

**Architecture:** Keep the deterministic `rule_scorer` as the numeric truth baseline, but add a dedicated judge schema and evidence pack beside it. The judge should consume task question, final report, tool outputs, retrieval evidence, and trace evidence, then emit dimensioned judge outputs plus degradation metadata without replacing rule-based scoring.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, existing `QwenClient`, existing `rule_scorer`, existing `/api/eval/run`, `/api/project-status`, `/demo`

---

### Task 1: Freeze full judge acceptance tests

**Files:**
- Modify: `backend/tests/test_analysis_runner.py`
- Modify: `backend/tests/test_analysis_api.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_qwen_client.py`
- Create: `backend/tests/test_judge_schema.py`

- [ ] **Step 1: Add a red schema test for structured judge output**

```python
from app.schemas.judge_schema import JudgeResult


def test_judge_result_requires_dimensions_and_summary():
    result = JudgeResult.model_validate(
        {
            "judge_summary": "Report is well grounded in tool evidence.",
            "judge_status": "ok",
            "dimensions": {
                "groundedness": {"score": 0.95, "verdict": "supported", "rationale": "Tool rows support the key findings."},
                "completeness": {"score": 0.9, "verdict": "complete", "rationale": "Required report sections are present."},
                "clarity": {"score": 0.88, "verdict": "clear", "rationale": "The report is understandable."},
            },
            "issue_count": 0,
            "issues": [],
            "degraded": False,
        }
    )

    assert result.judge_status == "ok"
    assert result.dimensions["groundedness"].score == 0.95
```

- [ ] **Step 2: Add a red runner test that requires full judge output in completed state**

```python
def test_run_analysis_task_records_structured_llm_judge(tmp_path: Path, monkeypatch):
    class JudgeStubLLMClient(RunnerStubLLMClient):
        def judge_report(self, question: str, final_report: dict, tool_results: list[dict], judge_evidence: dict) -> dict:
            assert question == "analyse sales by region"
            assert judge_evidence["question"] == "analyse sales by region"
            assert judge_evidence["final_report"]["title"] == "LLM Final Report"
            assert judge_evidence["tool_results"][0]["tool_name"] == "groupby_aggregate"
            return {
                "judge_summary": "Report is grounded in the deterministic aggregation.",
                "judge_status": "ok",
                "dimensions": {
                    "groundedness": {"score": 0.96, "verdict": "supported", "rationale": "Rows support the key finding."},
                    "completeness": {"score": 0.92, "verdict": "complete", "rationale": "Required sections exist."},
                    "clarity": {"score": 0.9, "verdict": "clear", "rationale": "Language is concise."},
                },
                "issue_count": 0,
                "issues": [],
                "degraded": False,
            }

    monkeypatch.setattr("app.agent.nodes.get_llm_client", lambda: JudgeStubLLMClient())
    ...
    result = run_analysis_task(task_id)

    assert result["llm_judgement"]["judge_status"] == "ok"
    assert result["llm_judgement"]["judge_summary"] != ""
    assert result["llm_judgement"]["dimensions"]["groundedness"]["score"] == 0.96
```

- [ ] **Step 3: Add a red API test for judge degradation instead of task failure**

```python
def test_run_analysis_degrades_when_llm_judge_fails(tmp_path, monkeypatch):
    class JudgeFailingClient(FailingGoalLLMClient):
        def generate_analysis_goal(self, question, file_profile, business_context, memory_context):
            return "compare region sales"

        def generate_analysis_plan(self, analysis_goal, file_profile, business_context, memory_context):
            return ["match fields", "aggregate", "chart", "report"]

        def generate_report(self, analysis_goal, intermediate_findings, chart_specs, business_context):
            return {
                "title": "Judge fallback report",
                "analysis_goal": analysis_goal,
                "key_findings": [{"finding": "East performs best", "evidence": "1200", "source_tool": "groupby_aggregate"}],
                "chart_explanations": ["Bar chart compares regional sales totals."],
                "business_suggestions": ["Focus on East."],
                "data_limitations": ["Uploaded CSV only."],
                "next_steps": ["Check by channel."],
            }

        def judge_report(self, question, final_report, tool_results, judge_evidence):
            raise QwenResponseError("judge provider failure")

    monkeypatch.setattr("app.agent.nodes.get_llm_client", lambda: JudgeFailingClient())
    ...
    run = client.post(f"/api/analysis/{task_id}/run")

    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["llm_judgement"]["degraded"] is True
    assert run.json()["llm_judgement"]["judge_status"] == "degraded"
    assert run.json()["errors"][-1]["code"] == "LLM_JUDGEMENT_DEGRADED"
```

- [ ] **Step 4: Add a red project-status test for surfaced judge dimensions**

```python
def test_get_project_status_surfaces_structured_judge_dimensions():
    task_id = "task_project_status_judge"
    state = {
        "task_id": task_id,
        "file_id": "file_project_status_judge",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {},
        "business_context": [],
        "analysis_plan": ["match fields"],
        "current_step": "completed",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "llm_judgement": {
            "judge_summary": "Report is grounded in tool evidence.",
            "judge_status": "ok",
            "dimensions": {
                "groundedness": {"score": 0.96, "verdict": "supported", "rationale": "Tool rows support the key finding."},
                "completeness": {"score": 0.92, "verdict": "complete", "rationale": "Required sections exist."},
                "clarity": {"score": 0.9, "verdict": "clear", "rationale": "Language is concise."},
            },
            "issue_count": 0,
            "issues": [],
            "degraded": False,
        },
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "completed",
    }
    create_task(task_id, state["file_id"], state["question"], state)
    update_task_state(task_id, state)

    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    judgement = response.json()["summary"]["latest_task"]["judgement"]
    assert judgement["judge_status"] == "ok"
    assert judgement["groundedness_score"] == 0.96
    assert judgement["completeness_score"] == 0.92
    assert judgement["clarity_score"] == 0.9
```

- [ ] **Step 5: Add a red Qwen client test for the new judge payload shape**

```python
def test_qwen_client_parses_structured_judge_response(monkeypatch):
    from app.llm.qwen_client import QwenClient

    monkeypatch.setattr(
        "app.llm.qwen_client.urlopen",
        lambda request, timeout: StubResponse(
            200,
            _chat_payload(
                json.dumps(
                    {
                        "judge_summary": "Report is grounded in tool evidence.",
                        "judge_status": "ok",
                        "dimensions": {
                            "groundedness": {"score": 0.96, "verdict": "supported", "rationale": "Rows support the key finding."},
                            "completeness": {"score": 0.92, "verdict": "complete", "rationale": "Sections exist."},
                            "clarity": {"score": 0.9, "verdict": "clear", "rationale": "Language is concise."},
                        },
                        "issue_count": 0,
                        "issues": [],
                        "degraded": False,
                    }
                )
            ),
        ),
    )

    client = QwenClient(api_key="test-key", base_url="https://example.com/v1", model="qwen-plus")
    result = client.judge_report(
        question="analyse sales by region",
        final_report={"title": "Report"},
        tool_results=[{"tool_name": "groupby_aggregate", "data": {"rows": [{"region": "East"}]}}],
        judge_evidence={"question": "analyse sales by region"},
    )

    assert result["judge_status"] == "ok"
    assert result["dimensions"]["groundedness"]["score"] == 0.96
```

- [ ] **Step 6: Run focused tests to verify they fail for missing judge structure**

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
    "tests/test_judge_schema.py",
    "tests/test_analysis_runner.py",
    "tests/test_analysis_api.py",
    "tests/test_project_status_api.py",
    "tests/test_qwen_client.py",
    "-q",
]))
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- failures because `JudgeResult` schema does not exist yet
- failures because `judge_report()` still expects the old narrow shape
- failures because judge degradation currently fails the whole task
- failures because `project-status` does not yet surface judge dimensions

- [ ] **Step 7: Commit the red acceptance state**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_analysis_runner.py backend/tests/test_analysis_api.py backend/tests/test_project_status_api.py backend/tests/test_qwen_client.py backend/tests/test_judge_schema.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze llm judge realization behavior"
```

### Task 2: Add dedicated judge schemas and normalize judge payloads

**Files:**
- Create: `backend/app/schemas/judge_schema.py`
- Modify: `backend/app/llm/base.py`
- Modify: `backend/app/llm/qwen_client.py`
- Modify: `backend/app/llm/mock_client.py`
- Modify: `backend/app/llm/prompt_templates.py`
- Modify: `backend/tests/test_judge_schema.py`
- Modify: `backend/tests/test_qwen_client.py`

- [ ] **Step 1: Create judge schema models**

```python
from typing import Literal

from pydantic import BaseModel, Field


class JudgeDimension(BaseModel):
    score: float
    verdict: str
    rationale: str


class JudgeResult(BaseModel):
    judge_summary: str
    judge_status: Literal["ok", "degraded"]
    dimensions: dict[str, JudgeDimension]
    issue_count: int
    issues: list[str] = Field(default_factory=list)
    degraded: bool = False
```

- [ ] **Step 2: Extend the LLM base interface for packed judge evidence**

```python
    @abstractmethod
    def judge_report(
        self,
        question: str,
        final_report: dict,
        tool_results: list[dict],
        judge_evidence: dict,
    ) -> dict:
        raise NotImplementedError
```

- [ ] **Step 3: Update judge prompt wording to require structured dimensions**

```python
JUDGE_SYSTEM_PROMPT = (
    "You are an analytics quality reviewer. "
    "Return JSON only with judge_summary, judge_status, dimensions, issue_count, issues, and degraded. "
    "Dimensions must include groundedness, completeness, and clarity. "
    "Do not invent unsupported evidence."
)
```

- [ ] **Step 4: Normalize Qwen judge payloads through `JudgeResult`**

```python
    def judge_report(self, question: str, final_report: dict, tool_results: list[dict], judge_evidence: dict) -> dict:
        payload = self._chat_json(
            JUDGE_SYSTEM_PROMPT,
            {
                "question": question,
                "final_report": final_report,
                "tool_results": tool_results,
                "judge_evidence": judge_evidence,
            },
        )
        return JudgeResult.model_validate(payload).model_dump()
```

- [ ] **Step 5: Make the mock client emit a full judge structure**

```python
    def judge_report(self, question: str, final_report: dict, tool_results: list[dict], judge_evidence: dict) -> dict:
        del question
        del judge_evidence
        has_findings = bool(final_report.get("key_findings"))
        has_tool_rows = any(item.get("data", {}).get("rows") for item in tool_results)
        issues = []
        if not has_findings:
            issues.append("Report contains no key findings.")
        if not has_tool_rows:
            issues.append("No tool rows were available for judging.")
        return {
            "judge_summary": "Mock judge completed using deterministic tool presence checks.",
            "judge_status": "ok",
            "dimensions": {
                "groundedness": {"score": 1.0 if has_tool_rows else 0.2, "verdict": "supported" if has_tool_rows else "weak", "rationale": "Checks whether tool rows exist."},
                "completeness": {"score": 1.0 if has_findings else 0.3, "verdict": "complete" if has_findings else "partial", "rationale": "Checks whether findings exist."},
                "clarity": {"score": 0.8, "verdict": "clear", "rationale": "Mock client emits a concise summary."},
            },
            "issue_count": len(issues),
            "issues": issues,
            "degraded": False,
        }
```

- [ ] **Step 6: Run schema and client tests**

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
    "tests/test_judge_schema.py",
    "tests/test_qwen_client.py",
    "-q",
]))
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- judge schema tests pass
- Qwen structured judge parsing tests pass

- [ ] **Step 7: Commit the schema milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/schemas/judge_schema.py backend/app/llm/base.py backend/app/llm/qwen_client.py backend/app/llm/mock_client.py backend/app/llm/prompt_templates.py backend/tests/test_judge_schema.py backend/tests/test_qwen_client.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: add structured llm judge schema"
```

### Task 3: Pack judge evidence and degrade gracefully in graph execution

**Files:**
- Modify: `backend/app/agent/nodes.py`
- Modify: `backend/tests/test_analysis_runner.py`
- Modify: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Add a helper to pack judge evidence**

```python
def _build_judge_evidence(state: AnalysisGraphState) -> dict:
    return {
        "question": state["question"],
        "analysis_goal": state["analysis_goal"],
        "final_report": state["final_report"],
        "tool_results": state["tool_results"],
        "business_context": state.get("business_context") or [],
        "memory_context": state.get("memory_context") or {},
        "events": state.get("events") or [],
        "eval_result": state.get("eval_result") or {},
    }
```

- [ ] **Step 2: Change judge failure from fatal to explicit degradation**

```python
    judge_evidence = _build_judge_evidence(state)
    try:
        llm_client = get_llm_client()
        state["llm_judgement"] = llm_client.judge_report(
            state["question"],
            state["final_report"],
            state["tool_results"],
            judge_evidence,
        )
    except (LLMConfigurationError, QwenResponseError) as exc:
        state["llm_judgement"] = {
            "judge_summary": "Judge degraded because the provider call failed.",
            "judge_status": "degraded",
            "dimensions": {},
            "issue_count": 1,
            "issues": [str(exc)],
            "degraded": True,
        }
        state["errors"].append(
            {
                "code": "LLM_JUDGEMENT_DEGRADED",
                "message": str(exc),
                "details": {"final_report_available": bool(state.get("final_report"))},
            }
        )
```

- [ ] **Step 3: Preserve task completion even when judge degrades**

```python
    state["current_step"] = "completed"
    state["status"] = "completed"
    record_task_completed(state["task_id"], "langgraph")
    hydrate_state_events(state)
    state["eval_result"] = score_task_state(state)
```

- [ ] **Step 4: Run graph and API regression tests**

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
    "tests/test_analysis_runner.py",
    "tests/test_analysis_api.py",
    "-q",
]))
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- completed-task judge tests pass
- judge provider failure no longer fails the whole task

- [ ] **Step 5: Commit the graph-integration milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/agent/nodes.py backend/tests/test_analysis_runner.py backend/tests/test_analysis_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: add judge evidence pack and degradation path"
```

### Task 4: Surface judge dimensions through eval and runtime overview

**Files:**
- Modify: `backend/app/api/eval.py`
- Modify: `backend/app/api/project_status.py`
- Modify: `backend/app/api/demo.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_llm_api.py`

- [ ] **Step 1: Expose judge dimensions in `project-status`**

```python
    llm_judgement = state.get("llm_judgement") or {}
    dimensions = llm_judgement.get("dimensions") or {}
    groundedness = dimensions.get("groundedness") or {}
    completeness = dimensions.get("completeness") or {}
    clarity = dimensions.get("clarity") or {}
    ...
        "judgement": {
            "judge_status": llm_judgement.get("judge_status"),
            "judge_summary": llm_judgement.get("judge_summary"),
            "degraded": bool(llm_judgement.get("degraded")),
            "issue_count": int(llm_judgement.get("issue_count", 0) or 0),
            "groundedness_score": groundedness.get("score"),
            "completeness_score": completeness.get("score"),
            "clarity_score": clarity.get("score"),
        },
```

- [ ] **Step 2: Keep `/api/eval/run` output honest by preserving rule and judge separation**

```python
    eval_result = score_task_state(state)
    eval_result["judge_status"] = (state.get("llm_judgement") or {}).get("judge_status")
    eval_result["judge_degraded"] = bool((state.get("llm_judgement") or {}).get("degraded"))
```

- [ ] **Step 3: Add a read-only judge card update in `/demo`**

```javascript
      latestTaskJudgementOutputEl.textContent = latestTask ? [
        `judge_status: ${latestTaskJudgement.judge_status || "none"}`,
        `judge_summary: ${latestTaskJudgement.judge_summary || "none"}`,
        `degraded: ${latestTaskJudgement.degraded ?? false}`,
        `groundedness_score: ${latestTaskJudgement.groundedness_score ?? "none"}`,
        `completeness_score: ${latestTaskJudgement.completeness_score ?? "none"}`,
        `clarity_score: ${latestTaskJudgement.clarity_score ?? "none"}`,
        `issue_count: ${latestTaskJudgement.issue_count ?? 0}`,
      ].join("\\n") : "No latest task judgement summary loaded yet.";
```

- [ ] **Step 4: Run runtime-evidence tests**

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
    "tests/test_llm_api.py",
    "-q",
]))
'@ | & "C:\Program Files\LibreOffice\program\python.exe" -
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
```

Expected:

- project-status judge dimension tests pass
- runtime overview remains backward compatible for other summaries

- [ ] **Step 5: Commit the runtime-evidence milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/eval.py backend/app/api/project_status.py backend/app/api/demo.py backend/tests/test_project_status_api.py backend/tests/test_llm_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: surface llm judge runtime evidence"
```

### Task 5: Align docs and run full backend verification

**Files:**
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `backend/tests/test_delivery_docs.py`
- Modify: `backend/tests/test_eval_cases.py`

- [ ] **Step 1: Update wording from supplementary `llm_judgement` to real structured judge**

```markdown
- LLM-as-Judge now emits:
  - `judge_summary`
  - `judge_status`
  - dimension scores for groundedness, completeness, and clarity
  - explicit degradation metadata when provider calls fail
```

- [ ] **Step 2: Extend doc tests to require structured judge terminology**

```python
def test_delivery_docs_mention_structured_llm_judge():
    content = (Path(__file__).resolve().parents[2] / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(
        encoding="utf-8"
    )

    assert "LLM-as-Judge" in content or "llm-as-judge" in content.lower()
    assert "judge_summary" in content
    assert "groundedness" in content
    assert "completeness" in content
    assert "clarity" in content
```

- [ ] **Step 3: Extend fixed eval case summary expectations for judge metadata**

```python
def test_run_fixed_eval_cases_returns_passing_summary():
    summary = run_fixed_eval_cases()

    assert all(item["judge_status"] in {"ok", "degraded"} for item in summary["results"])
```

- [ ] **Step 4: Run full backend suite**

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

- [ ] **Step 5: Commit the phase completion**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md backend/tests/test_delivery_docs.py backend/tests/test_eval_cases.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align llm judge evidence with resume wording"
```
