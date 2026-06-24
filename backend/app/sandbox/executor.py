import json
import shutil
import subprocess
import time
from pathlib import Path

from app.core import config


def _degraded_result(code: str, message: str, status: str = "degraded") -> dict:
    return {
        "status": status,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "elapsed_ms": 0,
        "parsed_output": {},
        "degraded": True,
        "error": {
            "code": code,
            "message": message,
            "suggested_fields": [],
        },
    }


def _classify_execution_failure(stderr: str) -> tuple[str, str]:
    lowered = (stderr or "").lower()
    if "syntaxerror" in lowered:
        return "SANDBOX_SYNTAX_ERROR", stderr.strip() or "Sandbox Python code has invalid syntax."
    if "importerror" in lowered or "modulenotfounderror" in lowered:
        return "SANDBOX_IMPORT_ERROR", stderr.strip() or "Sandbox code imports an unavailable module."
    if "permissionerror" in lowered or "read-only file system" in lowered:
        return "SANDBOX_PERMISSION_ERROR", stderr.strip() or "Sandbox code attempted a blocked filesystem operation."
    return "SANDBOX_EXECUTION_FAILED", stderr.strip() or "Sandbox execution failed."


class DockerSandboxExecutor:
    def docker_available(self) -> bool:
        docker_bin = shutil.which("docker")
        if docker_bin is None:
            return False
        try:
            result = subprocess.run(
                [docker_bin, "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0 and bool(result.stdout.strip())

    def _run_process(self, command: list[str], timeout_seconds: int) -> dict:
        started_at = time.perf_counter()
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "elapsed_ms": elapsed_ms,
        }

    def execute_python(self, code: str, mounted_files: list[dict], timeout_seconds: int) -> dict:
        if not config.DOCKER_SANDBOX_ENABLED:
            return _degraded_result("SANDBOX_DISABLED", "DockerSandbox is disabled by configuration.")
        if not self.docker_available():
            return _degraded_result("DOCKER_UNAVAILABLE", "Docker CLI is unavailable.")

        docker_bin = shutil.which("docker") or "docker"
        command = [
            docker_bin,
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            f"{config.DOCKER_SANDBOX_MEMORY_MB}m",
            "--cpus",
            str(config.DOCKER_SANDBOX_CPU_LIMIT),
            "--read-only",
        ]
        for mount in mounted_files:
            host_path = str(mount["host_path"]).replace("\\", "/")
            container_path = mount["container_path"]
            read_only = ":ro" if mount.get("read_only", False) else ""
            command.extend(["-v", f"{host_path}:{container_path}{read_only}"])
        command.extend([config.DOCKER_SANDBOX_IMAGE, "python", "-c", code])

        try:
            run_result = self._run_process(command, timeout_seconds)
        except TimeoutError:
            return _degraded_result(
                "SANDBOX_TIMEOUT",
                f"Sandbox execution timed out after {timeout_seconds}s.",
                status="timeout",
            )

        stdout = run_result.get("stdout", "")
        stderr = run_result.get("stderr", "")
        returncode = run_result.get("returncode")
        try:
            parsed_output = json.loads(stdout) if stdout.strip() else {}
        except json.JSONDecodeError:
            parsed_output = {"raw_stdout": stdout}

        return {
            "status": "completed" if returncode == 0 else "failed",
            "exit_code": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "elapsed_ms": int(run_result.get("elapsed_ms", 0) or 0),
            "parsed_output": parsed_output,
            "degraded": returncode != 0,
            "error": None
            if returncode == 0
            else {
                "code": _classify_execution_failure(stderr)[0],
                "message": _classify_execution_failure(stderr)[1],
                "suggested_fields": [],
            },
        }

    def execute_python_against_file(self, file_path: str | Path, code: str, timeout_seconds: int | None = None) -> dict:
        resolved_timeout = timeout_seconds or config.DOCKER_SANDBOX_TIMEOUT_SECONDS
        return self.execute_python(
            code=code,
            mounted_files=[
                {
                    "host_path": str(Path(file_path).resolve()),
                    "container_path": "/workspace/input/source.csv",
                    "read_only": True,
                }
            ],
            timeout_seconds=resolved_timeout,
        )
