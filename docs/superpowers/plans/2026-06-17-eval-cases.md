# Fixed Eval Cases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fixed-case regression runner that executes the real MVP analysis loop against a small predefined case set and returns a compact pass/fail summary.

**Architecture:** Build a small `eval_cases` module that defines supported cases, executes the real task creation and LangGraph-backed run flow against the sample CSV, and evaluates each case against stable threshold assertions. Keep execution local, synchronous, and grounded in the existing backend components.

**Tech Stack:** Python 3.12, FastAPI, SQLite, pytest

---

### Task 1: Add failing tests for fixed-case regression behavior

**Files:**
- Create: `backend/tests/test_eval_cases.py`

- [ ] **Step 1: Write a failing test for loading the fixed case set**

- [ ] **Step 2: Write a failing test for running the regression summary**

- [ ] **Step 3: Run the focused tests and verify they fail because `eval_cases.py` does not exist yet**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_eval_cases.py -v`

Expected:
- missing-module error for `app.eval.eval_cases`

- [ ] **Step 4: Commit RED tests if useful**

```bash
git add backend/tests/test_eval_cases.py
git commit -m "test: define fixed eval case behavior"
```

### Task 2: Implement fixed case definitions and execution helpers

**Files:**
- Create: `backend/app/eval/eval_cases.py`
- Modify: `backend/app/eval/__init__.py`
- Test: `backend/tests/test_eval_cases.py`

- [ ] **Step 1: Define the fixed case list for category, region, and channel scenarios**

- [ ] **Step 2: Implement helpers to register the sample CSV, create tasks, run analysis, and collect assertions**

- [ ] **Step 3: Return a compact summary with total counts, pass rate, and per-case details**

- [ ] **Step 4: Re-run focused tests and verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_eval_cases.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/eval/eval_cases.py backend/app/eval/__init__.py backend/tests/test_eval_cases.py
git commit -m "feat: add fixed eval cases runner"
```

### Task 3: Expose or document a simple execution path and verify end to end

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`

- [ ] **Step 1: Document how to run the fixed-case regression**

- [ ] **Step 2: Run the full backend test suite**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest -v`

Expected: PASS

- [ ] **Step 3: Run one real regression execution locally and confirm the three supported cases pass**

- [ ] **Step 4: Commit docs if changed**

```bash
git add README.md backend/README.md
git commit -m "docs: document fixed eval cases"
```
