"""
Tests for the command history repository.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from linux_assistant.exceptions import HistoryError
from linux_assistant.repositories.history_repository import (
    HISTORY_STDERR_SNIPPET_CHARS,
    HistoryRepository,
    MAX_HISTORY_ROWS,
)

TEST_CWD = "/home/testuser/project"


@pytest.fixture
def repo(tmp_path: Path) -> HistoryRepository:
    """Provide a HistoryRepository backed by a fresh temp file per test."""
    db_path = tmp_path / "test_history.db"
    return HistoryRepository(db_path=db_path)


class TestRecord:
    """Tests for HistoryRepository.record()."""

    def test_record_and_list_round_trip(self, repo: HistoryRepository) -> None:
        repo.record(
            command="echo hello",
            exit_code=0,
            duration_seconds=0.05,
            working_directory=TEST_CWD,
            stderr="",
        )
        entries = repo.list_recent()

        assert len(entries) == 1
        assert entries[0].command == "echo hello"
        assert entries[0].exit_code == 0
        assert entries[0].succeeded
        assert entries[0].duration_seconds == 0.05
        assert entries[0].working_directory == TEST_CWD

    def test_successful_command_does_not_store_stderr(
        self, repo: HistoryRepository
    ) -> None:
        repo.record(
            command="echo hello",
            exit_code=0,
            duration_seconds=0.05,
            working_directory=TEST_CWD,
            stderr="",
        )
        entries = repo.list_recent()

        assert entries[0].stderr_snippet is None

    def test_failed_command_stores_stderr_snippet(
        self, repo: HistoryRepository
    ) -> None:
        repo.record(
            command="ls /nope",
            exit_code=2,
            duration_seconds=0.02,
            working_directory=TEST_CWD,
            stderr="cannot access /nope",
        )
        entries = repo.list_recent()

        assert entries[0].failed
        assert entries[0].stderr_snippet == "cannot access /nope"

    def test_long_stderr_is_truncated_to_the_tail(
        self, repo: HistoryRepository
    ) -> None:
        long_stderr = "x" * (HISTORY_STDERR_SNIPPET_CHARS + 500)
        repo.record(
            command="some failing command",
            exit_code=1,
            duration_seconds=0.1,
            working_directory=TEST_CWD,
            stderr=long_stderr,
        )
        entries = repo.list_recent()

        assert entries[0].stderr_snippet is not None
        assert entries[0].stderr_snippet.endswith("x" * 50)
        assert len(entries[0].stderr_snippet) < len(long_stderr)

    def test_stdout_is_never_a_parameter(self, repo: HistoryRepository) -> None:
        # HistoryRepository.record() has no stdout parameter at all —
        # this test documents that guarantee structurally rather than
        # behaviorally, by asserting the signature has no such field.
        import inspect

        params = inspect.signature(repo.record).parameters
        assert "stdout" not in params


class TestListRecent:
    """Tests for HistoryRepository.list_recent()."""

    def test_returns_newest_first(self, repo: HistoryRepository) -> None:
        repo.record(
            command="first",
            exit_code=0,
            duration_seconds=0.01,
            working_directory=TEST_CWD,
            stderr="",
        )
        repo.record(
            command="second",
            exit_code=0,
            duration_seconds=0.01,
            working_directory=TEST_CWD,
            stderr="",
        )

        entries = repo.list_recent()

        assert entries[0].command == "second"
        assert entries[1].command == "first"

    def test_respects_limit(self, repo: HistoryRepository) -> None:
        for i in range(5):
            repo.record(
                command=f"command {i}",
                exit_code=0,
                duration_seconds=0.01,
                working_directory=TEST_CWD,
                stderr="",
            )

        entries = repo.list_recent(limit=2)

        assert len(entries) == 2

    def test_failures_only_filters_successful_commands(
        self, repo: HistoryRepository
    ) -> None:
        repo.record(
            command="good",
            exit_code=0,
            duration_seconds=0.01,
            working_directory=TEST_CWD,
            stderr="",
        )
        repo.record(
            command="bad",
            exit_code=1,
            duration_seconds=0.01,
            working_directory=TEST_CWD,
            stderr="oops",
        )

        entries = repo.list_recent(failures_only=True)

        assert len(entries) == 1
        assert entries[0].command == "bad"

    def test_empty_history_returns_empty_list(self, repo: HistoryRepository) -> None:
        assert repo.list_recent() == []


class TestPruning:
    """Tests for the FIFO row-cap enforced on every write."""

    def test_prunes_oldest_rows_beyond_max_history_rows(
        self, repo: HistoryRepository, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import linux_assistant.repositories.history_repository as history_module

        # This safely changes the value to 3 and auto-restores it later
        monkeypatch.setattr(history_module, "MAX_HISTORY_ROWS", 3)

        for i in range(5):
            repo.record(
                command=f"command {i}",
                exit_code=0,
                duration_seconds=0.01,
                working_directory=TEST_CWD,
                stderr="",
            )

        entries = repo.list_recent(limit=10)
        commands = [entry.command for entry in entries]

        assert len(entries) == 3
        assert "command 4" in commands
        assert "command 3" in commands
        assert "command 2" in commands
        assert "command 0" not in commands
        assert "command 1" not in commands


class TestClear:
    """Tests for HistoryRepository.clear()."""

    def test_clear_removes_all_entries(self, repo: HistoryRepository) -> None:
        repo.record(
            command="one",
            exit_code=0,
            duration_seconds=0.01,
            working_directory=TEST_CWD,
            stderr="",
        )
        repo.record(
            command="two",
            exit_code=0,
            duration_seconds=0.01,
            working_directory=TEST_CWD,
            stderr="",
        )

        repo.clear()

        assert repo.list_recent() == []