# Resume Tech Alignment Design

## Goal

Define a single truthful technical alignment roadmap so every technology named in the resume can eventually be backed by real code, runtime evidence, and test coverage in this repository.

This design treats the current repository as a real first-stage backend that already supports the main structured-table analysis loop, then identifies which named technologies are already grounded, which are only partially grounded, and which must be implemented before they can remain in the resume.

## Current Context

The repository already has a truthful backend loop built around:

- FastAPI APIs for upload, task creation, task execution, evaluation, provider diagnostics, demo delivery, and project runtime overview
- LangGraph orchestration with explicit `route_next_step`
- Deterministic tool execution through pandas and DuckDB
- Pydantic schemas for requests, tool arguments, and structured outputs
- SQLite persistence for files, tasks, events, tool logs, and eval results
- Redis-first session storage with SQLite fallback and granular recovery
- Real Tongyi Qianwen integration through `QwenClient`
- A lightweight local retrieval layer over JSONL knowledge items

The resume and extracted resume text still go further than the current implementation in several places, especially:

- `embedding + BM25 + rerank`
- stronger multi-turn Redis memory wording
- full `LLM-as-Judge`
- `DockerSandbox`
- direct `Plotly` wording if interpreted as real library-backed chart generation

The user requirement for the next stage is stricter than the earlier MVP rule: if a technology is named in the resume, it should be truly implemented in the project rather than preserved only through softened wording.

## Hard Requirements

The alignment work must follow these rules:

1. A resume technology can be treated as implemented only when code, runtime evidence, and test evidence all exist.
2. A partially similar implementation is not enough. For example:
   - BM25-style scoring is not the same as a true BM25 retrieval stage
   - `plotly_spec` generation is not the same as explicit Plotly library usage
   - lightweight `llm_judgement` is not the same as a full `LLM-as-Judge` evaluation layer
   - Redis-backed task state is not the same as multi-turn memory with sliding window and summary compression
3. New implementations must stay truthful to the system's existing architecture:
   - deterministic tools remain the source of truth for numeric conclusions
   - retrieval augments semantics instead of replacing exact tabular computation
   - evaluation and sandbox features must expose explicit degradation and error paths
4. Delivery materials must be updated only after the underlying implementation exists.

## Non-Goals

This alignment program does not include:

- a production-grade multi-tenant platform
- a full React frontend
- async queue infrastructure as a prerequisite for alignment
- broad product expansion unrelated to the resume technologies

These may still be reasonable future work, but they are not required for the stated alignment goal.

## Alignment Classification

The current repository should treat named technologies in three categories.

### Already Grounded

These can remain in the resume now because the implementation is already real:

- FastAPI
- LangGraph
- Pydantic
- pandas
- DuckDB
- SQLite
- Qwen / Tongyi Qianwen provider integration

### Partially Grounded And Must Be Upgraded

These exist in weaker or narrower forms and must be strengthened before strong resume wording is justified:

- RAG
- BM25
- Redis memory
- Plotly
- LLM-based evaluation

### Not Yet Grounded

These require entirely new implementation before they can remain in strong resume wording:

- embedding retrieval
- rerank
- DockerSandbox

## Recommended Delivery Strategy

The alignment work should be executed in phases ordered by dependency and risk rather than by whether a module already exists.

Three alternatives were considered:

### Approach A: Patch Each Resume Line Independently

Implement one missing resume phrase at a time, regardless of dependency order.

Pros:

- easy to explain
- gives quick visible progress

Cons:

- causes rework because retrieval, memory, eval, and sandbox overlap
- increases the chance of inconsistent architecture

### Approach B: Build New Capabilities First, Then Revisit Existing Modules

Start with the most obviously missing items like DockerSandbox and full judge logic, then adapt current modules later.

Pros:

- quickly closes the largest visible gaps

Cons:

- wrong dependency order
- forces new features to target unstable or incomplete retrieval and memory layers

### Approach C: Phase By Dependency And Runtime Evidence

Upgrade the core data path first, then memory, then evaluation, then sandbox, then final resume/document alignment.

Pros:

- lowest rework risk
- preserves truthful runtime evidence at every stage
- keeps later modules grounded in earlier modules

Cons:

- less dramatic early demos than jumping straight to sandbox work

### Recommendation

Use Approach C.

It fits the existing repository, keeps delivery truthful, and avoids building expensive modules on top of weak intermediate abstractions.

## Implementation Phases

### Phase 0: Alignment Baseline And Gating

Purpose:

- freeze the meaning of "real implementation" for resume technologies
- keep later work from drifting back into softened wording

Outputs:

- a repository-level alignment matrix document
- explicit acceptance gates for each technology
- a rule that resume wording upgrades follow implementation, not the reverse

Acceptance conditions:

- every named technology is classified as grounded, partially grounded, or not grounded
- each partially grounded technology has a concrete target state

### Phase 1: Retrieval Stack Realization

Purpose:

- upgrade the current local hybrid retriever into a truthful staged retrieval stack that supports `embedding + BM25 + rerank`

Current baseline:

- the repository already has local JSONL retrieval with keyword overlap, phrase hits, field weighting, and an internal BM25-style scoring component

Required upgrades:

- split retrieval into explicit stages:
  - lexical retrieval with a real BM25 component
  - vector retrieval with real embeddings
  - rerank stage over merged candidates
- preserve retrieval evidence in state and runtime inspection
- expose stage-specific scores instead of only a blended score

Implementation direction:

- retain JSONL knowledge items as the source dataset
- add chunk or item embedding generation and persistence
- adopt a local vector store suitable for the repository scale
- add a rerank module that consumes retrieved candidates and query context

Acceptance conditions:

- a real embedding stage exists and is exercised in tests
- a real BM25 retrieval stage exists as a first-class step
- rerank is a distinct implemented stage, not just final score sorting
- runtime evidence can show lexical, vector, rerank, and final merged retrieval outputs

### Phase 2: Plotly Realization

Purpose:

- upgrade chart generation from manually assembled Plotly-compatible specs to real Plotly-backed figure generation

Current baseline:

- the repository currently builds validated `plotly_spec` payloads but does not explicitly use the Plotly library to produce them

Required upgrades:

- use Plotly library objects to generate charts
- keep JSON-style output for persistence and demo rendering through figure serialization
- preserve existing schema discipline where practical

Acceptance conditions:

- chart generation code imports and uses Plotly directly
- serialized chart payloads come from Plotly figure generation rather than hand-built dicts
- tests validate the new behavior without broad frontend changes

### Phase 3: Redis Memory Realization

Purpose:

- upgrade Redis usage from task-state persistence and recovery into a truthful multi-turn memory subsystem

Current baseline:

- the repository already stores task state, granular task segments, and task locks in Redis when available
- it does not yet provide sliding window memory, summary memory, or explicit multi-turn context compression

Required upgrades:

- add turn-level memory records
- add a sliding window policy
- add summary compaction for older turns
- define how memory is fed back into planning, retrieval, and reporting

Acceptance conditions:

- Redis stores both task-state segments and explicit conversation memory segments
- memory pruning and summary refresh are real runtime behaviors
- tests cover multi-turn accumulation and summary refresh
- project runtime introspection can show memory status without overstating autonomy

### Phase 4: Full LLM-As-Judge Realization

Purpose:

- upgrade the current light `llm_judgement` output into a real LLM judge layer that complements the deterministic rule scorer

Current baseline:

- the repository already has a real rule scorer
- the repository already has a real Qwen-powered `judge_report` call
- the current judge output is intentionally narrow and should not be treated as a full judge subsystem

Required upgrades:

- define a richer judge schema
- pack structured evidence for judging:
  - user question
  - final report
  - tool outputs
  - retrieval evidence
  - selected trace evidence
- define explicit judge dimensions and aggregate outputs
- define judge degradation behavior when provider calls fail

Acceptance conditions:

- the LLM judge has a dedicated schema and dimension model
- evaluation output clearly separates rule scores from LLM judge scores
- tests cover success, malformed response, and provider-failure degradation
- runtime overview can expose judge evidence without confusing it with deterministic truth

### Phase 5: DockerSandbox Realization

Purpose:

- implement a truthful sandboxed execution capability that can be named directly in the resume

Current baseline:

- no real Docker sandbox execution module currently exists

Required upgrades:

- add a dedicated sandbox execution module
- define the container lifecycle and execution API
- enforce resource, timeout, and filesystem restrictions
- persist execution traces and surfaced degradation

Design constraints:

- do not replace the main deterministic tool chain with sandbox execution
- treat sandbox execution as an advanced controlled tool
- require explicit observability around code, result, timeout, and failure status

Acceptance conditions:

- code executes inside a controlled Docker container
- timeout and resource limits are enforced
- tests cover success, timeout, and blocked access behavior
- runtime evidence shows sandbox invocation and results

### Phase 6: Final Resume And Delivery Realignment

Purpose:

- update project, demo, and interview materials only after the underlying technologies are real

Required updates:

- README
- `docs/PROJECT_STATUS.md`
- `docs/RESUME_PROJECT_DESCRIPTION.md`
- `docs/RESUME_EVIDENCE_MAP.md`
- `docs/INTERVIEW_GUIDE.md`
- supporting demo and readiness documents

Acceptance conditions:

- every named resume technology points to code, runtime, and tests
- weak fallback wording like "BM25-style", "Plotly-style", or "supplementary llm_judgement" is removed only after replacement implementations exist

## Module-Level Work Queue

The existing modules that require real-implementation upgrades are:

- `backend/app/rag/keyword_retriever.py`
- `backend/app/tools/chart_tool.py`
- `backend/app/storage/session_store.py`
- `backend/app/llm/qwen_client.py`
- `backend/app/eval/*`
- `backend/app/api/project_status.py`
- `backend/app/api/demo.py`
- delivery and resume evidence documents

The main new module family that must be introduced is:

- sandbox execution support for Docker-based controlled analysis execution

## Testing And Evidence Requirements

Every phase must end with three evidence layers:

1. Code evidence
   - implementation exists in repository modules
2. Runtime evidence
   - API, demo, or script can surface the feature in a truthful way
3. Test evidence
   - focused tests exist and pass for the implemented behavior

No phase should be considered complete if one of those three layers is missing.

## Commit Strategy

Each phase should be delivered through multiple small commits rather than one large merge point.

Recommended commit boundaries:

- red tests or frozen acceptance expectations
- minimal implementation milestone
- runtime evidence exposure
- documentation and resume evidence alignment

This preserves the repository's current practice of making important delivery checkpoints explicit in git history.

## Risks

The main delivery risks are:

- embedding and rerank components introducing external model/runtime dependencies
- DockerSandbox adding OS, Docker, and security constraints on Windows
- LLM judge stability degrading tests if schema boundaries are not strict
- memory features expanding scope into a general chat system instead of targeted analysis memory

The mitigation is to preserve phase boundaries and insist on small truthful increments.

## Success Criteria

This alignment program is successful when:

- the technologies named in the resume are either fully implemented or explicitly removed from strong wording
- partially grounded substitutes are replaced with true implementations where the resume requires them
- the repository can demonstrate the named technologies through code, runtime outputs, and tests
- the project remains coherent as a structured-table analysis agent rather than expanding into unrelated feature work
