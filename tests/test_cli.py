"""
Tests for the command-line interface.
"""

from __future__ import annotations
from typer.testing import CliRunner
from linux_assistant.cli.main import app
from unittest.mock import MagicMock, patch

runner = CliRunner()


class TestRunCommand:
    """Tests for `smart-linux run`."""

    def test_run_prints_stdout_on_success(self) -> None:
        result = runner.invoke(app, ["run", "echo hello"])
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_run_exits_zero_for_successful_command(self) -> None:
        result = runner.invoke(app, ["run", "pwd"])
        assert result.exit_code == 0

    def test_run_without_check_does_not_fail_on_nonzero_exit(self) -> None:
        result = runner.invoke(app, ["run", "ls /no-such-directory-xyz"])
        assert result.exit_code != 0  # exits with the command's real code

    def test_run_with_check_exits_with_real_command_exit_code(self) -> None:
        result = runner.invoke(app, ["run", "ls /no-such-directory-xyz", "--check"])
        assert result.exit_code == 2

    def test_run_rejects_empty_command_with_usage_error(self) -> None:
        result = runner.invoke(app, ["run", ""])
        assert result.exit_code == 2

    def test_run_respects_timeout_flag(self) -> None:
        result = runner.invoke(app, ["run", "sleep 5", "--timeout", "1"])
        assert result.exit_code == 124
        
class TestDoctorCommand:
    """Tests for `smart-linux doctor`."""

    def test_doctor_runs_and_reports_bash(self) -> None:
        result = runner.invoke(app, ["doctor"])
        assert "bash" in result.stdout

    def test_doctor_exit_code_is_zero_or_one(self) -> None:
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code in (0, 1)
        
class TestExplainCommand:
    """Tests for `smart-linux explain`."""

    def test_explain_fails_cleanly_without_api_key(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        result = runner.invoke(app, ["explain", "some error"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "GROQ_API_KEY" in result.output

    def test_explain_returns_explanation_on_success(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Mocked explanation."

        with patch(
            "linux_assistant.cli.main.Explainer"
        ) as MockExplainerClass:
            mock_instance = MockExplainerClass.return_value
            mock_instance.explain.return_value = "Mocked explanation."

            result = runner.invoke(app, ["explain", "some error"])

        assert result.exit_code == 0
        assert "Mocked explanation." in result.stdout