# LLM-As-Judge Closure Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the current `LLM-as-Judge` subsystem as a truthful standard-closure milestone by tightening the packed judge evidence, exposing stable judge runtime summaries through `/api/eval/run`, `/api/project-status`, `/demo`, and fixed eval outputs, and aligning delivery docs around one consistent story.

**Architecture:** Keep the current structured judge schema, current three dimensions, and current non-fatal degradation semantics. Do not expand into a new judge platform. Instead, use the existing task state, provider layer, and runtime-overview surfaces to make the judge easier to inspect, easier to explain, and easier to demonstrate while preserving a strict separation from deterministic `RuleScorer`.

**Tech Stack:** FastAPI, Pydantic, existing Qwen provider integration, existing analysis graph, existing runtime overview and demo page, pytest

---

### Task 1: Freeze the missing closure behaviors in tests

**Files:**
- Modify: `backend/tests/test_analysis_runner.py`
- Modify: `backend/tests/test_analysis_api.py`
- Modify: `backend/tests/test_eval_cases.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add a red runner test that requires packed judge evidence to include process context**

```python
def test_run_analysis_task_packs_extended_judge_evidence(tmp_path: Path, monkeypatch):
    class JudgeEvidenceLLMClient(RunnerStubLLMClient):
        def judge_report(self, question: str, final_report: dict, tool_results: list[dict], judge_evidence: dict) -> dict:
            assert question == "analyse sales by region"
            assert judge_evidence["question"] == "analyse sales by region"
            assert judge_evidence["analysis_goal"] == "compare region sales"
            assert judge_evidence["final_report"]["title"] == "LLM Final Report"
            assert judge_evidence["tool_results"][0]["tool_name"] == "groupby_aggregate"
            assert isinstance(judge_evidence["business_context"], list)
            assert isinstance(judge_evidence["events"], list)
            assert "trace_summary" in judge_evidence
            assert "eval_baseline" in judge_evidence
            return {
                "judge_summary": "Judge reviewed packed execution evidence.",
                "judge_status": "ok",
                "dimensions": {
                    "groundedness": {"score": 0.96, "verdict": "supported", "rationale": "Tool rows support the key finding."},
                    "completeness": {"score": 0.92, "verdict": "complete", "rationale": "Required sections exist."},
                    "clarity": {"score": 0.9, "verdict": "clear", "rationale": "Language is concise."},
                },
                "issue_count": 0,
                "issues": [],
                "degraded": False,
            }

    monkeypatch.setattr("app.agent.nodes.get_llm_client", lambda: JudgeEvidenceLLMClient())
    ...
    result = run_analysis_task(task_id)

    assert result["llm_judgement"]["judge_status"] == "ok"
    assert result["llm_judgement"]["judge_summary"] == "Judge reviewed packed execution evidence."
```

- [ ] **Step 2: Add a red eval API test that requires judge summary fields to be returned separately from rule score**

```python
def test_eval_run_returns_judge_summary_fields(tmp_path):
    ...
    response = client.post("/api/eval/run", json={"task_id": task_id})

    assert response.status_code == 200
    eval_result = response.json()["eval_result"]
    assert eval_result["judge_status"] in {"ok", "degraded"}
    assert "judge_degraded" in eval_result
    assert "judge_summary" in eval_result
    assert "judge_issue_count" in eval_result
```

- [ ] **Step 3: Add a red fixed-eval test that requires judge metadata per case**

```python
def test_run_fixed_eval_cases_returns_judge_metadata():
    summary = run_fixed_eval_cases()

    assert all(item["judge_status"] in {"ok", "degraded"} for item in summary["results"])
    assert all("judge_degraded" in item for item in summary["results"])
    assert all("judge_issue_count" in item for item in summary["results"])
```

- [ ] **Step 4: Add a red doc test for standard-closure judge wording**

```python
def test_delivery_docs_mention_standard_llm_judge_runtime_evidence():
    repo_root = Path(__file__).resolve().parents[2]
    resume_description = (repo_root / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(encoding="utf-8")
    project_status = (repo_root / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")

    assert "packed evidence" in resume_description or "judge evidence" in resume_description
    assert "judge_status" in project_status
    assert "judge_summary" in project_status
    assert "judge_degraded" in project_status or "degraded" in project_status
```

- [ ] **Step 5: Run focused tests to verify the red state**

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
    "tests/test_analysis_runner.py",
    "tests/test_analysis_api.py",
    "tests/test_eval_cases.py",
    "tests/test_delivery_docs.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- runner tests fail because judge evidence is not yet packed to the stricter shape
- eval API tests fail because judge summary fields are not yet included in `eval_result`
- fixed eval tests fail because per-case judge metadata is incomplete
- doc tests fail because the delivery wording is not yet aligned

- [ ] **Step 6: Commit the red acceptance state**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_analysis_runner.py backend/tests/test_analysis_api.py backend/tests/test_eval_cases.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze llm judge closure enhancement"
```

### Task 2: Tighten the packed judge evidence in graph execution

**Files:**
- Modify: `backend/app/agent/nodes.py`
- Modify: `backend/tests/test_analysis_runner.py`

- [ ] **Step 1: Extend `_build_judge_evidence()` with compact trace and rule-baseline summaries**

```python
def _build_judge_evidence(state: AnalysisGraphState) -> dict:
    events = state.get("events") or []
    eval_result = state.get("eval_result") or {}
    return {
        "question": state["question"],
        "analysis_goal": state["analysis_goal"],
        "final_report": state["final_report"],
        "tool_results": state["tool_results"],
        "business_context": state.get("business_context") or [],
        "memory_context": state.get("memory_context") or {},
        "events": events,
        "trace_summary": {
            "event_count": len(events),
            "latest_event_type": events[-1].get("event_type") if events else None,
            "completed_step_count": len(state.get("completed_steps") or []),
        },
        "eval_result": eval_result,
        "eval_baseline": {
            "overall_score": eval_result.get("overall_score"),
            "tool_success_rate": eval_result.get("tool_success_rate"),
            "report_completeness": eval_result.get("report_completeness"),
            "trace_completeness": eval_result.get("trace_completeness"),
        },
    }
```

- [ ] **Step 2: Keep the current judge degradation behavior intact while preserving the stricter evidence pack**

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
```

- [ ] **Step 3: Run focused runner tests**

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
    "tests/test_analysis_runner.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- runner tests pass
- judge evidence pack is now stricter and test-backed

- [ ] **Step 4: Commit the graph-closure milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/agent/nodes.py backend/tests/test_analysis_runner.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: tighten llm judge evidence pack"
```

### Task 3: Expose standard judge summaries through eval and fixed-eval outputs

**Files:**
- Modify: `backend/app/api/eval.py`
- Modify: `backend/app/eval/eval_cases.py`
- Modify: `backend/tests/test_analysis_api.py`
- Modify: `backend/tests/test_eval_cases.py`

- [ ] **Step 1: Extend `/api/eval/run` output with compact judge metadata**

```python
    eval_result = score_task_state(state)
    llm_judgement = state.get("llm_judgement") or {}
    eval_result["judge_status"] = llm_judgement.get("judge_status")
    eval_result["judge_degraded"] = bool(llm_judgement.get("degraded"))
    eval_result["judge_summary"] = llm_judgement.get("judge_summary")
    eval_result["judge_issue_count"] = int(llm_judgement.get("issue_count", 0) or 0)
```

- [ ] **Step 2: Extend fixed eval result rows with compact judge metadata**

```python
    return {
        "case_id": case["case_id"],
        "question": case["question"],
        "passed": len(failures) == 0,
        "task_id": result["task_id"],
        "status": result["status"],
        "judge_status": (result.get("llm_judgement") or {}).get("judge_status"),
        "judge_degraded": bool((result.get("llm_judgement") or {}).get("degraded")),
        "judge_issue_count": int((result.get("llm_judgement") or {}).get("issue_count", 0) or 0),
        ...
    }
```

- [ ] **Step 3: Run focused eval and fixed-eval tests**

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
    "tests/test_analysis_api.py",
    "tests/test_eval_cases.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- eval API tests pass
- fixed eval summary now exposes compact judge metadata per case

- [ ] **Step 4: Commit the eval-output milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/eval.py backend/app/eval/eval_cases.py backend/tests/test_analysis_api.py backend/tests/test_eval_cases.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: expose llm judge summaries in eval outputs"
```

### Task 4: Finish runtime evidence through project status and demo

**Files:**
- Modify: `backend/app/api/project_status.py`
- Modify: `backend/app/api/demo.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_demo_page.py`

- [ ] **Step 1: Keep `project-status` judgement summary stable and explicit**

```python
        "judgement": {
            "supported_by_tools": llm_judgement.get("supported_by_tools"),
            "has_findings": llm_judgement.get("has_findings"),
            "judge_status": llm_judgement.get("judge_status"),
            "judge_summary": llm_judgement.get("judge_summary"),
            "degraded": bool(llm_judgement.get("degraded")),
            "issue_count": int(llm_judgement.get("issue_count", 0) or 0),
            "groundedness_score": groundedness.get("score"),
            "completeness_score": completeness.get("score"),
            "clarity_score": clarity.get("score"),
        },
```

- [ ] **Step 2: Update `/demo` copy so it describes a structured judge, not a vague supplementary flag**

```html
<div id="latest-task-judgement-meta" class="provider-meta">Latest structured LLM-as-Judge summary will appear here.</div>
```

```javascript
latestTaskJudgementMetaEl.textContent = latestTask
  ? [`task_id: ${latestTask.task_id}`, `judge_status: ${latestTaskJudgement.judge_status || "none"}`].join(" | ")
  : "No persisted task found yet.";
```

- [ ] **Step 3: Run focused runtime-evidence tests**

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
    "tests/test_project_status_api.py",
    "tests/test_demo_page.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- project-status judge summary tests pass
- demo page tests pass

- [ ] **Step 4: Commit the runtime-evidence milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/project_status.py backend/app/api/demo.py backend/tests/test_project_status_api.py backend/tests/test_demo_page.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: align llm judge runtime evidence surfaces"
```

### Task 5: Align delivery docs and run full backend verification

**Files:**
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Update doc wording to one stable story**

```markdown
- The project now exposes a structured `LLM-as-Judge` summary across `/api/eval/run`, `GET /api/project-status`, `/demo`, and fixed eval results.
- Judge inputs are packed from the real task execution path, including report output, tool evidence, retrieval context, and process summary.
- Rule-based evaluation remains the deterministic baseline; judge output is complementary and explicitly degradable.
```

- [ ] **Step 2: Re-run focused doc tests**

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
    "tests/test_delivery_docs.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- delivery doc tests pass

- [ ] **Step 3: Run the full backend suite**

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
- no regression in retrieval, memory, sandbox, or provider runtime evidence

- [ ] **Step 4: Commit the doc-alignment milestone**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align llm judge closure evidence"
```

- [ ] **Step 5: Stop and report the real verification output**

Report:

- exact focused-test summaries
- exact full-suite summary
- whether the judge remained clearly separated from deterministic rule scoring
