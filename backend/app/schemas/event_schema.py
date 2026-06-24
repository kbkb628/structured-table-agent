from typing import Any

from pydantic import BaseModel


class AnalysisEvent(BaseModel):
    event_id: str
    event_type: str
    node: str
    message: str
    payload: dict[str, Any]
    created_at: str


class AnalysisEventList(BaseModel):
    task_id: str
    events: list[AnalysisEvent]
