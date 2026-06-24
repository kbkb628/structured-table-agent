# LangGraph Runner Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current handwritten synchronous analysis-task orchestration with a minimal LangGraph state flow while preserving the same external API behavior, task-state shape, and failure semantics.

**Architecture:** Add a small `agent/` module that defines typed state helpers, node functions, and a linear LangGraph graph. Reuse the existing tool, storage, and evaluation logic inside nodes so `/api/analysis/{task_id}/run` changes orchestration style without changing truthful MVP capability boundaries.

**Tech Stack:** Python 3.12, FastAPI, LangGraph, Pydantic, SQLite, DuckDB, pytest

---

### Task 1: Add failing tests that lock graph-backed behavior

**Files:**
- Modify: `backend/tests/test_analysis_runner.py`
- Modify: `backend/tests/test_analysis_api.py`
- Create: `backend/tests/test_agent_graph.py`

- [ ] **Step 1: Write failing graph tests for successful region execution**

- [ ] **Step 2: Write failing graph tests for failure propagation**

- [ ] **Step 3: Run focused tests and verify they fail because `agent/` modules do not exist yet**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_agent_graph.py tests/test_analysis_runner.py tests/test_analysis_api.py -v`

Expected:
- missing-module errors for `app.agent`
- or failing assertions because `/run` is not graph-backed yet

- [ ] **Step 4: Commit RED tests if useful**

```bash
git add backend/tests/test_agent_graph.py backend/tests/test_analysis_runner.py backend/tests/test_analysis_api.py
git commit -m "test: define langgraph runner behavior"
```

### Task 2: Add LangGraph dependency and agent module skeleton

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/app/agent/__init__.py`
- Create: `backend/app/agent/state.py`
- Create: `backend/app/agent/nodes.py`
- Create: `backend/app/agent/graph.py`

- [ ] **Step 1: Add the minimal LangGraph dependency**

- [ ] **Step 2: Define state typing helpers that preserve existing top-level keys**

- [ ] **Step 3: Add graph skeleton and node stubs**

- [ ] **Step 4: Re-run focused tests and verify they now fail on node behavior rather than missing modules**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_agent_graph.py -v`

Expected:
- graph imports succeed
- behavior tests still fail until node logic is implemented

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app/agent
git commit -m "feat: scaffold langgraph agent module"
```

### Task 3: Move orchestration logic into LangGraph nodes

**Files:**
- Modify: `backend/app/agent/nodes.py`
- Modify: `backend/app/agent/graph.py`
- Modify: `backend/app/services/analysis_runner.py`
- Test: `backend/tests/test_agent_graph.py`
- Test: `backend/tests/test_analysis_runner.py`

- [ ] **Step 1: Implement node logic by reusing existing tool, event, and persistence helpers**

- [ ] **Step 2: Build the linear state graph from load -> match -> execute -> chart -> report -> evaluate**

- [ ] **Step 3: Make `run_analysis_task` delegate to the LangGraph runner**

- [ ] **Step 4: Re-run runner and graph tests and verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_agent_graph.py tests/test_analysis_runner.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agent/nodes.py backend/app/agent/graph.py backend/app/services/analysis_runner.py backend/tests/test_agent_graph.py backend/tests/test_analysis_runner.py
git commit -m "feat: migrate analysis runner to langgraph"
```

### Task 4: Verify API compatibility and update docs

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`
- Test: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Re-run analysis API tests to verify `/run` still behaves the same**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_analysis_api.py -v`

Expected: PASS

- [ ] **Step 2: Update docs to state that current orchestration is now LangGraph-based while capability boundaries remain unchanged**

- [ ] **Step 3: Run the full backend test suite**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest -v`

Expected: PASS

- [ ] **Step 4: Run one real API flow and confirm completed and failed scenarios still look correct**

- [ ] **Step 5: Commit docs if changed**

```bash
git add README.md backend/README.md
git commit -m "docs: document langgraph runner migration"
```
