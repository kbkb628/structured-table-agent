# Observability Closure Design

## Goal

Close the MVP observability gap described in `DEVELOPMENT_GUIDE.md` by giving `backend/app/observability` a real responsibility boundary instead of keeping event and trace logic scattered across API, agent, and storage modules.

This round should:

- centralize task event recording helpers in `observability/`
- centralize event-type constants used by trace scoring and runtime flow
- preserve the existing SQLite event table, API responses, and task-state schema

This round does not add dashboards, external tracing backends, or new persistence tables.

## Scope

### In scope

- `backend/app/observability/event_logger.py`
- `backend/app/observability/trace_models.py`
- wiring existing runtime paths to the new observability helpers
- regression tests for startup-event sequence and event hydration

### Out of scope

- OpenTelemetry
- Langfuse
- frontend timeline redesign
- event replay UI
- trace sampling or metrics aggregation

## Design Decisions

### 1. Keep storage and observability separate

`storage/analysis_store.py` should remain the low-level SQLite access layer.

`observability/event_logger.py` should become the semantic event layer that:

- names lifecycle events
- provides reusable helper methods
- hydrates persisted events back into task state

This keeps API and agent code focused on business flow instead of event row construction.

### 2. Freeze event names in one place

The MVP already depends on stable event names for:

- `/api/analysis/{task_id}/events`
- `RuleScorer.trace_completeness`
- fixed eval cases

`trace_models.py` should hold these constants so future changes do not silently drift between runtime and scoring logic.

### 3. Preserve existing event semantics

This round is a refactor with small testable improvements, not a behavior rewrite.

The following truths must stay unchanged:

- startup still records `task_created`, `rag_retrieved`, `goal_understood`, `plan_generated`
- runtime still records tool, chart, report, completion, failure, and eval events
- task state still exposes `events` as the persisted ordered timeline

### 4. Add only tests that prove the boundary

The new tests should prove:

- startup helper writes the expected ordered event sequence
- state hydration reloads the latest persisted events into `state["events"]`

No broad snapshot tests are needed for this round.

## Acceptance Criteria

This round is complete when:

- `backend/app/observability` is a real used module, not an empty planned directory
- API, eval, and agent flows all use observability helpers instead of directly constructing lifecycle events
- trace scoring reads required event names from a shared source
- focused tests and full backend tests pass
