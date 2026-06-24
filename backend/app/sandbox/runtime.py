from app.core import config
from app.sandbox.executor import DockerSandboxExecutor


def describe_sandbox_runtime() -> dict:
    executor = DockerSandboxExecutor()
    return {
        "enabled": config.DOCKER_SANDBOX_ENABLED,
        "docker_available": executor.docker_available(),
        "image": config.DOCKER_SANDBOX_IMAGE,
        "network_disabled": config.DOCKER_SANDBOX_NETWORK_DISABLED,
        "timeout_seconds": config.DOCKER_SANDBOX_TIMEOUT_SECONDS,
        "memory_limit_mb": config.DOCKER_SANDBOX_MEMORY_MB,
        "cpu_limit": config.DOCKER_SANDBOX_CPU_LIMIT,
    }
