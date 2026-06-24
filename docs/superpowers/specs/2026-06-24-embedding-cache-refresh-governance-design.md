# Embedding Cache Refresh Governance Design

## Goal

Add a truthful, narrow governance capability for the real embedding retrieval layer so the repository can actively refresh stale or missing `knowledge_embeddings` records instead of only repairing them lazily during retrieval.

This design is intentionally small:

- keep the current JSONL knowledge base
- keep the current SQLite-backed `knowledge_embeddings` table
- keep the current retrieval contract and lazy repair behavior
- add one explicit refresh path for operational control and runtime evidence

The purpose is to strengthen the retrieval stack's engineering reality without drifting away from the current project phase or the development guide.

## Current Context

The current repository already has these real embedding-related behaviors:

- `backend/app/rag/embedding_client.py` loads and uses a real bi-encoder model
- `backend/app/rag/vector_retriever.py` computes embeddings for knowledge items when cache entries are missing or stale
- `backend/app/rag/embedding_store.py` persists cached embeddings into SQLite
- `backend/app/rag/embedding_store.py` already exposes `summarize_embedding_cache()`
- `GET /api/project-status` already exposes runtime cache summary fields:
  - `knowledge_item_count`
  - `cached_item_count`
  - `fresh_item_count`
  - `stale_item_count`
  - `missing_item_count`
  - `cache_coverage_ratio`

The remaining gap is governance:

- there is no explicit API or service entrypoint to refresh the cache on demand
- there is no way to rebuild missing records before the first retrieval request touches them
- there is no direct operational evidence for how many records were refreshed in a deliberate maintenance run

That gap matters because the resume-alignment roadmap now requires technologies to be backed by code, runtime evidence, and tests, not just by implicit behavior.

## Hard Requirements

This feature must follow these rules:

1. Do not replace or redesign the existing retrieval path.
2. Do not broaden scope into rerank, BM25, judge, memory, or sandbox work.
3. Do not add fake refresh behavior. Every refresh must compute real embeddings through the existing embedding client.
4. Preserve the development guide boundary that retrieval augments business semantics and does not replace deterministic tabular computation.
5. Keep the implementation small enough to fit the current staged delivery approach.
6. Expose operational results through a truthful runtime contract.

## Non-Goals

This design does not include:

- a background scheduler
- asynchronous queue processing
- distributed vector infrastructure
- a new vector database
- automatic refresh-on-write for knowledge base edits
- extra demo UX beyond what is needed for runtime evidence

Those may become reasonable later, but they are unnecessary for the current gap.

## Problem Statement

Today the cache is only repaired when retrieval happens. That is correct but incomplete:

- the first retrieval after knowledge-base changes pays the refresh cost
- there is no operator-controlled warm-up or rebuild path
- runtime introspection can show cache health, but not an explicit governance action

The repository needs a small, reviewable maintenance path that can:

- refresh only missing records
- refresh only stale records
- rebuild the whole cache when needed

without disturbing the main retrieval flow.

## Approaches Considered

### Approach A: Script-Only Refresh

Add a repository script that scans the knowledge base and rebuilds records locally.

Pros:

- simple to implement
- useful for local maintenance

Cons:

- weaker alignment with the existing backend-service architecture
- runtime evidence is less visible than an API path
- harder to surface in `/api/project-status` and delivery materials

### Approach B: API-Only Refresh

Add a backend API entrypoint that triggers a synchronous refresh and returns a structured result.

Pros:

- matches the current FastAPI service shape
- provides direct runtime evidence
- easy to test at both service and API layers
- minimal scope

Cons:

- less convenient than a script for offline maintenance
- refresh latency is paid by the caller

### Approach C: API Plus Script

Add both the API and a wrapper script.

Pros:

- best operator ergonomics
- script can call the API and support demos

Cons:

- larger scope than necessary for the current gap
- duplicates interfaces too early

## Recommendation

Use Approach B now.

It is the smallest truthful implementation that fits the current repository. It strengthens the service boundary, creates explicit runtime evidence, and avoids unnecessary interface sprawl. A script wrapper can be added later if there is a real demonstration need.

## Proposed Design

### 1. Store-Layer Refresh Function

Add a new store-level function in `backend/app/rag/embedding_store.py` that:

- loads the current knowledge base
- computes the expected content hash for each item
- checks existing cached rows
- decides whether each item needs refresh according to the requested mode
- computes real embeddings for refresh targets using the existing embedding client
- persists refreshed records through the existing `upsert_knowledge_embedding()` path

This function should be the single source of truth for refresh logic.

#### Refresh Modes

Support exactly these three modes:

- `missing`: refresh only items without a cache record
- `stale`: refresh only items whose content hash or model name does not match the current expectation
- `all`: refresh every valid knowledge item

No broader filtering is needed now.

#### Returned Result

The refresh function should return a structured summary with at least:

- `mode`
- `model_name`
- `knowledge_item_count`
- `scanned_item_count`
- `refreshed_item_count`
- `missing_refreshed_count`
- `stale_refreshed_count`
- `error_count`
- `elapsed_ms`

This result is intentionally operational rather than analytical. It describes what the maintenance run actually did.

### 2. API Entry Point

Add a dedicated refresh endpoint under the backend API.

Recommended shape:

- `POST /api/rag/embedding-cache/refresh`

Request body:

```json
{
  "mode": "missing"
}
```

Response body:

```json
{
  "mode": "missing",
  "model_name": "sentence-transformers/all-MiniLM-L6-v2",
  "knowledge_item_count": 12,
  "scanned_item_count": 12,
  "refreshed_item_count": 2,
  "missing_refreshed_count": 2,
  "stale_refreshed_count": 0,
  "error_count": 0,
  "elapsed_ms": 184
}
```

This endpoint should stay synchronous for now. That keeps the implementation obvious and avoids inventing a task model for a very small maintenance action.

### 3. Runtime Evidence Boundary

This feature should not overload `GET /api/project-status` with mutable refresh-job history yet.

The current cache summary already tells us the present cache state. The new refresh API should provide action-level evidence for a single maintenance run. That is enough for the current phase.

Therefore:

- keep `summary.embedding_cache` as the steady-state view
- use the new refresh API response as the per-run evidence
- do not add persistent `last_refresh_*` fields unless runtime review shows a real need later

This keeps the scope narrow and avoids turning a simple governance feature into a monitoring subsystem.

### 4. Error Handling

The refresh path must be explicit about failures.

Expected behaviors:

- invalid mode returns a validation error through FastAPI or schema validation
- malformed knowledge items should not silently succeed
- embedding provider failures should be surfaced as request failure rather than fabricated partial success

For the first implementation, fail-fast is acceptable and preferable to fake resilience. The repository already has lazy per-item repair in retrieval, so this explicit maintenance path does not need complex retry orchestration yet.

### 5. Compatibility With Existing Retrieval

The new refresh path must not change:

- `retrieve_vector_candidates()`
- cache lookup semantics during retrieval
- the SQLite schema for `knowledge_embeddings`
- the current `summarize_embedding_cache()` response contract

The existing lazy repair path remains valuable because:

- it preserves correctness when explicit refresh was not run
- it keeps retrieval self-healing

The new governance feature complements that behavior; it does not replace it.

## Module Impact

### Files To Modify

- `backend/app/rag/embedding_store.py`
- `backend/app/api/project_status.py` only if compatibility or cross-linking is needed
- a new API module under `backend/app/api/` for the refresh endpoint
- targeted tests under `backend/tests/`

### Files Likely To Add

- `backend/app/api/rag_embedding_cache.py` or equivalent
- one dedicated API test file for refresh behavior

### Files To Keep Stable

- `backend/app/rag/vector_retriever.py`
- `backend/app/rag/embedding_client.py`
- `backend/app/rag/knowledge_loader.py`

## Testing Strategy

The feature should be delivered through TDD with three evidence layers.

### Store Tests

Add focused tests proving that:

- `missing` refreshes only uncached items
- `stale` refreshes only outdated items
- `all` refreshes the full knowledge base

Tests should verify persisted cache rows after the refresh, not just returned counters.

### API Tests

Add focused API tests proving that:

- the endpoint accepts valid modes
- the returned counters match the maintenance action
- the endpoint exposes the current model name and elapsed time

### Compatibility Tests

Keep existing cache summary tests green so the earlier runtime-evidence checkpoint remains truthful.

## Documentation Impact

After implementation, the repository should update only the materials that actually need to mention the new capability, for example:

- `backend/README.md`
- any runtime or interview evidence doc that describes the retrieval stack

The wording must stay precise:

- the repository supports explicit embedding-cache refresh governance
- the cache is still local SQLite-backed persistence
- this is not a claim of external vector database infrastructure

## Acceptance Criteria

This feature is complete only when all of the following are true:

1. There is a real backend endpoint to refresh the embedding cache.
2. The endpoint supports `missing`, `stale`, and `all`.
3. The refresh path computes real embeddings through the existing embedding client.
4. The refresh result exposes truthful operational counters.
5. Focused store and API tests pass.
6. Existing `summary.embedding_cache` runtime evidence remains intact.
7. Documentation mentions the feature only within its real capability boundary.

## Risks And Mitigation

### Risk: Scope Expansion

The feature could drift into a larger retrieval refactor.

Mitigation:

- keep `vector_retriever.py` behavior unchanged
- add only one store function and one API endpoint

### Risk: Slow Tests Due To Real Model Calls

Embedding refresh can be expensive in tests.

Mitigation:

- patch `encode_texts()` in focused tests
- verify persistence and counters without depending on heavy model execution

### Risk: Overstated Runtime Claims

Documentation may accidentally describe this as a full cache-management system.

Mitigation:

- keep wording limited to explicit manual refresh governance
- do not claim scheduling, background workers, or distributed infrastructure

## Success Condition

This design succeeds when the retrieval layer gains a small but real maintenance interface that closes the current governance gap, strengthens resume-tech truthfulness, and leaves the wider architecture unchanged.
