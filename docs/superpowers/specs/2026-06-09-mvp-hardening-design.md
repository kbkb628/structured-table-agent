# MVP Hardening Design

## Goal

Keep the current synchronous analysis-task loop, but make it truthful enough for the guide's MVP boundary:

- cover the three required demo question families with real tool execution
- record failures and degradation states explicitly instead of silently breaking
- produce a real `eval_result` based on rule scoring and expose it through API/state

This design does not add LangGraph, RAG, Redis, MockLLM, or async execution.

## Scope

### In scope

- category sales TopN
- region sales comparison
- channel order-count and sales-amount comparison
- task failure handling for field mismatch, non-numeric metrics, empty aggregation, and chart degradation
- deterministic report fallback behavior
- `RuleScorer` implementation and `eval_result` persistence
- `POST /api/eval/run`

### Out of scope

- LangGraph node orchestration
- knowledge-base retrieval
- real LLM provider integration
- Redis session state
- background jobs or polling workers

## Design Decisions

### 1. Keep one synchronous runner, extend it to multi-metric execution

The existing runner already owns task orchestration. Instead of introducing new orchestration layers, it should support one or more aggregation requests derived from the user question.

- category and region questions still execute one aggregation
- channel performance executes two aggregations:
  - order count by channel
  - sales amount sum by channel

The task state already supports `tool_results`, `chart_specs`, and `intermediate_findings`, so this extension does not require changing frozen top-level state fields.

### 2. Make field matching return an executable analysis spec

`match_fields` should stop returning only a single dimension/metric pair. It should return:

- `dimension_field`
- `metrics`
- `analysis_type`
- candidate fields and warnings

`metrics` is a list of tool requests the runner can execute directly. This keeps logic centralized and avoids ad-hoc branching in the API layer.

### 3. Treat chart generation as degradable, not mandatory

If tool results exist but chart input is empty or malformed:

- do not discard the task
- write a chart-related error into `errors`
- record a `chart_failed` event
- still generate a text report from tool results

This follows the guide's rule that failure should degrade when possible, not pretend success or crash the whole service.

### 4. Add a truthful rule scorer

`RuleScorer` will evaluate:

- schema validity
- tool success rate
- field validity
- chart validity
- report completeness
- trace completeness

It uses only the real task state and recorded events. No judge model is introduced.

### 5. Keep API contract stable

Existing analysis endpoints remain unchanged. We only add:

- `POST /api/eval/run`

This endpoint supports:

- running eval for an existing `task_id`
- returning the computed `eval_result`
- persisting that same result back into the task state

## Failure Handling

The following cases must become explicit:

- unmatched dimension field
- unmatched metric field
- unsupported combined request shape
- empty aggregation result
- chart generation failure
- evaluation request for missing task

All failures must:

- write structured entries into `errors`
- emit task events
- avoid fake success states

## Acceptance Criteria

The round is complete when all of the following are true:

- all three demo question families run through the real backend loop
- failed analysis scenarios return truthful task state and events
- completed tasks contain non-empty `eval_result`
- `POST /api/eval/run` works for an existing task
- automated tests cover success and failure flows
