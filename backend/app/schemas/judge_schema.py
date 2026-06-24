from typing import Literal

from pydantic import BaseModel, Field


class JudgeDimension(BaseModel):
    score: float
    verdict: str
    rationale: str


class JudgeResult(BaseModel):
    judge_summary: str
    judge_status: Literal["ok", "degraded"]
    dimensions: dict[str, JudgeDimension]
    issue_count: int
    issues: list[str] = Field(default_factory=list)
    degraded: bool = False
