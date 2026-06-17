# Qwen Provider Integration Design

## Context

The current backend already exposes a replaceable `LLMClient` interface and uses `MockLLMClient` during task creation to generate `analysis_goal` and `analysis_plan`. The deterministic analysis loop, tool execution, persistence, and evaluation are already implemented and verified. The next step is to make the project better match the resume description by integrating a real LLM provider without weakening the deterministic tool chain.

This design raises the priority of truthful real-provider support above the earlier MVP-only preference for MockLLM-first operation. The project should be able to run against Tongyi Qianwen with the user's existing environment variable while keeping a minimal explicit fallback path for local development and failure diagnosis.

## Goals

- Add a real `QwenClient` implementation behind the existing `LLMClient` interface.
- Support provider selection through configuration rather than hard-coded imports.
- Use the real LLM in four capability points:
  - analysis goal generation
  - analysis plan generation
  - final report generation
  - report judgement
- Keep deterministic numeric computation inside pandas, DuckDB, and existing tools.
- Make provider failures explicit by default instead of silently pretending success.
- Preserve a controlled fallback path to `MockLLMClient` when explicitly configured.

## Non-goals

- No change to the deterministic tool chain for field matching, aggregation, chart generation, or persistence.
- No introduction of embedding, BM25, rerank, async queue, or DockerSandbox in this iteration.
- No claim that all analysis is LLM-native. Real numeric results must remain grounded in tool outputs.
- No broad frontend work in this change.

## Recommended Approach

Implement a provider factory with configuration-driven selection and add a `QwenClient` that calls the Qwen OpenAI-compatible chat completions API over HTTP. Keep `MockLLMClient` as a concrete fallback implementation, but stop treating it as the only normal path. When `LLM_PROVIDER=qwen`, the backend should instantiate the real provider and fail explicitly if required credentials are missing or if the call fails and fallback is disabled. When fallback is enabled, the failure should be visible in logs or state rather than hidden.

This approach fits the current codebase because `task_builder.py` already centralizes task-start LLM usage, and the `LLMClient` abstraction already exists. It also supports a resume-truthful statement: the project has completed replaceable provider integration and can run against Tongyi Qianwen in a real environment.

## Rejected Alternatives

### Replace MockLLM everywhere and remove fallback

This would maximize “realness” but would make the repo strongly dependent on an external API and undermine local verification and controlled failure behavior. It is too brittle for continued development.

### Build a fully generic multi-provider SDK layer now

This would be more extensible but adds unnecessary surface area for the current goal. The codebase only needs one truthful real provider today, and the existing abstraction is already enough to support later expansion.

## Architecture

### Provider configuration

Introduce explicit configuration values:

- `LLM_PROVIDER`
- `LLM_ALLOW_FALLBACK`
- `QWEN_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_MODEL`
- `QWEN_TIMEOUT_SECONDS`

The default provider can be set to `qwen` to better align with the current project direction, but the implementation must still allow an explicit `mock` mode for testability and offline runs.

### Provider factory

Add a small factory module responsible for:

- reading configuration
- validating whether a provider can be built
- returning `QwenClient` or `MockLLMClient`
- handling explicit fallback only when allowed

This removes direct `MockLLMClient()` construction from `task_builder.py`.

### Qwen client responsibilities

`QwenClient` will implement the existing `LLMClient` methods:

- `generate_analysis_goal`
- `generate_analysis_plan`
- `generate_report`
- `judge_report`

The client will send structured prompts to Qwen and parse JSON responses into Python objects expected by the current code. The client should validate the shape of the returned content and raise a provider error when the response cannot be parsed into the required structure.

### Prompting and output discipline

The real provider must not be allowed to invent unsupported capabilities. Prompts should instruct the model to:

- base numeric claims only on provided tool outputs
- return concise structured JSON
- avoid fabricating missing evidence
- acknowledge limitations when tool outputs are absent

Goal and plan generation can remain lightweight. Report generation and judging should be structured and bounded so the deterministic tool chain remains the source of truth for numbers.

## Data Flow Changes

### Task creation

`create_analysis_task()` and `build_analysis_state()` should resolve the configured provider through the factory instead of hard-coding `MockLLMClient`. This affects:

- `analysis_goal`
- `analysis_plan`

### Report stage

The current graph uses the deterministic `generate_report` tool. This change should extend the report stage as follows:

1. Keep the deterministic report tool to generate a grounded baseline report.
2. Use the configured `LLMClient.generate_report()` to produce an LLM-structured summary grounded in:
   - intermediate findings
   - chart specs
   - business context
   - deterministic report result
3. Persist the resulting final report only after it conforms to the existing final report schema.

This keeps the current stable chain while adding real-provider participation in the final narrative layer.

### Evaluation stage

The rule scorer remains primary. The configured `LLMClient.judge_report()` should be added as supplementary structured judgement data recorded into state without replacing `RuleScorer`.

## Error Handling

### Missing credentials

If `LLM_PROVIDER=qwen` and no API key is available:

- raise an explicit provider configuration error by default
- only fall back to `MockLLMClient` when `LLM_ALLOW_FALLBACK=true`

### Provider call failure

If Qwen returns an HTTP error, timeout, malformed JSON, or unusable content:

- record the failure details
- fail explicitly by default
- only fall back to mock when fallback is enabled

### Invalid model output

If the model returns content that cannot be parsed into the expected shape:

- treat it as a provider error
- do not silently coerce broken structures into partial success

## Testing Strategy

Follow TDD with explicit red-green verification for each behavior.

Coverage required:

- provider factory returns `MockLLMClient` when configured
- provider factory returns `QwenClient` when configured and credentials exist
- provider factory fails explicitly when Qwen is selected without API key
- provider factory falls back to mock when allowed
- task creation uses the configured provider for goal and plan generation
- report generation path can accept a non-mock provider result and persist schema-valid final output
- malformed Qwen responses raise provider errors

Tests should mock HTTP at the transport boundary rather than mocking internal parsing logic, so the provider contract is exercised realistically.

## Documentation Updates

Update the following documents after implementation:

- `backend/README.md`
- `docs/PROJECT_STATUS.md`
- `docs/RESUME_PROJECT_DESCRIPTION.md`
- `docs/INTERVIEW_GUIDE.md` if needed

The wording must be upgraded from “real provider not implemented” to a truthful statement such as “real Tongyi Qianwen provider integration completed, with explicit configurable fallback to MockLLM for local development or failure recovery.”

## Acceptance Criteria

- The backend can instantiate a real `QwenClient` using environment variables already present on the machine.
- Analysis task creation can generate `analysis_goal` and `analysis_plan` through Qwen.
- Final report generation can incorporate Qwen while staying bounded by deterministic tool outputs.
- Provider selection is configuration-driven.
- Missing credentials or provider failures do not silently masquerade as success.
- Tests cover provider selection, failure behavior, and task creation integration.
- Documentation and project-status files are updated to match the new truth boundary.
