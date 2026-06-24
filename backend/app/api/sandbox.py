from fastapi import APIRouter
from pydantic import BaseModel

from app.sandbox.runtime import describe_sandbox_runtime
from app.tools.sandbox_tool import execute_in_docker_sandbox


router = APIRouter(tags=["sandbox"])


class SandboxExecutionRequest(BaseModel):
    file_id: str
    python_code: str
    timeout_seconds: int | None = None


@router.get("/api/sandbox/status")
def get_sandbox_status() -> dict:
    return describe_sandbox_runtime()


@router.post("/api/sandbox/execute")
def run_sandbox_execution(request: SandboxExecutionRequest) -> dict:
    return execute_in_docker_sandbox(
        file_id=request.file_id,
        python_code=request.python_code,
        timeout_seconds=request.timeout_seconds,
    )
