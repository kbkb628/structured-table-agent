# MockLLM And Lightweight RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real local JSONL keyword retriever and a replaceable `MockLLMClient` so `business_context`, `analysis_goal`, and `analysis_plan` are truthfully populated without changing the current synchronous runner architecture.

**Architecture:** Keep the existing FastAPI + SQLite + synchronous task flow. Add a small `rag/` module for keyword retrieval and an `llm/` abstraction layer for deterministic goal/plan generation, then wire both into `POST /api/analysis/start` and persist the outputs in task state and events.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLite, pytest, JSONL

---

### Task 1: Add failing tests for lightweight RAG and MockLLM behavior

**Files:**
- Create: `backend/tests/test_keyword_retriever.py`
- Create: `backend/tests/test_mock_llm.py`
- Modify: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Write failing retriever tests for category and region recall**

- [ ] **Step 2: Write failing MockLLM tests for goal and plan generation**

- [ ] **Step 3: Extend analysis API tests to require non-empty `business_context` and `rag_retrieved` events**

- [ ] **Step 4: Run the focused tests and verify they fail**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_keyword_retriever.py tests/test_mock_llm.py tests/test_analysis_api.py -v`

Expected:
- missing-module errors for `app.rag` and `app.llm`
- analysis API assertions fail because `business_context` is still empty and `rag_retrieved` is not emitted

- [ ] **Step 5: Commit RED tests if useful**

```bash
git add backend/tests/test_keyword_retriever.py backend/tests/test_mock_llm.py backend/tests/test_analysis_api.py
git commit -m "test: define mock llm and rag behavior"
```

### Task 2: Implement JSONL knowledge loading and keyword retrieval

**Files:**
- Create: `backend/app/rag/knowledge_base.jsonl`
- Create: `backend/app/rag/knowledge_loader.py`
- Create: `backend/app/rag/keyword_retriever.py`
- Create: `backend/app/rag/__init__.py`
- Test: `backend/tests/test_keyword_retriever.py`

- [ ] **Step 1: Add a minimal knowledge base with sales metric, category, region, channel, and TopN semantics**

- [ ] **Step 2: Implement JSONL loading with graceful empty-result behavior**

- [ ] **Step 3: Implement deterministic keyword scoring using question terms plus file-profile columns**

- [ ] **Step 4: Re-run retriever tests and verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_keyword_retriever.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/rag backend/tests/test_keyword_retriever.py
git commit -m "feat: add lightweight keyword retriever"
```

### Task 3: Implement replaceable MockLLM layer

**Files:**
- Create: `backend/app/llm/base.py`
- Create: `backend/app/llm/mock_client.py`
- Create: `backend/app/llm/prompt_templates.py`
- Create: `backend/app/llm/__init__.py`
- Test: `backend/tests/test_mock_llm.py`

- [ ] **Step 1: Define the `LLMClient` interface for goal and plan generation**

- [ ] **Step 2: Implement `MockLLMClient` with deterministic category, region, channel, and fallback branches**

- [ ] **Step 3: Keep wording truthful and optionally incorporate retrieved business context titles**

- [ ] **Step 4: Re-run MockLLM tests and verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_mock_llm.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/llm backend/tests/test_mock_llm.py
git commit -m "feat: add replaceable mock llm client"
```

### Task 4: Wire RAG and MockLLM into analysis task creation

**Files:**
- Modify: `backend/app/api/analysis.py`
- Modify: `backend/app/schemas/analysis_schema.py`
- Modify: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Retrieve `business_context` during `/api/analysis/start`**

- [ ] **Step 2: Generate `analysis_goal` and `analysis_plan` through `MockLLMClient`**

- [ ] **Step 3: Persist `business_context` and emit `rag_retrieved` before `goal_understood` and `plan_generated`**

- [ ] **Step 4: Re-run focused API tests and verify they pass**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_analysis_api.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/analysis.py backend/app/schemas/analysis_schema.py backend/tests/test_analysis_api.py
git commit -m "feat: populate goal plan and business context"
```

### Task 5: Update docs and run full verification

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`

- [ ] **Step 1: Update README files to state that MVP now includes MockLLM and JSONL keyword retrieval**

- [ ] **Step 2: Run the full backend test suite**

Run: `cd backend && .\.venv\Scripts\python.exe -m pytest -v`

Expected: PASS

- [ ] **Step 3: Run the demo script or a manual API flow to verify `business_context` is returned and events include `rag_retrieved`**

Expected:
- `analysis/start` returns populated `business_context`
- persisted task state contains the same `business_context`
- event timeline includes `rag_retrieved`

- [ ] **Step 4: Commit docs if changed**

```bash
git add README.md backend/README.md
git commit -m "docs: document mock llm and lightweight rag"
```
