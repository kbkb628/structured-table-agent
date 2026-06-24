# RAG Retrieval Realization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the current local hybrid retriever into a truthful staged retrieval stack with explicit BM25 retrieval, embedding retrieval, and rerank, while preserving the current `retrieve_business_context()` integration surface used by task creation.

**Architecture:** Keep JSONL knowledge items as the source dataset, but split retrieval into explicit lexical, vector, and rerank stages. Store knowledge embeddings in SQLite, expose per-stage retrieval evidence in `business_context`, and surface the latest-stage evidence through `GET /api/project-status` without changing the core deterministic analysis tool chain.

**Tech Stack:** Python 3.12, FastAPI, SQLite, pytest, `rank-bm25`, `sentence-transformers`, existing project `SessionStore` / `project-status` delivery paths

---

### Task 1: Freeze retrieval-stage acceptance tests

**Files:**
- Modify: `backend/tests/test_keyword_retriever.py`
- Modify: `backend/tests/test_project_status_api.py`
- Create: `backend/tests/test_embedding_store.py`

- [ ] **Step 1: Extend keyword retriever tests to require staged retrieval evidence**

```python
from pathlib import Path

from app.rag.keyword_retriever import retrieve_business_context


def test_retrieve_business_context_includes_stage_evidence(tmp_path: Path):
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        "\n".join(
            [
                '{"id":"metric_sales_amount","type":"metric_definition","title":"Sales Amount","content":"Sales amount usually means the order transaction amount.","tags":["sales","metric"],"related_fields":["sales_amount"]}',
                '{"id":"dimension_region","type":"field_definition","title":"Region","content":"Region is used for geographic sales comparison.","tags":["region","dimension"],"related_fields":["region"]}',
            ]
        ),
        encoding="utf-8",
    )

    file_profile = {
        "columns": [
            {"name": "region", "type": "string"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    result = retrieve_business_context(
        question="analyse sales by region",
        file_profile=file_profile,
        knowledge_base_path=kb_path,
    )

    evidence = result["items"][0]["retrieval_evidence"]
    assert "bm25_rank" in evidence
    assert "bm25_score" in evidence
    assert "embedding_rank" in evidence
    assert "embedding_score" in evidence
    assert "rerank_score" in evidence
    assert "final_rank" in evidence
    assert set(evidence["retrieval_sources"]).issubset({"bm25", "embedding"})
```

- [ ] **Step 2: Extend project-status tests to require surfaced retrieval-stage evidence**

```python
def test_get_project_status_surfaces_embedding_and_rerank_evidence():
    task_id = "task_project_status_retrieval_evidence"
    state = {
        "task_id": task_id,
        "file_id": "file_project_status_retrieval_evidence",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {},
        "business_context": [
            {
                "id": "analysis_region_sales",
                "title": "Sales By Region",
                "related_fields": ["region", "sales_amount"],
                "score": 21.4,
                "score_breakdown": {
                    "keyword_score": 6.0,
                    "field_score": 4.0,
                    "phrase_score": 4.0,
                    "bm25_score": 3.4,
                },
                "retrieval_evidence": {
                    "bm25_rank": 1,
                    "bm25_score": 3.4,
                    "embedding_rank": 2,
                    "embedding_score": 0.8123,
                    "rerank_score": 0.9931,
                    "final_rank": 1,
                    "retrieval_sources": ["bm25", "embedding"],
                },
            }
        ],
        "analysis_plan": ["match fields"],
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
    context = response.json()["summary"]["latest_task"]["context"]
    assert context["top_business_context_embedding_score"] == 0.8123
    assert context["top_business_context_rerank_score"] == 0.9931
    assert context["top_business_context_retrieval_sources"] == ["bm25", "embedding"]
```

- [ ] **Step 3: Add a red test for SQLite embedding persistence**

```python
import json

from app.rag.embedding_store import get_knowledge_embedding, upsert_knowledge_embedding


def test_upsert_knowledge_embedding_round_trips_record():
    upsert_knowledge_embedding(
        item_id="analysis_region_sales",
        content_hash="hash_001",
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        embedding=[0.1, 0.2, 0.3],
    )

    record = get_knowledge_embedding("analysis_region_sales")

    assert record is not None
    assert record["item_id"] == "analysis_region_sales"
    assert record["content_hash"] == "hash_001"
    assert record["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert json.loads(record["embedding_json"]) == [0.1, 0.2, 0.3]
```

- [ ] **Step 4: Run focused tests to verify they fail**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_keyword_retriever.py tests/test_project_status_api.py tests/test_embedding_store.py -q
```

Expected:

- failures because `retrieval_evidence` fields do not exist yet
- import failure because `app.rag.embedding_store` does not exist yet
- failures because `project-status` does not surface embedding / rerank evidence

- [ ] **Step 5: Commit the red acceptance state**

```bash
git add backend/tests/test_keyword_retriever.py backend/tests/test_project_status_api.py backend/tests/test_embedding_store.py
git commit -m "test: freeze staged retrieval evidence behavior"
```

### Task 2: Add retrieval dependencies, config, and embedding persistence

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/storage/database.py`
- Create: `backend/app/rag/embedding_store.py`

- [ ] **Step 1: Add retrieval-stack dependencies**

```toml
[project]
dependencies = [
  "fastapi>=0.115.0,<1.0.0",
  "uvicorn>=0.30.0,<1.0.0",
  "python-multipart>=0.0.9,<1.0.0",
  "pandas>=2.2.0,<3.0.0",
  "duckdb>=1.0.0,<2.0.0",
  "openpyxl>=3.1.0,<4.0.0",
  "xlrd>=2.0.0,<3.0.0",
  "langgraph>=0.2.34,<1.0.0",
  "rank-bm25>=0.2.2,<1.0.0",
  "sentence-transformers>=5.0.0,<6.0.0",
  "numpy>=2.0.0,<3.0.0",
]
```

- [ ] **Step 2: Add explicit RAG model and stage configuration**

```python
RAG_BI_ENCODER_MODEL = get_env("RAG_BI_ENCODER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RAG_RERANK_MODEL = get_env("RAG_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RAG_BM25_TOP_K = int(get_env("RAG_BM25_TOP_K", "8") or "8")
RAG_VECTOR_TOP_K = int(get_env("RAG_VECTOR_TOP_K", "8") or "8")
RAG_FINAL_TOP_K = int(get_env("RAG_FINAL_TOP_K", "5") or "5")
RAG_ENABLE_VECTOR_RETRIEVAL = get_bool_env("RAG_ENABLE_VECTOR_RETRIEVAL", True)
RAG_ENABLE_RERANK = get_bool_env("RAG_ENABLE_RERANK", True)
```

- [ ] **Step 3: Add a SQLite table for knowledge embeddings**

```python
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_embeddings (
                item_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                model_name TEXT NOT NULL,
                vector_dim INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
```

- [ ] **Step 4: Create the embedding persistence helper**

```python
import json
from datetime import datetime, timezone

from app.storage.database import get_connection
from app.storage.database import init_db


def _ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_knowledge_embedding(item_id: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT item_id, content_hash, embedding_json, model_name, vector_dim, updated_at
            FROM knowledge_embeddings
            WHERE item_id = ?
            """,
            (item_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "item_id": row[0],
        "content_hash": row[1],
        "embedding_json": row[2],
        "model_name": row[3],
        "vector_dim": row[4],
        "updated_at": row[5],
    }


def upsert_knowledge_embedding(item_id: str, content_hash: str, model_name: str, embedding: list[float]) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO knowledge_embeddings (
                item_id, content_hash, embedding_json, model_name, vector_dim, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                content_hash = excluded.content_hash,
                embedding_json = excluded.embedding_json,
                model_name = excluded.model_name,
                vector_dim = excluded.vector_dim,
                updated_at = excluded.updated_at
            """,
            (
                item_id,
                content_hash,
                json.dumps(embedding, ensure_ascii=False),
                model_name,
                len(embedding),
                _ts(),
            ),
        )
```

- [ ] **Step 5: Run the focused storage test**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_embedding_store.py -q
```

Expected:

- `test_upsert_knowledge_embedding_round_trips_record` passes

- [ ] **Step 6: Commit the scaffolding milestone**

```bash
git add backend/pyproject.toml backend/app/core/config.py backend/app/storage/database.py backend/app/rag/embedding_store.py backend/tests/test_embedding_store.py
git commit -m "feat: add rag retrieval config and embedding store"
```

### Task 3: Replace BM25-style scoring with an explicit BM25 retrieval stage

**Files:**
- Create: `backend/app/rag/tokenization.py`
- Create: `backend/app/rag/bm25_retriever.py`
- Modify: `backend/app/rag/keyword_retriever.py`
- Modify: `backend/app/rag/__init__.py`
- Create: `backend/tests/test_bm25_retriever.py`

- [ ] **Step 1: Add shared tokenization helpers**

```python
import re


def tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if token]


def tokenize_set(text: str) -> set[str]:
    return set(tokenize(text))


def normalize_text(text: str) -> str:
    return " ".join(tokenize(text))
```

- [ ] **Step 2: Implement a true BM25 retriever backed by `rank-bm25`**

```python
from rank_bm25 import BM25Okapi

from app.rag.tokenization import tokenize


def build_bm25_corpus(knowledge_items: list[dict]) -> tuple[list[dict], list[list[str]], BM25Okapi]:
    tokenized_corpus: list[list[str]] = []
    for item in knowledge_items:
        document = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("content", "")),
                " ".join(item.get("tags", [])),
                " ".join(item.get("related_fields", [])),
            ]
        )
        tokenized_corpus.append(tokenize(document))
    return knowledge_items, tokenized_corpus, BM25Okapi(tokenized_corpus)


def retrieve_bm25_candidates(question: str, file_profile: dict, knowledge_items: list[dict], top_k: int) -> list[dict]:
    items, tokenized_corpus, bm25 = build_bm25_corpus(knowledge_items)
    query_tokens = tokenize(question) + [
        token
        for column in file_profile.get("columns", [])
        for token in tokenize(column["name"])
    ]
    scores = bm25.get_scores(query_tokens)
    ranked = sorted(
        [
            {
                "item": items[index],
                "bm25_rank": rank + 1,
                "bm25_score": round(float(score), 4),
            }
            for rank, (index, score) in enumerate(
                sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
            )
            if score > 0
        ],
        key=lambda row: row["bm25_score"],
        reverse=True,
    )
    return ranked[:top_k]
```

- [ ] **Step 3: Add a focused BM25 retriever test**

```python
from app.rag.bm25_retriever import retrieve_bm25_candidates


def test_retrieve_bm25_candidates_prefers_region_sales_template():
    knowledge_items = [
        {
            "id": "analysis_region_sales",
            "title": "Sales By Region",
            "content": "Compare regional sales totals.",
            "tags": ["sales", "region"],
            "related_fields": ["region", "sales_amount"],
        },
        {
            "id": "analysis_channel_orders",
            "title": "Channel Order Count Analysis",
            "content": "Compare channel order counts.",
            "tags": ["channel", "orders"],
            "related_fields": ["channel", "order_id"],
        },
    ]
    file_profile = {
        "columns": [
            {"name": "region", "type": "string"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    candidates = retrieve_bm25_candidates(
        question="analyse sales by region",
        file_profile=file_profile,
        knowledge_items=knowledge_items,
        top_k=3,
    )

    assert candidates[0]["item"]["id"] == "analysis_region_sales"
    assert candidates[0]["bm25_rank"] == 1
    assert candidates[0]["bm25_score"] > 0
```

- [ ] **Step 4: Keep `retrieve_business_context()` stable while delegating lexical ranking to the new stage**

```python
from app.core import config
from app.rag.bm25_retriever import retrieve_bm25_candidates
from app.rag.knowledge_loader import load_knowledge_base


def retrieve_business_context(question: str, file_profile: dict, knowledge_base_path: Path | None = None, limit: int = 3) -> dict:
    knowledge_items = load_knowledge_base(knowledge_base_path)
    if not knowledge_items:
        return {"items": []}

    bm25_candidates = retrieve_bm25_candidates(
        question=question,
        file_profile=file_profile,
        knowledge_items=knowledge_items,
        top_k=max(limit, config.RAG_BM25_TOP_K),
    )

    items = []
    for final_rank, candidate in enumerate(bm25_candidates[:limit], start=1):
        item = candidate["item"]
        items.append(
            {
                "id": item["id"],
                "type": item.get("type", ""),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "related_fields": item.get("related_fields", []),
                "score": round(candidate["bm25_score"], 2),
                "score_breakdown": {
                    "keyword_score": 0.0,
                    "field_score": 0.0,
                    "phrase_score": 0.0,
                    "bm25_score": candidate["bm25_score"],
                },
                "retrieval_evidence": {
                    "bm25_rank": candidate["bm25_rank"],
                    "bm25_score": candidate["bm25_score"],
                    "embedding_rank": None,
                    "embedding_score": None,
                    "rerank_score": None,
                    "final_rank": final_rank,
                    "retrieval_sources": ["bm25"],
                },
            }
        )
    return {"items": items}
```

- [ ] **Step 5: Run the BM25-focused tests**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_bm25_retriever.py tests/test_keyword_retriever.py -q
```

Expected:

- BM25-specific tests pass
- stage-evidence tests still fail on missing embedding and rerank fields or `None` values if assertions are stricter

- [ ] **Step 6: Commit the BM25 retrieval milestone**

```bash
git add backend/app/rag/tokenization.py backend/app/rag/bm25_retriever.py backend/app/rag/keyword_retriever.py backend/app/rag/__init__.py backend/tests/test_bm25_retriever.py backend/tests/test_keyword_retriever.py
git commit -m "feat: add explicit bm25 retrieval stage"
```

### Task 4: Add embedding retrieval with SQLite-backed embedding cache

**Files:**
- Create: `backend/app/rag/embedding_client.py`
- Create: `backend/app/rag/vector_retriever.py`
- Modify: `backend/app/rag/keyword_retriever.py`
- Create: `backend/tests/test_vector_retriever.py`

- [ ] **Step 1: Add a lazy embedding client wrapper**

```python
from sentence_transformers import SentenceTransformer

from app.core import config

_model = None


def get_bi_encoder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(config.RAG_BI_ENCODER_MODEL)
    return _model


def encode_texts(texts: list[str]) -> list[list[float]]:
    vectors = get_bi_encoder().encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]
```

- [ ] **Step 2: Implement vector retrieval with cached knowledge embeddings**

```python
import hashlib
import json

import numpy as np

from app.core import config
from app.rag.embedding_client import encode_texts
from app.rag.embedding_store import get_knowledge_embedding
from app.rag.embedding_store import upsert_knowledge_embedding


def _content_hash(item: dict) -> str:
    raw = json.dumps(
        {
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "tags": item.get("tags", []),
            "related_fields": item.get("related_fields", []),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def retrieve_vector_candidates(question: str, knowledge_items: list[dict], top_k: int) -> list[dict]:
    query_vector = np.array(encode_texts([question])[0], dtype=float)
    rows: list[dict] = []

    for item in knowledge_items:
        content_hash = _content_hash(item)
        cached = get_knowledge_embedding(item["id"])
        if cached and cached["content_hash"] == content_hash and cached["model_name"] == config.RAG_BI_ENCODER_MODEL:
            item_vector = np.array(json.loads(cached["embedding_json"]), dtype=float)
        else:
            text = " ".join(
                [
                    str(item.get("title", "")),
                    str(item.get("content", "")),
                    " ".join(item.get("tags", [])),
                    " ".join(item.get("related_fields", [])),
                ]
            )
            embedding = encode_texts([text])[0]
            upsert_knowledge_embedding(
                item_id=item["id"],
                content_hash=content_hash,
                model_name=config.RAG_BI_ENCODER_MODEL,
                embedding=embedding,
            )
            item_vector = np.array(embedding, dtype=float)

        score = float(np.dot(query_vector, item_vector))
        rows.append({"item": item, "embedding_score": round(score, 4)})

    ranked = sorted(rows, key=lambda row: row["embedding_score"], reverse=True)
    return [
        {**row, "embedding_rank": rank + 1}
        for rank, row in enumerate(ranked[:top_k])
    ]
```

- [ ] **Step 3: Add a vector retrieval test with a stub encoder**

```python
from app.rag.vector_retriever import retrieve_vector_candidates


def test_retrieve_vector_candidates_uses_embedding_similarity(monkeypatch):
    knowledge_items = [
        {"id": "analysis_region_sales", "title": "Sales By Region", "content": "Compare region sales.", "tags": [], "related_fields": []},
        {"id": "analysis_channel_orders", "title": "Channel Orders", "content": "Compare channel orders.", "tags": [], "related_fields": []},
    ]

    def fake_encode_texts(texts: list[str]) -> list[list[float]]:
        mapping = {
            "analyse sales by region": [1.0, 0.0],
            "Sales By Region Compare region sales.  ": [1.0, 0.0],
            "Channel Orders Compare channel orders.  ": [0.0, 1.0],
        }
        return [mapping[text] for text in texts]

    monkeypatch.setattr("app.rag.vector_retriever.encode_texts", fake_encode_texts)

    candidates = retrieve_vector_candidates(
        question="analyse sales by region",
        knowledge_items=knowledge_items,
        top_k=2,
    )

    assert candidates[0]["item"]["id"] == "analysis_region_sales"
    assert candidates[0]["embedding_rank"] == 1
    assert candidates[0]["embedding_score"] > candidates[1]["embedding_score"]
```

- [ ] **Step 4: Merge embedding candidates into `retrieve_business_context()`**

```python
    vector_candidates = retrieve_vector_candidates(
        question=question,
        knowledge_items=knowledge_items,
        top_k=max(limit, config.RAG_VECTOR_TOP_K),
    ) if config.RAG_ENABLE_VECTOR_RETRIEVAL else []

    merged: dict[str, dict] = {}
    for candidate in bm25_candidates:
        item_id = candidate["item"]["id"]
        merged[item_id] = {
            "item": candidate["item"],
            "bm25_rank": candidate["bm25_rank"],
            "bm25_score": candidate["bm25_score"],
            "embedding_rank": None,
            "embedding_score": None,
            "retrieval_sources": ["bm25"],
        }
    for candidate in vector_candidates:
        item_id = candidate["item"]["id"]
        current = merged.setdefault(
            item_id,
            {
                "item": candidate["item"],
                "bm25_rank": None,
                "bm25_score": 0.0,
                "embedding_rank": None,
                "embedding_score": None,
                "retrieval_sources": [],
            },
        )
        current["embedding_rank"] = candidate["embedding_rank"]
        current["embedding_score"] = candidate["embedding_score"]
        if "embedding" not in current["retrieval_sources"]:
            current["retrieval_sources"].append("embedding")
```

- [ ] **Step 5: Run the vector-focused tests**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_vector_retriever.py tests/test_keyword_retriever.py tests/test_embedding_store.py -q
```

Expected:

- vector and embedding-store tests pass
- keyword-retriever tests now show embedding evidence, but rerank-specific assertions still fail

- [ ] **Step 6: Commit the embedding retrieval milestone**

```bash
git add backend/app/rag/embedding_client.py backend/app/rag/vector_retriever.py backend/app/rag/keyword_retriever.py backend/tests/test_vector_retriever.py backend/tests/test_keyword_retriever.py backend/tests/test_embedding_store.py
git commit -m "feat: add embedding retrieval stage"
```

### Task 5: Add rerank and surface staged evidence through project runtime overview

**Files:**
- Create: `backend/app/rag/reranker.py`
- Modify: `backend/app/rag/keyword_retriever.py`
- Modify: `backend/app/api/project_status.py`
- Modify: `backend/tests/test_project_status_api.py`
- Create: `backend/tests/test_reranker.py`

- [ ] **Step 1: Add a CrossEncoder reranker wrapper**

```python
from sentence_transformers.cross_encoder import CrossEncoder

from app.core import config

_reranker = None


def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(config.RAG_RERANK_MODEL)
    return _reranker


def rerank_candidates(question: str, candidates: list[dict], top_k: int) -> list[dict]:
    if not candidates:
        return []

    pairs = [
        (
            question,
            " ".join(
                [
                    str(candidate["item"].get("title", "")),
                    str(candidate["item"].get("content", "")),
                ]
            ),
        )
        for candidate in candidates
    ]
    scores = get_reranker().predict(pairs)
    ranked = sorted(
        [
            {**candidate, "rerank_score": round(float(score), 4)}
            for candidate, score in zip(candidates, scores, strict=True)
        ],
        key=lambda row: row["rerank_score"],
        reverse=True,
    )
    return [
        {**row, "final_rank": rank + 1}
        for rank, row in enumerate(ranked[:top_k])
    ]
```

- [ ] **Step 2: Add a reranker unit test using a stub predictor**

```python
from app.rag.reranker import rerank_candidates


def test_rerank_candidates_reorders_merged_results(monkeypatch):
    candidates = [
        {"item": {"id": "analysis_region_sales", "title": "Sales By Region", "content": "Compare region sales."}},
        {"item": {"id": "analysis_channel_orders", "title": "Channel Orders", "content": "Compare channel orders."}},
    ]

    class StubReranker:
        def predict(self, pairs):
            return [0.97, 0.11]

    monkeypatch.setattr("app.rag.reranker.get_reranker", lambda: StubReranker())

    ranked = rerank_candidates(
        question="analyse sales by region",
        candidates=candidates,
        top_k=2,
    )

    assert ranked[0]["item"]["id"] == "analysis_region_sales"
    assert ranked[0]["rerank_score"] == 0.97
    assert ranked[0]["final_rank"] == 1
```

- [ ] **Step 3: Make `retrieve_business_context()` finalize results through rerank**

```python
    merged_candidates = list(merged.values())
    ranked_candidates = rerank_candidates(
        question=question,
        candidates=merged_candidates,
        top_k=limit,
    ) if config.RAG_ENABLE_RERANK else [
        {**candidate, "rerank_score": None, "final_rank": index + 1}
        for index, candidate in enumerate(merged_candidates[:limit])
    ]

    items = []
    for candidate in ranked_candidates:
        item = candidate["item"]
        items.append(
            {
                "id": item["id"],
                "type": item.get("type", ""),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "related_fields": item.get("related_fields", []),
                "score": round(candidate["rerank_score"] or candidate["bm25_score"] or candidate["embedding_score"] or 0.0, 2),
                "score_breakdown": {
                    "keyword_score": 0.0,
                    "field_score": 0.0,
                    "phrase_score": 0.0,
                    "bm25_score": candidate["bm25_score"] or 0.0,
                },
                "retrieval_evidence": {
                    "bm25_rank": candidate["bm25_rank"],
                    "bm25_score": candidate["bm25_score"],
                    "embedding_rank": candidate["embedding_rank"],
                    "embedding_score": candidate["embedding_score"],
                    "rerank_score": candidate["rerank_score"],
                    "final_rank": candidate["final_rank"],
                    "retrieval_sources": candidate["retrieval_sources"],
                },
            }
        )
```

- [ ] **Step 4: Surface embedding and rerank evidence through `project-status`**

```python
    top_business_context_retrieval = top_business_context.get("retrieval_evidence") or {}
    ...
        "context": {
            "business_context_count": len(business_context),
            "top_business_context_title": top_business_context.get("title"),
            "top_business_context_score": top_business_context.get("score"),
            "top_business_context_related_field_count": len(top_business_context.get("related_fields") or []),
            "top_business_context_has_score_breakdown": bool(top_business_context_score_breakdown),
            "top_business_context_keyword_score": top_business_context_score_breakdown.get("keyword_score"),
            "top_business_context_field_score": top_business_context_score_breakdown.get("field_score"),
            "top_business_context_phrase_score": top_business_context_score_breakdown.get("phrase_score"),
            "top_business_context_bm25_score": top_business_context_score_breakdown.get("bm25_score"),
            "top_business_context_embedding_score": top_business_context_retrieval.get("embedding_score"),
            "top_business_context_rerank_score": top_business_context_retrieval.get("rerank_score"),
            "top_business_context_retrieval_sources": top_business_context_retrieval.get("retrieval_sources") or [],
```

- [ ] **Step 5: Run end-to-end retrieval and project-status tests**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_keyword_retriever.py tests/test_reranker.py tests/test_project_status_api.py -q
```

Expected:

- staged retrieval evidence is now present end to end
- project-status tests pass with surfaced embedding and rerank evidence

- [ ] **Step 6: Commit the rerank and runtime-evidence milestone**

```bash
git add backend/app/rag/reranker.py backend/app/rag/keyword_retriever.py backend/app/api/project_status.py backend/tests/test_reranker.py backend/tests/test_keyword_retriever.py backend/tests/test_project_status_api.py
git commit -m "feat: add rerank stage and retrieval runtime evidence"
```

### Task 6: Update delivery documents and verify the full backend suite

**Files:**
- Modify: `README.md`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/RESUME_PROJECT_DESCRIPTION.md`
- Modify: `docs/RESUME_EVIDENCE_MAP.md`
- Modify: `backend/tests/test_delivery_docs.py`

- [ ] **Step 1: Update repository wording from lightweight-only retrieval to real staged retrieval**

```markdown
- RAG retrieval now includes:
  - explicit BM25 lexical retrieval
  - embedding-based vector retrieval
  - rerank over merged candidates
- `GET /api/project-status`, `/demo`, and `demo_mvp.ps1` surface the latest task's retrieval-stage evidence
```

- [ ] **Step 2: Tighten doc tests to require the upgraded wording**

```python
def test_resume_project_description_mentions_real_retrieval_stack():
    content = (Path(__file__).resolve().parents[2] / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(
        encoding="utf-8"
    )

    assert "embedding" in content
    assert "BM25" in content
    assert "rerank" in content
    assert "top_business_context_embedding_score" in content or "embedding_score" in content
    assert "top_business_context_rerank_score" in content or "rerank_score" in content
```

- [ ] **Step 3: Run the full backend suite**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest -q
```

Expected:

- full suite passes

- [ ] **Step 4: Run one live runtime-overview smoke**

Run:

```powershell
cd E:\bgagent1\.worktrees\day1-mvp-backend\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/project-status"
```

Expected:

- latest task context summary can include `top_business_context_embedding_score`
- latest task context summary can include `top_business_context_rerank_score`
- latest task context summary can include `top_business_context_retrieval_sources`

- [ ] **Step 5: Commit the phase completion**

```bash
git add README.md docs/PROJECT_STATUS.md docs/RESUME_PROJECT_DESCRIPTION.md docs/RESUME_EVIDENCE_MAP.md backend/tests/test_delivery_docs.py
git commit -m "docs: align retrieval stack evidence with resume wording"
```
