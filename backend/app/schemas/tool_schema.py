from typing import Any

from pydantic import BaseModel


class ToolError(BaseModel):
    code: str
    message: str
    suggested_fields: list[str] = []


class ToolResponse(BaseModel):
    success: bool
    tool_name: str
    data: dict[str, Any] | None
    summary: str
    error: ToolError | None
    metadata: dict[str, Any]
