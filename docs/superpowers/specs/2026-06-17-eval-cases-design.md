# Fixed Eval Cases Design

## Goal

Add a fixed-case regression layer on top of the existing `RuleScorer` so the MVP can run a repeatable evaluation set instead of only scoring one task at a time.

This round should:

- define a small fixed-case corpus aligned with the current sample CSV and supported question families
- execute those cases through the real backend loop
- summarize case-level pass/fail and scoring results

This round does not add any new model capability, frontend interface, or external service.

## Scope

### In scope

- `backend/app/eval/eval_cases.py`
- a small execution entrypoint in the eval API or eval module
- tests for fixed-case execution and summary output
- README updates describing how to run the regression set

### Out of scope

- external benchmarking systems
- LLM-as-Judge
- multiple datasets beyond the existing sample sales CSV
- UI dashboards for eval history

## Design Decisions

### 1. Fixed cases should map to real supported MVP scenarios

The regression set must only cover behaviors the code truthfully supports today:

- category sales TopN
- region sales comparison
- channel order-count and sales comparison

No cases should assert unsupported trend analysis, anomaly detection, or external business semantics.

### 2. Cases should execute the real loop, not mock the runner

Each fixed case should:

1. upload or register the sample CSV
2. create an analysis task
3. run the real LangGraph-backed analysis flow
4. score the result using the existing `eval_result`

This keeps regression meaningful and grounded in the same behavior users actually call.

### 3. Keep case assertions lightweight but truthful

Each case should define:

- `case_id`
- `question`
- expected minimum tool count
- expected minimum chart count
- expected status
- expected minimum overall score

Optional assertions can also include:

- expected event types
- expected required context ids

Assertions should focus on stable truths, not fragile exact wording.

### 4. Return a compact regression summary

The regression runner should return:

- total case count
- passed case count
- failed case count
- per-case results
- aggregate pass rate

Each case result should include:

- `case_id`
- `question`
- `passed`
- `task_id`
- `status`
- `overall_score`
- `issues`
- assertion failures if any

## Execution Model

The implementation can stay local and synchronous.

- use the existing sample CSV path
- create independent tasks for each case
- do not persist a second long-term eval history table in this round unless necessary

The main requirement is repeatability, not audit-history storage.

## Acceptance Criteria

This round is complete when:

- there is a real fixed-case definition module
- the regression runner executes all supported MVP case families
- tests verify summary structure and pass/fail behavior
- README documents how to run the fixed-case regression
