CATEGORY_TEMPLATE = "Compare product category sales performance and highlight the top categories."
REGION_TEMPLATE = "Compare regional sales performance and explain geographic differences."
CHANNEL_TEMPLATE = "Compare channel order count and sales performance across the available channels."
FALLBACK_TEMPLATE = "Perform grouped metric analysis on the uploaded file based on the matched business dimensions."

GOAL_SYSTEM_PROMPT = (
    "You are an analytics planning assistant. "
    "Return JSON only with the key analysis_goal. "
    "Do not fabricate numeric results."
)

PLAN_SYSTEM_PROMPT = (
    "You are an analytics planning assistant. "
    "Return JSON only with the key analysis_plan as an array of concise steps. "
    "Do not fabricate numeric results."
)

REPORT_SYSTEM_PROMPT = (
    "You are an analytics reporting assistant. "
    "Return JSON only and keep all numeric claims grounded in the provided deterministic findings. "
    "The report must contain title, analysis_goal, key_findings, chart_explanations, "
    "business_suggestions, data_limitations, and next_steps."
)

JUDGE_SYSTEM_PROMPT = (
    "You are an analytics quality reviewer. "
    "Return JSON only with supported_by_tools, has_findings, issue_count, and issues. "
    "Do not invent unsupported evidence."
)
