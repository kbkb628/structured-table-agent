from fastapi import APIRouter
from pydantic import BaseModel, field_validator, model_validator

from app.core import config
from app.sandbox.templates import build_sandbox_template_code
from app.sandbox.store import get_latest_sandbox_execution
from app.sandbox.store import record_sandbox_execution
from app.sandbox.runtime import describe_sandbox_runtime
from app.tools.sandbox_tool import execute_in_docker_sandbox


router = APIRouter(tags=["sandbox"])


class SandboxExecutionRequest(BaseModel):
    file_id: str
    python_code: str | None = None
    template_name: str | None = None
    timeout_seconds: int | None = None

    @model_validator(mode="after")
    def validate_execution_mode(self):
        if bool(self.python_code) == bool(self.template_name):
            raise ValueError("Provide exactly one of python_code or template_name.")
        return self

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout_seconds(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 1 or value > config.DOCKER_SANDBOX_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds exceeds the configured sandbox limit.")
        return value


@router.get("/api/sandbox/status")
def get_sandbox_status() -> dict:
    return {
        **describe_sandbox_runtime(),
        "latest_execution": get_latest_sandbox_execution(),
    }


@router.post("/api/sandbox/execute")
def run_sandbox_execution(request: SandboxExecutionRequest) -> dict:
    python_code = request.python_code or build_sandbox_template_code(request.template_name or "")
    response = execute_in_docker_sandbox(
        file_id=request.file_id,
        python_code=python_code,
        timeout_seconds=request.timeout_seconds,
    )
    record_sandbox_execution(
        file_id=request.file_id,
        request_payload={**request.model_dump(), "python_code": python_code},
        response_payload=response,
        execution_source="sandbox_api",
    )
    return response
