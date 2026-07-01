"""
Unit tests for CommandExecutor.
"""

from __future__ import annotations
from unittest.mock import patch
import pytest
from linux_assistant.exceptions import CommandExecutionError, CommandTimeoutError, ValidationError
from linux_assistant.models import CommandResult
from linux_assistant.services.command_executor import CommandExecutor


class TestCommandExecutorValidation:
    """Tests for input validation before execution."""

    def test_execute_raises_validation_error_on_empty_command(self) -> None:
        executor = CommandExecutor()
        with pytest.raises(ValidationError):
            executor.execute("")

    def test_execute_raises_validation_error_on_whitespace_command(self) -> None:
        executor = CommandExecutor()
        with pytest.raises(ValidationError):
            executor.execute("     ")

    def test_execute_raises_validation_error_on_zero_timeout(self) -> None:
        executor = CommandExecutor()
        with pytest.raises(ValidationError):
            executor.execute("pwd", timeout=0)

    def test_execute_raises_validation_error_on_negative_timeout(self) -> None:
        executor = CommandExecutor()
        with pytest.raises(ValidationError):
            executor.execute("pwd", timeout=-5)


class TestCommandExecutorSuccess:
    """Tests for successful command execution."""

    def test_execute_returns_command_result(self) -> None:
        executor = CommandExecutor()
        result = executor.execute("pwd")
        assert isinstance(result, CommandResult)

    def test_execute_succeeded_is_true_for_zero_exit_code(self) -> None:
        executor = CommandExecutor()
        result = executor.execute("pwd")
        assert result.succeeded is True

    def test_execute_failed_is_true_for_nonzero_exit_code(self) -> None:
        executor = CommandExecutor()
        result = executor.execute("ls /no-such-directory-xyz")
        assert result.failed is True

    def test_execute_captures_stdout(self) -> None:
        executor = CommandExecutor()
        result = executor.execute("echo hello")
        assert result.stdout == "hello"

    def test_execute_strips_leading_and_trailing_whitespace_from_command(
        self,
    ) -> None:
        executor = CommandExecutor()
        result = executor.execute("  echo hello  ")
        assert result.command == "echo hello"


class TestCommandExecutorFailureWrapping:
    """Tests that subprocess-level failures are wrapped in custom exceptions."""

    def test_execute_raises_command_timeout_error_on_timeout(self) -> None:
        executor = CommandExecutor()
        with pytest.raises(CommandTimeoutError):
            executor.execute("sleep 5", timeout=1)

    def test_execute_raises_command_execution_error_on_os_error(self) -> None:
        executor = CommandExecutor()
        with patch(
            "linux_assistant.services.command_executor.subprocess.run",
            side_effect=OSError("no such shell"),
        ):
            with pytest.raises(CommandExecutionError):
                executor.execute("pwd")

    def test_command_timeout_error_is_a_command_execution_error(self) -> None:
        """CommandTimeoutError must be catchable as CommandExecutionError."""
        executor = CommandExecutor()
        with pytest.raises(CommandExecutionError):
            executor.execute("sleep 5", timeout=1)
