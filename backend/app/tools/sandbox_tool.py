from app.sandbox.executor import DockerSandboxExecutor
from app.sandbox.templates import build_sandbox_template_code
from app.schemas.tool_schema import ToolError
from app.schemas.tool_schema import ToolResponse
from app.storage.file_store import get_file_record


def execute_in_docker_sandbox(
    file_id: str,
    python_code: str | None = None,
    template_name: str | None = None,
    timeout_seconds: int | None = None,
) -> dict:
    record = get_file_record(file_id)
    if record is None:
        return {
            "status": "failed",
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "elapsed_ms": 0,
            "parsed_output": {},
            "degraded": True,
            "error": {
                "code": "FILE_NOT_FOUND",
                "message": f"Unknown file_id: {file_id}",
                "suggested_fields": [],
            },
        }
    resolved_code = python_code or build_sandbox_template_code(template_name or "")
    return DockerSandboxExecutor().execute_python_against_file(
        file_path=record.stored_path,
        code=resolved_code,
        timeout_seconds=timeout_seconds,
    )


def advanced_code_execution(
    file_id: str,
    python_code: str | None = None,
    template_name: str | None = None,
    timeout_seconds: int | None = None,
) -> ToolResponse:
    sandbox_kwargs = {
        "file_id": file_id,
        "python_code": python_code,
        "timeout_seconds": timeout_seconds,
    }
    if template_name is not None:
        sandbox_kwargs["template_name"] = template_name
    result = execute_in_docker_sandbox(
        **sandbox_kwargs,
    )
    error_payload = result.get("error")
    return ToolResponse(
        success=result["status"] == "completed",
        tool_name="advanced_code_execution",
        data=result,
        summary="sandbox execution completed" if result["status"] == "completed" else "sandbox execution degraded",
        error=(
            ToolError(
                code=error_payload["code"],
                message=error_payload["message"],
                suggested_fields=error_payload.get("suggested_fields", []),
            )
            if error_payload
            else None
        ),
        metadata={
            "elapsed_ms": int(result.get("elapsed_ms", 0) or 0),
            "sandbox_status": result["status"],
        },
    )
