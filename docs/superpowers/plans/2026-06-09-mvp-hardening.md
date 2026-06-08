# MVP Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current analysis-task MVP so it truthfully covers the required demo question families, records degradations, and persists a real rule-based `eval_result`.

**Architecture:** Keep the existing synchronous FastAPI + SQLite loop intact. Expand rule-based field matching into executable metric specs, let the runner handle one or multiple tool calls with explicit failure events, then score the final task state through a deterministic `RuleScorer` exposed by a small eval API.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLite, DuckDB, pytest

---

### Task 1: Add tests for multi-question coverage and degraded failures

**Files:**
- Modify: `backend/tests/test_match_fields.py`
- Modify: `backend/tests/test_analysis_runner.py`
- Modify: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Write failing tests for channel multi-metric matching**

- [ ] **Step 2: Run the targeted tests and verify they fail for the expected reason**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_match_fields.py tests/test_analysis_runner.py tests/test_analysis_api.py -v`

Expected:
- channel question assertions fail because only one metric is supported
- degraded failure assertions fail because the runner does not emit explicit failure state yet

- [ ] **Step 3: Commit test-only changes after RED if helpful**

```bash
git add backend/tests/test_match_fields.py backend/tests/test_analysis_runner.py backend/tests/test_analysis_api.py
git commit -m "test: define mvp hardening behavior"
```

### Task 2: Implement executable match specs and runner hardening

**Files:**
- Modify: `backend/app/tools/match_fields.py`
- Modify: `backend/app/tools/chart_tool.py`
- Modify: `backend/app/tools/report_tool.py`
- Modify: `backend/app/tools/duckdb_tools.py`
- Modify: `backend/app/services/analysis_runner.py`
- Modify: `backend/app/storage/analysis_store.py`

- [ ] **Step 1: Implement match spec output that can describe one or multiple metrics**

- [ ] **Step 2: Harden tool/report/chart behavior for empty results and degradations**

- [ ] **Step 3: Update the runner to execute multiple tool requests, persist findings, and emit failure/degradation events**

- [ ] **Step 4: Re-run the targeted tests and verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_match_fields.py tests/test_analysis_runner.py tests/test_analysis_api.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/tools/match_fields.py backend/app/tools/chart_tool.py backend/app/tools/report_tool.py backend/app/tools/duckdb_tools.py backend/app/services/analysis_runner.py backend/app/storage/analysis_store.py
git commit -m "feat: harden analysis runner for mvp scenarios"
```

### Task 3: Add rule scorer and eval API

**Files:**
- Create: `backend/app/eval/rule_scorer.py`
- Create: `backend/app/api/eval.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/schemas/analysis_schema.py`
- Create: `backend/tests/test_rule_scorer.py`
- Modify: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Write failing tests for rule scoring and eval endpoint**

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_rule_scorer.py tests/test_analysis_api.py -v`

Expected:
- `ModuleNotFoundError` or endpoint 404 before implementation

- [ ] **Step 3: Implement deterministic scoring and persistence back into task state**

- [ ] **Step 4: Re-run the focused tests and verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_rule_scorer.py tests/test_analysis_api.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/eval/rule_scorer.py backend/app/api/eval.py backend/app/main.py backend/app/schemas/analysis_schema.py backend/tests/test_rule_scorer.py backend/tests/test_analysis_api.py
git commit -m "feat: add rule-based task evaluation"
```

### Task 4: Update docs and verify the whole backend loop

**Files:**
- Modify: `backend/README.md`

- [ ] **Step 1: Update README with current truthful MVP scope and eval usage**

- [ ] **Step 2: Run the full backend test suite**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest -v`

Expected: PASS

- [ ] **Step 3: Run one manual end-to-end API flow against the sample CSV**

Expected:
- category, region, and channel families are demonstrable
- completed task includes `eval_result`
- degraded failures show up in `errors` and `events`

- [ ] **Step 4: Commit docs if changed**

```bash
git add backend/README.md
git commit -m "docs: document hardened mvp backend"
```
