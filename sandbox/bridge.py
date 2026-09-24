from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any


@dataclass(frozen=True)
class SandboxLimits:
    """Resource limits sent to the Rust sandbox."""

    max_instructions: int
    max_memory_bytes: int
    max_execution_time_ms: int

    def __post_init__(self) -> None:
        if self.max_instructions <= 0:
            raise ValueError(
                "max_instructions must be greater than zero."
            )

        if self.max_memory_bytes <= 0:
            raise ValueError(
                "max_memory_bytes must be greater than zero."
            )

        if self.max_execution_time_ms <= 0:
            raise ValueError(
                "max_execution_time_ms must be greater than zero."
            )


@dataclass(frozen=True)
class SandboxExecution:
    """Measured execution information."""

    instructions_used: int
    memory_used_bytes: int
    execution_time_ms: int


@dataclass(frozen=True)
class SandboxBridgeResult:
    """Result returned by the Rust sandbox."""

    success: bool
    status: str
    experiment_id: str
    candidate_id: str
    instructions_used: int
    memory_used_bytes: int
    execution_time_ms: int
    message: str


class SandboxBridge:
    """
    Python interface to the CARDINAL Rust sandbox.

    The bridge communicates through a JSON-lines protocol.
    It does not execute candidate code itself.
    """

    def __init__(
        self,
        executable: str | Path,
    ) -> None:
        self.executable = str(
            executable
        )

    def execute(
        self,
        *,
        experiment_id: str,
        candidate_id: str,
        limits: SandboxLimits,
        execution: SandboxExecution,
    ) -> SandboxBridgeResult:
        if not experiment_id:
            raise ValueError(
                "experiment_id cannot be empty."
            )

        if not candidate_id:
            raise ValueError(
                "candidate_id cannot be empty."
            )

        request = {
            "experiment_id": experiment_id,
            "candidate_id": candidate_id,
            "max_instructions": (
                limits.max_instructions
            ),
            "max_memory_bytes": (
                limits.max_memory_bytes
            ),
            "max_execution_time_ms": (
                limits.max_execution_time_ms
            ),
            "instructions_used": (
                execution.instructions_used
            ),
            "memory_used_bytes": (
                execution.memory_used_bytes
            ),
            "execution_time_ms": (
                execution.execution_time_ms
            ),
        }

        process = subprocess.run(
            [self.executable],
            input=json.dumps(request) + "\n",
            text=True,
            capture_output=True,
            check=False,
        )

        if process.returncode != 0:
            raise RuntimeError(
                "Rust sandbox process failed: "
                + process.stderr.strip()
            )

        output = process.stdout.strip()

        if not output:
            raise RuntimeError(
                "Rust sandbox returned no result."
            )

        try:
            payload: dict[str, Any] = (
                json.loads(output)
            )
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Rust sandbox returned invalid JSON."
            ) from error

        return SandboxBridgeResult(
            success=bool(
                payload["success"]
            ),
            status=str(
                payload["status"]
            ),
            experiment_id=str(
                payload["experiment_id"]
            ),
            candidate_id=str(
                payload["candidate_id"]
            ),
            instructions_used=int(
                payload["instructions_used"]
            ),
            memory_used_bytes=int(
                payload["memory_used_bytes"]
            ),
            execution_time_ms=int(
                payload["execution_time_ms"]
            ),
            message=str(
                payload["message"]
            ),
          )
