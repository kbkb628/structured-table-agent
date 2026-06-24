# Embedding Cache Runtime Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the real embedding retrieval layer more reviewable by surfacing cache freshness and coverage evidence for `knowledge_embeddings` through repository code, runtime status, tests, and delivery docs.

**Architecture:** Keep the current local embedding retrieval path and SQLite-backed `knowledge_embeddings` table unchanged as the storage source of truth. Add a small cache-summary layer that compares the current knowledge base against persisted embedding records, then expose a stable summary through `GET /api/project-status` and delivery materials without changing the existing retrieval contract.

**Tech Stack:** FastAPI, SQLite, JSONL knowledge base, pytest

---

### Task 1: Freeze failing tests for embedding cache runtime evidence

**Files:**
- Modify: `backend/tests/test_embedding_store.py`
- Modify: `backend/tests/test_project_status_api.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add a failing embedding store summary test**

```python
def test_summarize_embedding_cache_reports_fresh_and_stale_records(tmp_path, monkeypatch):
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        "\n".join(
            [
                '{"id":"item_a","title":"A","content":"fresh","tags":[],"related_fields":[]}',
                '{"id":"item_b","title":"B","content":"stale","tags":[],"related_fields":[]}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.rag.embedding_store.KNOWLEDGE_BASE_PATH", kb_path)

    upsert_knowledge_embedding("item_a", content_hash_for_a, model_name, [0.1, 0.2])
    upsert_knowledge_embedding("item_b", "stale_hash", model_name, [0.2, 0.3])

    summary = summarize_embedding_cache(knowledge_base_path=kb_path)

    assert summary["knowledge_item_count"] == 2
    assert summary["cached_item_count"] == 2
    assert summary["fresh_item_count"] == 1
    assert summary["stale_item_count"] == 1
```

- [ ] **Step 2: Add a failing project-status runtime summary test**

```python
def test_get_project_status_surfaces_embedding_cache_summary(monkeypatch):
    monkeypatch.setattr(
        "app.api.project_status._embedding_cache_info",
        lambda: {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "knowledge_item_count": 12,
            "cached_item_count": 10,
            "fresh_item_count": 9,
            "stale_item_count": 1,
            "missing_item_count": 2,
            "cache_coverage_ratio": 0.8333,
        },
    )

    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    embedding_cache = response.json()["summary"]["embedding_cache"]
    assert embedding_cache["cached_item_count"] == 10
    assert embedding_cache["stale_item_count"] == 1
    assert embedding_cache["cache_coverage_ratio"] == 0.8333
```

- [ ] **Step 3: Add failing delivery-doc assertions**

```python
assert "embedding_cache" in project_status
assert "cache_coverage_ratio" in api_reference
assert "stale_item_count" in interview_guide
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
    "tests/test_embedding_store.py",
    "tests/test_project_status_api.py",
    "tests/test_delivery_docs.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- embedding store tests fail because cache summary API does not exist yet
- project-status tests fail because `summary.embedding_cache` is not exposed yet
- delivery-doc tests fail because docs do not mention the runtime cache fields yet

- [ ] **Step 5: Commit the red tests**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_embedding_store.py backend/tests/test_project_status_api.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze embedding cache runtime evidence"
```

### Task 2: Implement embedding cache summary extraction and runtime exposure

**Files:**
- Modify: `backend/app/rag/embedding_store.py`
- Modify: `backend/app/api/project_status.py`

- [ ] **Step 1: Add cache-summary helpers in the embedding store**

```python
def summarize_embedding_cache(knowledge_base_path: Path | None = None) -> dict:
    ...
    return {
        "model_name": config.RAG_BI_ENCODER_MODEL,
        "knowledge_item_count": ...,
        "cached_item_count": ...,
        "fresh_item_count": ...,
        "stale_item_count": ...,
        "missing_item_count": ...,
        "cache_coverage_ratio": ...,
    }
```

- [ ] **Step 2: Expose the summary through project status**

```python
def _embedding_cache_info() -> dict:
    return summarize_embedding_cache()

...
"embedding_cache": _embedding_cache_info(),
```

- [ ] **Step 3: Run focused tests to verify green**

Run the same focused command from Task 1.

Expected:

- focused embedding-store and project-status tests pass
- docs may still fail until Task 3 is completed

- [ ] **Step 4: Commit the runtime summary implementation**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/rag/embedding_store.py backend/app/api/project_status.py backend/tests/test_embedding_store.py backend/tests/test_project_status_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: expose embedding cache runtime summary"
```

### Task 3: Align delivery docs with embedding cache runtime evidence

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/API_REFERENCE.md`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/INTERVIEW_GUIDE.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add truthful runtime wording**

```markdown
`GET /api/project-status` now exposes `summary.embedding_cache` with
`knowledge_item_count`, `cached_item_count`, `fresh_item_count`,
`stale_item_count`, `missing_item_count`, and `cache_coverage_ratio`.
```

- [ ] **Step 2: Keep the wording inside the real capability boundary**

```markdown
This summary describes the current local embedding cache state for the staged
retrieval layer. It is runtime evidence for embedding persistence and freshness,
not a claim of distributed vector infrastructure.
```

- [ ] **Step 3: Re-run focused tests**

Run the same focused command from Task 1.

Expected:

- `tests/test_embedding_store.py` passes
- `tests/test_project_status_api.py` passes
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
- runtime delivery docs remain aligned

- [ ] **Step 5: Commit the documentation alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add README.md backend/README.md docs/API_REFERENCE.md docs/PROJECT_STATUS.md docs/INTERVIEW_GUIDE.md docs/RESUME_EVIDENCE_MAP.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align embedding cache runtime evidence"
```
