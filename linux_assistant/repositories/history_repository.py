"""
Repository for persisting and querying command execution history.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from linux_assistant.config.settings import settings
from linux_assistant.exceptions import HistoryError
from linux_assistant.models import HistoryEntry

# Maximum characters of stderr to retain for a failed command. Errors
# typically surface at the end of their output (e.g. the final lines
# of a stack trace), so the tail is kept rather than the head.
HISTORY_STDERR_SNIPPET_CHARS = 1000

# Hard cap on the number of rows retained in the history table. Once
# exceeded, the oldest rows are pruned on every write. This bounds
# the database's size indefinitely without a background job or
# time-based expiry, which would be unreliable for sporadic CLI use.
MAX_HISTORY_ROWS = 5000

HISTORY_DB_FILE = settings.data_directory / "history.db"


def _truncate_stderr(stderr: str) -> str:
    """
    Truncate stderr to the last HISTORY_STDERR_SNIPPET_CHARS
    characters, prefixing a marker if truncation occurred.
    """
    if len(stderr) <= HISTORY_STDERR_SNIPPET_CHARS:
        return stderr
    return "...[truncated]... " + stderr[-HISTORY_STDERR_SNIPPET_CHARS:]


class HistoryRepository:
    """
    Store and retrieve command execution history in a local SQLite
    database. Only command metadata and, for failures, a truncated
    stderr snippet are stored — stdout is never persisted, since it
    frequently contains sensitive data (secrets, keys, credentials)
    and can grow unboundedly for commands like `find` or `cat`.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or HISTORY_DB_FILE

    def _connect(self) -> sqlite3.Connection:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self._db_path)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT NOT NULL,
                    exit_code INTEGER NOT NULL,
                    executed_at TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    working_directory TEXT NOT NULL,
                    stderr_snippet TEXT
                )
                """
            )
            return connection
        except sqlite3.Error as exc:
            raise HistoryError(f"Could not open history database: {exc}") from exc

    def record(
        self,
        *,
        command: str,
        exit_code: int,
        duration_seconds: float,
        working_directory: str,
        stderr: str,
    ) -> None:
        """
        Record a single command invocation, then prune the oldest
        rows beyond MAX_HISTORY_ROWS.

        Args:
            command: The exact command that was executed.
            exit_code: The command's exit status.
            duration_seconds: Time taken to execute the command.
            working_directory: Absolute path the command was run from.
            stderr: The command's raw stderr output. Only stored
                (truncated) when exit_code is non-zero; ignored
                otherwise.
        """
        stderr_snippet = _truncate_stderr(stderr) if exit_code != 0 and stderr else None
        executed_at = datetime.now(timezone.utc).isoformat()

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO history (
                        command, exit_code, executed_at, duration_seconds,
                        working_directory, stderr_snippet
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        command,
                        exit_code,
                        executed_at,
                        duration_seconds,
                        working_directory,
                        stderr_snippet,
                    ),
                )
                connection.execute(
                    """
                    DELETE FROM history
                    WHERE id NOT IN (
                        SELECT id FROM history ORDER BY id DESC LIMIT ?
                    )
                    """,
                    (MAX_HISTORY_ROWS,),
                )
        except sqlite3.Error as exc:
            raise HistoryError(f"Could not record command history: {exc}") from exc

    def list_recent(
        self, *, limit: int = 20, failures_only: bool = False
    ) -> list[HistoryEntry]:
        """
        Return the most recent history entries, newest first.

        Args:
            limit: Maximum number of entries to return.
            failures_only: If True, only include entries with a
                non-zero exit code.
        """
        query = (
            "SELECT id, command, exit_code, executed_at, duration_seconds, "
            "working_directory, stderr_snippet FROM history"
        )
        if failures_only:
            query += " WHERE exit_code != 0"
        query += " ORDER BY id DESC LIMIT ?"

        try:
            with self._connect() as connection:
                rows = connection.execute(query, (limit,)).fetchall()
        except sqlite3.Error as exc:
            raise HistoryError(f"Could not read command history: {exc}") from exc

        return [
            HistoryEntry(
                id=row[0],
                command=row[1],
                exit_code=row[2],
                executed_at=datetime.fromisoformat(row[3]),
                duration_seconds=row[4],
                working_directory=row[5],
                stderr_snippet=row[6],
            )
            for row in rows
        ]

    def clear(self) -> None:
        """
        Permanently delete all recorded history entries.
        """
        try:
            with self._connect() as connection:
                connection.execute("DELETE FROM history")
        except sqlite3.Error as exc:
            raise HistoryError(f"Could not clear command history: {exc}") from exc