# MockLLM And Lightweight RAG Design

## Goal

Extend the current truthful MVP backend with the next guide-aligned layer:

- a replaceable `LLMClient` interface
- a local `MockLLMClient` implementation
- a real JSONL-backed keyword retriever for lightweight business-context recall
- real `business_context`, `analysis_goal`, and `analysis_plan` state population

This round keeps the existing synchronous runner and does not introduce LangGraph, Redis, async queues, or a real external model API.

## Scope

### In scope

- `backend/app/llm/base.py`
- `backend/app/llm/mock_client.py`
- `backend/app/llm/prompt_templates.py`
- `backend/app/rag/knowledge_base.jsonl`
- `backend/app/rag/knowledge_loader.py`
- `backend/app/rag/keyword_retriever.py`
- retrieval-backed `business_context`
- MockLLM-generated `analysis_goal`
- MockLLM-generated `analysis_plan`
- `rag_retrieved` event emission
- README updates that truthfully document the new boundary

### Out of scope

- LangGraph nodes and graph orchestration
- real LLM API integration
- embedding, BM25, rerank, or vector storage
- Redis state
- frontend changes

## Design Decisions

### 1. Keep orchestration synchronous and inject semantics into the existing loop

The current loop already has one truthful user path:

- upload file
- create analysis task
- run analysis
- inspect state and events

Instead of changing orchestration, this round enriches task creation and execution with business semantics.

- `POST /api/analysis/start` will retrieve `business_context`, then call `MockLLMClient` to generate `analysis_goal` and `analysis_plan`
- `POST /api/analysis/{task_id}/run` will reuse the persisted `business_context`

This keeps the API contract stable and avoids prematurely coupling the code to LangGraph.

### 2. Use a small local knowledge base with real keyword scoring

The retriever must be truthful but minimal.

- knowledge source: `knowledge_base.jsonl`
- each item contains `id`, `type`, `title`, `content`, `tags`, `related_fields`
- scoring uses question keywords plus file-profile column names
- top matched items are returned as `business_context`

This satisfies the guide's requirement that MVP RAG be lightweight but real.

### 3. Keep the MockLLM deterministic and replaceable

`LLMClient` should define:

- `generate_analysis_goal(question, file_profile, business_context)`
- `generate_analysis_plan(analysis_goal, file_profile, business_context)`

`MockLLMClient` should implement deterministic branching for:

- category sales questions
- region sales questions
- channel order-count and sales questions
- a grouped-analysis fallback

The output should clearly depend on question intent and optionally incorporate retrieved business context in wording, without pretending to be a real model.

### 4. Preserve frozen top-level task fields

The state schema remains stable. This round only changes what is actually populated:

- `business_context` becomes non-empty when retrieval matches
- `analysis_goal` is generated through `MockLLMClient`
- `analysis_plan` is generated through `MockLLMClient`

No top-level state fields are renamed or removed.

## Data Flow

### Task creation

`POST /api/analysis/start`

1. Load the uploaded file profile
2. Retrieve business context from JSONL knowledge base
3. Generate analysis goal through `MockLLMClient`
4. Generate analysis plan through `MockLLMClient`
5. Persist state with populated `business_context`
6. Record `task_created`, `rag_retrieved`, `goal_understood`, `plan_generated`

### Task execution

`POST /api/analysis/{task_id}/run`

1. Load persisted task state
2. Reuse existing `business_context`
3. Execute field matching, aggregation, chart generation, report generation, and evaluation
4. Keep event and failure behavior unchanged from the current hardened MVP

## Failure Handling

The new layer must explicitly handle:

- missing or malformed JSONL knowledge base
- zero retrieval hits
- unsupported question patterns in `MockLLMClient`

Required behavior:

- retrieval failure should not crash task creation
- empty retrieval should produce `business_context = []`
- empty retrieval should still record `rag_retrieved` with zero items
- `MockLLMClient` fallback should still produce a generic grouped-analysis goal and plan

## Acceptance Criteria

This round is complete when:

- new `llm/` and `rag/` modules exist and are covered by tests
- `POST /api/analysis/start` returns non-empty `analysis_goal` and `analysis_plan` through `MockLLMClient`
- at least category and region questions produce non-empty `business_context`
- task state includes persisted `business_context`
- event timeline includes `rag_retrieved`
- the full backend test suite still passes
