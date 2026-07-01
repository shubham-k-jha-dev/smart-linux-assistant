"""
Unit tests for shell utilities.
"""

from __future__ import annotations

import pytest

from linux_assistant.exceptions import ValidationError
from linux_assistant.utils.shell import command_exists


class TestCommandExists:
    """Tests for command_exists()."""

    def test_command_exists_returns_true_for_known_command(self) -> None:
        assert command_exists("ls") is True

    def test_command_exists_returns_false_for_unknown_command(self) -> None:
        assert command_exists("this-command-does-not-exist-xyz") is False

    def test_command_exists_raises_validation_error_on_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            command_exists("")

    def test_command_exists_raises_validation_error_on_whitespace_name(
        self,
    ) -> None:
        with pytest.raises(ValidationError):
            command_exists("     ")

    def test_command_exists_strips_whitespace_before_checking(self) -> None:
        assert command_exists("  ls  ") is True