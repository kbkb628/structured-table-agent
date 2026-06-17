DATASET_PROFILED = "dataset_profiled"
TASK_CREATED = "task_created"
RAG_RETRIEVED = "rag_retrieved"
GOAL_UNDERSTOOD = "goal_understood"
PLAN_GENERATED = "plan_generated"
FIELDS_MATCHED = "fields_matched"
TOOL_CALLED = "tool_called"
TOOL_SUCCEEDED = "tool_succeeded"
TOOL_FAILED = "tool_failed"
CHART_GENERATED = "chart_generated"
CHART_FAILED = "chart_failed"
REPORT_GENERATED = "report_generated"
EVAL_FINISHED = "eval_finished"
TASK_COMPLETED = "task_completed"
TASK_FAILED = "task_failed"

STARTUP_TRACE_EVENTS = (
    TASK_CREATED,
    DATASET_PROFILED,
    RAG_RETRIEVED,
    GOAL_UNDERSTOOD,
    PLAN_GENERATED,
)

REQUIRED_TRACE_EVENTS = (
    TASK_CREATED,
    FIELDS_MATCHED,
    TOOL_SUCCEEDED,
    REPORT_GENERATED,
    TASK_COMPLETED,
)
