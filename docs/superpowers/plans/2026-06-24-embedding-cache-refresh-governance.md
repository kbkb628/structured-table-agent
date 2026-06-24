# Embedding Cache Refresh Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real backend governance path that can refresh missing, stale, or all knowledge-item embeddings on demand while preserving the existing retrieval flow and existing cache runtime summary.

**Architecture:** Extend the current SQLite-backed embedding cache with one store-level refresh function that scans the JSONL knowledge base, reuses the existing embedding client, and persists refreshed rows through the existing upsert path. Expose that function through one narrow FastAPI endpoint under `/api/rag/embedding-cache/refresh`, keep the current lazy retrieval repair behavior untouched, and prove the behavior with focused store and API tests plus delivery-doc alignment.

**Tech Stack:** FastAPI, Pydantic, SQLite, JSONL knowledge base, sentence-transformers integration, pytest

---

### Task 1: Freeze red tests for refresh-governance behavior

**Files:**
- Modify: `backend/tests/test_embedding_store.py`
- Create: `backend/tests/test_rag_embedding_cache_api.py`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add a failing store test for `missing` refresh**

```python
def test_refresh_embedding_cache_refreshes_missing_items_only(tmp_path: Path, monkeypatch):
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "refresh_missing_a",
                        "title": "Revenue",
                        "content": "sales amount definition",
                        "tags": ["metric"],
                        "related_fields": ["sales_amount"],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "id": "refresh_missing_b",
                        "title": "Region",
                        "content": "region dimension definition",
                        "tags": ["dimension"],
                        "related_fields": ["region"],
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "app.rag.embedding_store.encode_texts",
        lambda texts: [[float(index + 1), float(index + 2)] for index, _ in enumerate(texts)],
    )

    result = refresh_embedding_cache(mode="missing", knowledge_base_path=kb_path)

    assert result["mode"] == "missing"
    assert result["knowledge_item_count"] == 2
    assert result["refreshed_item_count"] == 2
    assert result["missing_refreshed_count"] == 2
    assert result["stale_refreshed_count"] == 0
    assert result["error_count"] == 0
    assert get_knowledge_embedding("refresh_missing_a") is not None
    assert get_knowledge_embedding("refresh_missing_b") is not None
```

- [ ] **Step 2: Add a failing store test for `stale` refresh**

```python
def test_refresh_embedding_cache_refreshes_stale_items_only(tmp_path: Path, monkeypatch):
    kb_path = tmp_path / "knowledge_base.jsonl"
    item_a = {
        "id": "refresh_stale_a",
        "title": "Fresh Item",
        "content": "fresh content",
        "tags": [],
        "related_fields": [],
    }
    item_b = {
        "id": "refresh_stale_b",
        "title": "Stale Item",
        "content": "stale content",
        "tags": [],
        "related_fields": [],
    }
    kb_path.write_text(
        "\n".join([json.dumps(item_a, ensure_ascii=False), json.dumps(item_b, ensure_ascii=False)]),
        encoding="utf-8",
    )

    fresh_hash = hashlib.sha256(
        json.dumps(
            {
                "title": item_a["title"],
                "content": item_a["content"],
                "tags": item_a["tags"],
                "related_fields": item_a["related_fields"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    upsert_knowledge_embedding(
        item_id=item_a["id"],
        content_hash=fresh_hash,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        embedding=[0.1, 0.2],
    )
    upsert_knowledge_embedding(
        item_id=item_b["id"],
        content_hash="stale_hash",
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        embedding=[0.3, 0.4],
    )

    monkeypatch.setattr(
        "app.rag.embedding_store.encode_texts",
        lambda texts: [[9.0, 10.0] for _ in texts],
    )

    result = refresh_embedding_cache(mode="stale", knowledge_base_path=kb_path)

    stale_record = get_knowledge_embedding("refresh_stale_b")
    assert result["mode"] == "stale"
    assert result["refreshed_item_count"] == 1
    assert result["missing_refreshed_count"] == 0
    assert result["stale_refreshed_count"] == 1
    assert stale_record is not None
    assert json.loads(stale_record["embedding_json"]) == [9.0, 10.0]
```

- [ ] **Step 3: Add a failing API contract test**

```python
def test_refresh_embedding_cache_api_returns_runtime_summary(monkeypatch):
    monkeypatch.setattr(
        "app.api.rag_embedding_cache.refresh_embedding_cache",
        lambda mode: {
            "mode": mode,
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "knowledge_item_count": 12,
            "scanned_item_count": 12,
            "refreshed_item_count": 3,
            "missing_refreshed_count": 2,
            "stale_refreshed_count": 1,
            "error_count": 0,
            "elapsed_ms": 184,
        },
    )

    client = TestClient(app)
    response = client.post("/api/rag/embedding-cache/refresh", json={"mode": "missing"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "missing"
    assert payload["refreshed_item_count"] == 3
    assert payload["missing_refreshed_count"] == 2
    assert payload["stale_refreshed_count"] == 1
```

- [ ] **Step 4: Add a failing invalid-mode API test**

```python
def test_refresh_embedding_cache_api_rejects_invalid_mode():
    client = TestClient(app)
    response = client.post("/api/rag/embedding-cache/refresh", json={"mode": "invalid"})

    assert response.status_code == 422
```

- [ ] **Step 5: Add failing delivery-doc expectations**

```python
def test_embedding_cache_refresh_governance_is_documented():
    backend_readme = Path("backend/README.md").read_text(encoding="utf-8")
    assert "/api/rag/embedding-cache/refresh" in backend_readme
    assert "missing|stale|all" in backend_readme
```

- [ ] **Step 6: Run focused tests to verify they fail**

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
    "tests/test_rag_embedding_cache_api.py",
    "tests/test_delivery_docs.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- store tests fail because `refresh_embedding_cache()` does not exist yet
- API tests fail because the router is not implemented or registered yet
- doc test fails because the refresh endpoint is not documented yet

- [ ] **Step 7: Commit the red tests**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/tests/test_embedding_store.py backend/tests/test_rag_embedding_cache_api.py backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "test: freeze embedding cache refresh governance"
```

### Task 2: Implement the store-layer refresh function

**Files:**
- Modify: `backend/app/rag/embedding_store.py`

- [ ] **Step 1: Add refresh mode typing and reusable refresh-target logic**

```python
RefreshMode = Literal["missing", "stale", "all"]


def _needs_refresh(item: dict, cached: tuple[str, str] | None, mode: RefreshMode) -> tuple[bool, str | None]:
    if mode == "all":
        if cached is None:
            return True, "missing"
        return True, "stale" if cached[0] != _knowledge_item_content_hash(item) or cached[1] != config.RAG_BI_ENCODER_MODEL else "fresh"

    if cached is None:
        return (mode == "missing"), "missing"

    cached_hash, cached_model_name = cached
    expected_hash = _knowledge_item_content_hash(item)
    is_stale = cached_hash != expected_hash or cached_model_name != config.RAG_BI_ENCODER_MODEL
    if mode == "stale" and is_stale:
        return True, "stale"
    return False, "fresh" if not is_stale else "stale"
```

- [ ] **Step 2: Add the real refresh function**

```python
def refresh_embedding_cache(
    mode: RefreshMode,
    knowledge_base_path: Path | None = None,
) -> dict:
    started = time.perf_counter()
    knowledge_items = load_knowledge_base(knowledge_base_path)
    item_ids = [item["id"] for item in knowledge_items if item.get("id")]
    cached_rows = _load_cached_embedding_rows(item_ids)

    refreshed_item_count = 0
    missing_refreshed_count = 0
    stale_refreshed_count = 0

    for item in knowledge_items:
        item_id = item.get("id")
        if not item_id:
            continue
        should_refresh, reason = _needs_refresh(item, cached_rows.get(item_id), mode)
        if not should_refresh:
            continue
        embedding = encode_texts([_build_embedding_text(item)])[0]
        upsert_knowledge_embedding(
            item_id=item_id,
            content_hash=_knowledge_item_content_hash(item),
            model_name=config.RAG_BI_ENCODER_MODEL,
            embedding=embedding,
        )
        refreshed_item_count += 1
        if reason == "missing":
            missing_refreshed_count += 1
        elif reason == "stale":
            stale_refreshed_count += 1

    return {
        "mode": mode,
        "model_name": config.RAG_BI_ENCODER_MODEL,
        "knowledge_item_count": len(knowledge_items),
        "scanned_item_count": len(knowledge_items),
        "refreshed_item_count": refreshed_item_count,
        "missing_refreshed_count": missing_refreshed_count,
        "stale_refreshed_count": stale_refreshed_count,
        "error_count": 0,
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }
```

- [ ] **Step 3: Reuse a small helper for bulk cache-row lookup**

```python
def _load_cached_embedding_rows(item_ids: list[str]) -> dict[str, tuple[str, str]]:
    if not item_ids:
        return {}
    placeholders = ", ".join("?" for _ in item_ids)
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT item_id, content_hash, model_name
            FROM knowledge_embeddings
            WHERE item_id IN ({placeholders})
            """,
            tuple(item_ids),
        ).fetchall()
    return {row[0]: (row[1], row[2]) for row in rows}
```

- [ ] **Step 4: Run focused store tests to verify green**

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
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- all embedding-store tests pass, including the new refresh-governance cases

- [ ] **Step 5: Commit the store implementation**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/rag/embedding_store.py backend/tests/test_embedding_store.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: add embedding cache refresh store logic"
```

### Task 3: Expose the refresh API and register the router

**Files:**
- Create: `backend/app/api/rag_embedding_cache.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add request and response schemas in the API module**

```python
class EmbeddingCacheRefreshRequest(BaseModel):
    mode: Literal["missing", "stale", "all"]


class EmbeddingCacheRefreshResponse(BaseModel):
    mode: Literal["missing", "stale", "all"]
    model_name: str
    knowledge_item_count: int
    scanned_item_count: int
    refreshed_item_count: int
    missing_refreshed_count: int
    stale_refreshed_count: int
    error_count: int
    elapsed_ms: int
```

- [ ] **Step 2: Implement the router**

```python
router = APIRouter(prefix="/api/rag/embedding-cache", tags=["rag"])


@router.post("/refresh", response_model=EmbeddingCacheRefreshResponse)
def refresh_embedding_cache_api(request: EmbeddingCacheRefreshRequest) -> EmbeddingCacheRefreshResponse:
    result = refresh_embedding_cache(mode=request.mode)
    return EmbeddingCacheRefreshResponse(**result)
```

- [ ] **Step 3: Register the router in the app**

```python
from app.api.rag_embedding_cache import router as rag_embedding_cache_router

...
app.include_router(rag_embedding_cache_router)
```

- [ ] **Step 4: Run focused API tests to verify green**

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
    "tests/test_rag_embedding_cache_api.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- refresh API tests pass
- invalid mode returns `422`

- [ ] **Step 5: Commit the API entrypoint**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/app/api/rag_embedding_cache.py backend/app/main.py backend/tests/test_rag_embedding_cache_api.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "feat: expose embedding cache refresh api"
```

### Task 4: Align docs and run full verification

**Files:**
- Modify: `backend/README.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Add truthful README wording for the new endpoint**

```markdown
The backend now provides `POST /api/rag/embedding-cache/refresh` for explicit
embedding-cache governance. Supported modes are `missing`, `stale`, and `all`.
The endpoint computes real embeddings through the current bi-encoder path and
returns refresh counters for the maintenance run. This is a local SQLite-backed
cache-management capability, not an external vector database service.
```

- [ ] **Step 2: Re-run the focused doc and compatibility tests**

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
    "tests/test_rag_embedding_cache_api.py",
    "tests/test_delivery_docs.py",
]))
'@ | & 'C:\Program Files\LibreOffice\program\python.exe'
$exitCode = $LASTEXITCODE
if (Test-Path '.pytest-tmp') { Remove-Item -Recurse -Force '.pytest-tmp' }
exit $exitCode
```

Expected:

- refresh-governance tests pass
- existing project-status runtime summary tests stay green
- delivery-doc assertions pass

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

- the full backend suite passes
- no existing embedding-cache runtime evidence regresses

- [ ] **Step 4: Commit docs and verification alignment**

```powershell
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' add backend/README.md backend/tests/test_delivery_docs.py
git -C 'E:\bgagent1\.worktrees\day1-mvp-backend' commit -m "docs: align embedding cache refresh governance"
```

- [ ] **Step 5: Stop and report the real verification output**

Report:

- exact focused-test result summaries
- exact full-suite result summary
- whether any existing runtime evidence or retrieval contract changed unexpectedly
