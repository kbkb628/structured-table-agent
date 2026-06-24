# LLM-As-Judge Closure Enhancement Design

## Goal

Strengthen the repository's existing `LLM-as-Judge` implementation so it becomes a more complete, reviewable, and interview-ready subsystem without expanding into a separate product surface.

This design is intentionally a closure-enhancement pass rather than a brand-new feature family. The repository already has:

- a real `judge_report()` interface on the replaceable `LLMClient`
- real `QwenClient` judge execution
- a structured `JudgeResult` schema
- persisted `llm_judgement` data in task state
- runtime exposure through `GET /api/project-status`
- delivery docs that already describe a real structured judge layer

The remaining gap is not basic existence. The gap is that the judge still needs a tighter end-to-end evidence chain and stronger runtime visibility so the implementation better matches resume-level explanation and live demonstration needs.

## Current Context

The current backend already separates two quality layers:

- `RuleScorer` for deterministic structural checks
- `LLM-as-Judge` for model-based supplementary quality review

The current judge already emits:

- `judge_summary`
- `judge_status`
- dimension outputs for:
  - `groundedness`
  - `completeness`
  - `clarity`
- explicit `degraded` metadata when the provider path fails

The current system also already exposes parts of this through:

- task state persistence
- `GET /api/project-status`
- `/demo`
- fixed eval delivery materials

However, the implementation still has closure weaknesses:

1. the packed evidence passed into the judge can be strengthened and standardized
2. judge runtime visibility can be made more consistent across `/api/eval/run`, `/api/project-status`, `/demo`, and fixed eval outputs
3. the docs and runtime outputs should align around one stable story: the judge is a structured supplementary evaluation layer, not a vague extra flag and not a replacement for deterministic scoring

## Hard Requirements

This enhancement must follow these rules:

1. Do not let the judge replace deterministic `RuleScorer`.
2. Do not merge judge scores into the rule-based `overall_score`.
3. Do not invent a separate asynchronous judge platform, queue, service, or database table.
4. Preserve the completed-task path even when judge provider calls fail.
5. Keep judge output structured and explicit.
6. Improve interview readiness only through real code, runtime evidence, and tests.

## Non-Goals

This design does not include:

- creating a standalone judge service
- adding many new dimensions just for appearance
- changing the main numerical analysis source of truth
- introducing a judge-only persistence layer
- implementing long-running asynchronous judge jobs
- turning the judge into a gate that blocks task completion

The judge remains a supplementary quality layer over a deterministic analysis pipeline.

## Problem Statement

The repository already has a truthful structured judge, but the current experience can still feel narrower than the resume-oriented explanation suggests.

The real missing closure is:

- a better-defined evidence pack for judging
- stronger cross-surface runtime visibility
- a more consistent explanation boundary between:
  - rule-based evaluation
  - model-based judgement
  - task completion semantics

The next step should therefore optimize for completeness, explainability, and runtime evidence rather than for adding more dimensions or building a larger subsystem.

## Approaches Considered

### Approach A: Display-Only Enhancement

Focus mostly on `/demo`, `/api/project-status`, and documentation so the judge looks more substantial without changing much of the core execution flow.

Pros:

- fast visible improvement
- minimal code churn

Cons:

- risks overrepresenting a judge path whose evidence packing is still weaker than the presentation
- less defensible in code review or interview follow-up

### Approach B: Core-Only Enhancement

Focus on packed evidence and degradation semantics, while leaving runtime displays and delivery materials mostly unchanged.

Pros:

- technically clean
- strongest internal correctness

Cons:

- weaker visible improvement for demo and interview use
- slower payoff in delivery evidence

### Approach C: Closure Enhancement Across Core Plus Runtime Evidence

Improve packed judge evidence, preserve graceful degradation, and then expose the improved outputs consistently across the runtime surfaces already used in this repository.

Pros:

- strongest balance of truthfulness and demonstrability
- directly improves resume support
- does not require expanding scope into a new subsystem

Cons:

- slightly broader than a pure core refactor

## Recommendation

Use Approach C.

This keeps the judge grounded in real implementation, strengthens the evidence chain, and improves demo/readiness value without drifting into a new platform or exaggerated capability surface.

## Proposed Design

### 1. Strengthen the Judge Evidence Pack

The judge should consume one explicit packed evidence structure instead of relying on only a small set of loosely interpreted inputs.

Recommended packed evidence contents:

- `question`
- `analysis_goal`
- `final_report`
- `tool_results`
- `business_context`
- lightweight trace evidence derived from task events
- rule-score summary from `eval_result`

This is not meant to create a separate evidence database. It is meant to make the current judge call more explicit and more defensible.

The purpose is simple:

- `question` explains the user's intent
- `analysis_goal` explains the normalized target
- `final_report` is what the judge is reviewing
- `tool_results` provide deterministic grounding evidence
- `business_context` explains semantic retrieval support
- event/trace summary explains process completeness
- `eval_result` shows the deterministic quality baseline beside the model review

### 2. Preserve Judge As A Supplementary Layer

The judge must remain separate from `RuleScorer`.

That means:

- `RuleScorer` still produces the deterministic `overall_score`
- judge dimensions must not be folded into that score
- runtime outputs can show both layers side by side
- the docs must continue to explain that the judge supplements, not replaces, deterministic checks

This separation is important for both engineering clarity and interview honesty.

### 3. Keep Judge Failure Non-Fatal

If a provider-backed judge call fails:

- the task should remain `completed` if the deterministic analysis path completed successfully
- `llm_judgement` should record:
  - `judge_status = degraded`
  - `degraded = true`
  - issues describing the failure
- `errors` should include a stable degradation record, such as `LLM_JUDGEMENT_DEGRADED`

This behavior matches the architectural truth:

- the judge is not the core numerical execution path
- the system should still surface a completed report even if the supplementary quality layer degrades

### 4. Strengthen Runtime Evidence Across Existing Surfaces

This design should not create new surfaces. It should improve the ones that already exist.

#### `/api/project-status`

The runtime overview should expose a stable latest-task judgement summary that includes:

- `judge_status`
- `judge_summary`
- `degraded`
- `issue_count`
- `groundedness_score`
- `completeness_score`
- `clarity_score`

This keeps the latest-task runtime view strong enough for review and demo use.

#### `/api/eval/run`

The evaluation API should remain honest by keeping rule scores and judge status separate.

Recommended additions:

- `judge_status`
- `judge_degraded`
- optionally a compact judge summary field if it is clearly labeled

The rule-based `overall_score` should remain a rule score, not a blended score.

#### `/demo`

The demo should include a read-only judge output block that makes the current judge state easy to explain live.

Recommended displayed fields:

- `judge_status`
- `judge_summary`
- `degraded`
- `groundedness_score`
- `completeness_score`
- `clarity_score`
- `issue_count`

This is enough for interview demonstration without turning the page into a judge dashboard.

#### Fixed Eval Summary

The fixed eval summary should expose basic judge state per case so the quality story is not limited to one latest task.

Recommended minimum:

- each result item includes `judge_status`
- aggregate outputs stay rule-centric, but the result set remains judge-aware

This gives the repository one more truthful runtime evidence layer for interviews and audits.

### 5. Keep Dimension Scope Stable

The current dimension set is already sufficient for this phase:

- `groundedness`
- `completeness`
- `clarity`

This design explicitly avoids adding many new dimensions simply to make the system appear richer.

Reason:

- more dimensions create more prompt/schema/test surface
- more dimensions do not meaningfully improve the current interview truth boundary
- the real gap is closure and visibility, not count of judge axes

If the current dimensions are packed with stronger evidence and surfaced more consistently, they are enough.

## Module Impact

### Primary Code Files

- `backend/app/agent/nodes.py`
- `backend/app/api/eval.py`
- `backend/app/api/project_status.py`
- `backend/app/api/demo.py`

### Supporting LLM Files

- `backend/app/llm/base.py`
- `backend/app/llm/qwen_client.py`
- `backend/app/llm/mock_client.py`
- `backend/app/schemas/judge_schema.py`

These already exist and should be enhanced rather than replaced.

### Primary Test Files

- `backend/tests/test_analysis_runner.py`
- `backend/tests/test_analysis_api.py`
- `backend/tests/test_project_status_api.py`
- `backend/tests/test_qwen_client.py`
- `backend/tests/test_judge_schema.py`
- `backend/tests/test_eval_cases.py`
- `backend/tests/test_delivery_docs.py`

### Delivery Docs

- `docs/PROJECT_STATUS.md`
- `docs/RESUME_PROJECT_DESCRIPTION.md`
- `docs/RESUME_EVIDENCE_MAP.md`
- optionally a narrow adjustment in `docs/INTERVIEW_GUIDE.md`

## Testing Strategy

The implementation should follow TDD and end with four evidence layers.

### 1. Core Judge Flow Tests

Verify:

- successful judge output is persisted in completed tasks
- packed judge evidence includes the expected fields
- judge degradation does not fail the task

### 2. Runtime Evidence Tests

Verify:

- `GET /api/project-status` surfaces structured judge summary
- `/api/eval/run` exposes judge status separately from rule scores
- `/demo` reflects judge runtime values in read-only output

### 3. Fixed Eval And Delivery Tests

Verify:

- fixed eval results include per-case judge state
- doc assertions require structured judge wording and evidence references

### 4. Full Backend Verification

Run the full backend suite to ensure:

- no regression in retrieval
- no regression in memory/runtime evidence
- no regression in sandbox/runtime evidence
- no regression in provider diagnostics

## Documentation Boundary

After implementation, all related materials should align around one stable statement:

- the project has a real structured `LLM-as-Judge` layer
- the judge consumes packed evidence from the real task execution path
- the judge degrades explicitly when provider calls fail
- deterministic rule scoring remains the primary structural quality baseline

The documentation should not say or imply:

- the judge replaces rule scoring
- the judge blocks task completion
- the judge is an independent production review platform

## Acceptance Criteria

This enhancement is complete only when all of the following are true:

1. Judge input uses a clearer packed evidence structure.
2. Judge degradation is explicit and non-fatal to completed tasks.
3. `/api/project-status` surfaces the current structured judge summary.
4. `/api/eval/run` exposes judge status without blending it into rule score.
5. `/demo` exposes a readable judge runtime summary.
6. fixed eval outputs include basic judge state per result.
7. delivery docs describe the judge as a structured supplementary evaluation layer.
8. focused tests and the full backend suite pass.

## Risks And Mitigation

### Risk: Overexpansion Into A Larger Judge Platform

Mitigation:

- no new async pipeline
- no new judge table
- no large dimension expansion

### Risk: Overstating Capabilities In Docs

Mitigation:

- keep rule-vs-judge separation explicit
- describe judge as supplementary and structured

### Risk: Provider Instability Creating False Task Failures

Mitigation:

- keep judge degradation non-fatal
- persist explicit degraded status and issues

## Success Condition

This design succeeds when `LLM-as-Judge` becomes easier to explain, easier to demonstrate, and more defensible through code and runtime evidence, while still staying within the real capability boundary of the current repository.
