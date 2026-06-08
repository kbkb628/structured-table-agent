from pydantic import BaseModel


class KeyFinding(BaseModel):
    finding: str
    evidence: str
    source_tool: str


class FinalReport(BaseModel):
    title: str
    analysis_goal: str
    key_findings: list[KeyFinding]
    chart_explanations: list[str]
    business_suggestions: list[str]
    data_limitations: list[str]
    next_steps: list[str]
