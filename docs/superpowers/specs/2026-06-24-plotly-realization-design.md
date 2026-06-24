# Plotly Realization Design

## Goal

Upgrade chart generation from manually assembled Plotly-compatible dictionaries to real Plotly-backed figure generation, while preserving the existing backend API shape consumed by the current task pipeline, persistence layer, and `/demo` page.

This design treats Plotly realization as a focused tool-layer upgrade rather than a chart-delivery rewrite.

## Current Context

The repository already has a truthful chart-delivery path:

- analysis tools produce grouped rows through deterministic pandas / DuckDB execution
- `generate_chart()` returns a `ToolResponse`
- chart payloads are persisted into task state as `chart_specs`
- `/demo` renders the persisted `plotly_spec` structure without a browser-side Plotly dependency
- multiple tests already validate `chart_type`, `plotly_spec`, and failure behavior

However, the current implementation in `backend/app/tools/chart_tool.py` still assembles the `plotly_spec` dictionary by hand. That means the repository can truthfully claim Plotly-compatible output, but cannot yet strongly claim real Plotly library usage.

The user requirement is stricter: technologies named in the resume should be backed by real implementation, not only compatible structure.

## Hard Requirements

1. `generate_chart()` must use the real Plotly library to build the chart.
2. Existing output consumers must remain stable:
   - `ToolResponse` contract stays the same
   - `data["chart_type"]` stays the same
   - `data["plotly_spec"]` remains available and structurally compatible
3. Failure behavior must remain truthful and explicit:
   - empty rows still fail
   - missing fields still fail
   - unsupported `chart_type` still fail
4. Runtime evidence must become stronger than before:
   - the chart result should explicitly reveal that Plotly generated it
5. This phase must not expand into frontend or storage redesign.

## Non-Goals

This phase does not include:

- changing `/demo` to import or execute Plotly in the browser
- storing HTML exports or image artifacts
- redesigning chart persistence format across the whole system
- adding many new chart types
- changing the LangGraph analysis flow

## Options Considered

### Approach A: Replace Hand-Built Spec With Plotly Internals Only

Use Plotly to build figures, but keep returning only `plotly_spec` with no new runtime evidence fields.

Pros:

- minimal surface-area change
- easiest drop-in replacement

Cons:

- weaker runtime proof
- the implementation is real, but the result payload does not clearly expose that fact

### Approach B: Keep Existing Output Shape And Add Plotly Runtime Evidence

Use Plotly to build the figure, serialize it through `figure.to_plotly_json()`, keep `plotly_spec`, and add explicit runtime evidence fields such as:

- `figure_backend`
- `plotly_trace_count`

Pros:

- real Plotly implementation
- existing consumers remain stable
- runtime evidence becomes explicit
- narrow blast radius

Cons:

- requires a small schema expansion
- requires targeted test and document updates

### Approach C: Redesign Chart Delivery Around Full Figure JSON Or HTML

Persist full figure payloads or rendered assets and update all consumers accordingly.

Pros:

- most direct Plotly-centric delivery model

Cons:

- too much scope for this phase
- would ripple through demo rendering, persistence, tests, and docs
- unnecessary for the current resume-alignment goal

## Recommendation

Use Approach B.

It is the smallest truthful upgrade that:

- makes Plotly library usage real
- preserves the current backend contracts
- adds explicit runtime evidence
- avoids turning a tool-layer realization into a UI rewrite

## Target Design

### External Contract

`generate_chart()` keeps the same function signature:

```python
def generate_chart(
    title: str,
    x_field: str,
    y_field: str,
    rows: list[dict],
    chart_type: str = "bar",
) -> ToolResponse:
```

Its success payload remains compatible:

```python
{
    "chart_type": "bar" | "line",
    "plotly_spec": {...},
    "figure_backend": "plotly",
    "plotly_trace_count": 1,
}
```

The current `plotly_spec` key remains the canonical persisted chart structure so the rest of the system does not need to change.

### Internal Chart Construction

`chart_tool.py` will:

1. validate `rows`, `x_field`, `y_field`, and `chart_type`
2. build a real `plotly.graph_objects.Figure`
3. add one trace:
   - `go.Bar` for `bar`
   - `go.Scatter(mode="lines+markers")` for `line`
4. apply layout titles through Plotly
5. serialize the figure through `figure.to_plotly_json()`
6. return the serialized payload as `plotly_spec`

This ensures the final persisted chart spec comes from Plotly itself rather than a hand-written dict.

### Schema Changes

`GenerateChartOutput` should be extended minimally with:

- `figure_backend: str`
- `plotly_trace_count: int`

The existing `PlotlySpec` and `plotly_spec` structure should remain intact.

No broad schema redesign is needed in this phase.

### Metadata Behavior

Existing metadata should remain:

- `row_count`
- `fields_used`
- `chart_type`

If useful, `metadata` may additionally include:

- `figure_backend`

But the primary runtime evidence should live in `data`, because `data` is what the system already treats as chart artifact payload.

## Files In Scope

### Must Modify

- `backend/pyproject.toml`
- `backend/app/tools/chart_tool.py`
- `backend/app/schemas/tool_schema.py`
- `backend/tests/test_chart_and_report_tools.py`
- `backend/tests/test_tool_registry.py`

### Likely Document Updates After Implementation

- `docs/PROJECT_STATUS.md`
- `docs/RESUME_PROJECT_DESCRIPTION.md`
- `docs/RESUME_EVIDENCE_MAP.md`
- `backend/tests/test_delivery_docs.py`

## Testing Plan

This phase should follow TDD.

### Red Tests To Add First

1. `generate_chart()` success payload includes `figure_backend == "plotly"`
2. `generate_chart()` success payload includes `plotly_trace_count == 1`
3. existing assertions still hold:
   - bar returns `type == "bar"`
   - line returns `type == "scatter"`
   - line returns `mode == "lines+markers"`
4. registry invocation still returns schema-valid output with new fields

### Green Verification

After implementation:

- chart tool unit tests pass
- registry tests pass
- any analysis-runner tests touching `plotly_spec` still pass

## Runtime Evidence Requirements

To treat Plotly as truly grounded after this phase, the repository should be able to point to:

1. code evidence
   - `chart_tool.py` imports and uses Plotly directly
2. runtime evidence
   - chart payload includes `figure_backend = "plotly"`
   - chart payload includes `plotly_trace_count`
3. test evidence
   - chart tool and registry tests assert those fields

Only after those three layers exist should wording be upgraded from “Plotly-style” to “real Plotly-backed chart generation”.

## Risks

### Schema Drift Risk

Adding fields could break output validation if `GenerateChartOutput` is not updated in lockstep.

Mitigation:

- update schema first in the same implementation slice

### Consumer Compatibility Risk

Any change to `plotly_spec` structure could break `/demo` and existing tests.

Mitigation:

- preserve `plotly_spec` as the primary serialized artifact
- avoid changing the keys currently consumed by demo rendering

### Over-Scope Risk

It would be easy to expand this into frontend chart modernization.

Mitigation:

- keep all changes confined to the backend chart tool and its immediate contract/tests

## Success Criteria

This phase is successful when:

- Plotly is imported and used in `chart_tool.py`
- `plotly_spec` is generated from a real Plotly `Figure`
- the chart result explicitly exposes `figure_backend = "plotly"`
- tests validate both compatibility and runtime evidence
- documentation can truthfully describe Plotly as real library-backed chart generation
