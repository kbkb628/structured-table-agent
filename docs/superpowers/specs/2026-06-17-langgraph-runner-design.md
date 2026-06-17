# LangGraph Runner Migration Design

## Goal

Migrate the current synchronous `analysis_runner` orchestration into a minimal LangGraph-based state flow while preserving the truthful MVP capability boundary that already exists:

- keep the same API contracts
- keep the same task-state top-level fields
- keep the same tool execution, event recording, error handling, and evaluation behavior
- do not add real LLM APIs, Redis, frontend changes, or async workers

This round is about orchestration shape, not feature-surface expansion.

## Scope

### In scope

- `backend/app/agent/state.py`
- `backend/app/agent/nodes.py`
- `backend/app/agent/graph.py`
- `backend/app/agent/__init__.py`
- switching `/api/analysis/{task_id}/run` to use the graph-backed runner
- minimal LangGraph dependency integration
- tests that verify graph-based execution still produces the same externally visible task outcomes

### Out of scope

- dynamic branching beyond the current linear loop
- Redis-backed checkpoints
- multi-turn conversation memory
- real model routing
- frontend progress streaming

## Design Decisions

### 1. Preserve the existing state contract exactly

The task-state schema is already frozen around:

- `analysis_goal`
- `business_context`
- `analysis_plan`
- `field_understanding`
- `tool_results`
- `chart_specs`
- `final_report`
- `eval_result`
- `events`
- `errors`

LangGraph should operate on the same dictionary structure instead of introducing a second incompatible state model. `agent/state.py` may provide typing aliases or helpers, but must not rename top-level keys.

### 2. Model the current runner as a linear graph first

The current execution sequence is already stable and real. The minimal graph should encode this sequence:

1. `load_task_node`
2. `match_fields_node`
3. `execute_tools_node`
4. `generate_charts_node`
5. `generate_report_node`
6. `evaluate_report_node`

This is enough to satisfy the guide's requirement that `/run` be graph-driven without prematurely adding speculative branching.

### 3. Reuse existing logic instead of rewriting behavior

The node implementations should call the same utilities already proven by tests:

- `match_fields`
- `groupby_aggregate`
- `generate_chart`
- `generate_report`
- `score_task_state`
- analysis store event and persistence helpers

The migration should minimize logic drift. The goal is that the graph runner remains behaviorally equivalent to the current synchronous runner for successful and failed cases.

### 4. Keep failure handling explicit inside nodes

Each node must preserve current truthful degradation rules:

- no silent failures
- write to `errors`
- emit the same failure events
- persist failed state
- stop the graph once the task has irrecoverably failed

### 5. Introduce only the minimum LangGraph dependency surface

The project only needs enough LangGraph surface to compile and execute a linear state graph. We do not need checkpointing, persistence plugins, or message abstractions in this round.

## Node Responsibilities

### `load_task_node`

- load task state from SQLite
- ensure status becomes `running`
- ensure `current_step` is set consistently

### `match_fields_node`

- run `match_fields`
- persist `field_understanding`
- emit `fields_matched`
- fail fast when no executable plan can be derived

### `execute_tools_node`

- loop through metrics
- call `groupby_aggregate`
- record tool calls and tool events
- append `tool_results` and `intermediate_findings`
- fail on tool failure or empty results

### `generate_charts_node`

- build chart specs for successful tool results
- record chart events
- degrade explicitly on chart failure without discarding valid tool results

### `generate_report_node`

- call `generate_report`
- persist `final_report`
- emit `report_generated`

### `evaluate_report_node`

- call `score_task_state`
- persist `eval_result`
- emit `eval_finished`
- mark task completed and persist final state

## Acceptance Criteria

This round is complete when:

- `/api/analysis/{task_id}/run` executes through LangGraph
- successful category, region, and channel runs still complete
- failure scenarios still produce truthful failed states and events
- `eval_result` is still persisted
- full backend tests pass
