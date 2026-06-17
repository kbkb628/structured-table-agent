# Observability Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize MVP event and trace handling into `backend/app/observability` without changing external APIs or persistence shape.

**Architecture:** Add a thin semantic event layer over the existing SQLite event store. Keep `analysis_store` as raw persistence, move lifecycle event naming and helper behavior into `observability`, and update runtime modules to call that layer.

**Tech Stack:** Python 3.12, FastAPI, SQLite, LangGraph, pytest

---

### Task 1: Add observability helpers and constants

**Files:**
- Create: `backend/app/observability/trace_models.py`
- Create: `backend/app/observability/event_logger.py`
- Create: `backend/app/observability/__init__.py`

- [ ] **Step 1: Define shared event-name constants and required trace sets**

- [ ] **Step 2: Add helper functions for startup events, lifecycle events, event listing, and state hydration**

- [ ] **Step 3: Keep helpers as thin wrappers over `storage/analysis_store.py`**

### Task 2: Rewire runtime modules to use observability

**Files:**
- Modify: `backend/app/api/analysis.py`
- Modify: `backend/app/api/eval.py`
- Modify: `backend/app/agent/nodes.py`
- Modify: `backend/app/eval/eval_cases.py`
- Modify: `backend/app/eval/rule_scorer.py`

- [ ] **Step 1: Replace direct startup-event recording with `record_startup_events`**

- [ ] **Step 2: Replace direct event list hydration with `hydrate_state_events` / `list_analysis_events`**

- [ ] **Step 3: Replace lifecycle event writes in LangGraph nodes with semantic helper calls**

- [ ] **Step 4: Point `RuleScorer` required trace logic at shared constants**

### Task 3: Add regression tests and verify

**Files:**
- Create: `backend/tests/test_event_logger.py`
- Modify: `backend/README.md`

- [ ] **Step 1: Add focused tests for startup event ordering and state hydration**

- [ ] **Step 2: Briefly document that event timelines now flow through `backend/app/observability`**

- [ ] **Step 3: Run focused tests**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_event_logger.py tests/test_analysis_api.py tests/test_analysis_runner.py tests/test_eval_cases.py tests/test_rule_scorer.py -v`

Expected: PASS

- [ ] **Step 4: Run full backend test suite**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest -v`

Expected: PASS
