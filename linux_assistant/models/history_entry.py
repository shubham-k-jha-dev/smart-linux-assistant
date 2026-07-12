"""
Domain model representing a single recorded entry in the command
history store.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class HistoryEntry:
    """
    Store a single past command invocation as recorded by
    HistoryRepository.

        id:
            Auto-incrementing primary key assigned by the store.

        command:
            The exact command that was executed.

        exit_code:
            Exit status returned by the operating system.

        executed_at:
            Timestamp indicating when the command finished executing.

        duration_seconds:
            Time taken to execute the command, in seconds.

        working_directory:
            Absolute path of the directory the command was run from.

        stderr_snippet:
            A truncated tail of the command's stderr output, captured
            only when the command failed (exit_code != 0). None when
            the command succeeded, to avoid storing unnecessary data.
    """

    id: int
    command: str
    exit_code: int
    executed_at: datetime
    duration_seconds: float
    working_directory: str
    stderr_snippet: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        return not self.succeeded