"""
Domain model representing the result of a Linux command.

This model acts as the common language between different parts of
the application. Whether a command is executed by the CLI, collected
by a background daemon, or later exposed through a FastAPI endpoint,
its outcome should be represented using this object.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class CommandResult:
    """
    Store the outcome of a single command execution.
        command:
            The exact command that was executed.

        exit_code:
            Exit status returned by the operating system.

        stdout:
            Standard output produced by the command.

        stderr:
            Standard error produced by the command.

        executed_at:
            Timestamp indicating when the command finished executing.
        duration_seconds:
            Time taken to execute the command, in seconds.
    """

    command: str
    exit_code: int
    stdout: str
    stderr: str
    executed_at: datetime
    duration_seconds: float

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        return not self.succeeded