"""
Tests for the command-line interface.
"""

from __future__ import annotations
import os
import pytest
from typer.testing import CliRunner
from linux_assistant.cli.main import app
from unittest.mock import MagicMock, patch

runner = CliRunner()

@pytest.fixture(autouse=True)
def _mock_history_repository():
    """
    Prevent every CLI test in this file from writing to the real,
    on-disk history database. Autouse means this applies to every
    test automatically, with no per-test opt-in required.
    """
    with patch("linux_assistant.cli.main.HistoryRepository") as MockHistoryRepo:
        yield MockHistoryRepo
        
        
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
    
    def test_run_without_suggest_fix_flag_does_not_invoke_explainer(self) -> None:
        with patch("linux_assistant.cli.main.Explainer") as MockExplainerClass:
            result = runner.invoke(app, ["run", "ls /no-such-directory-xyz"])

        MockExplainerClass.assert_not_called()
        assert result.exit_code != 0

    def test_run_suggest_fix_prints_suggestion_on_failure(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")

        with patch("linux_assistant.cli.main.Explainer") as MockExplainerClass:
            mock_instance = MockExplainerClass.return_value
            mock_instance.suggest_fix.return_value = "ls /correct-directory"

            result = runner.invoke(
                app, ["run", "ls /no-such-directory-xyz", "--check", "--suggest-fix"]
            )

        assert "ls /correct-directory" in result.output

    def test_run_suggest_fix_preserves_original_exit_code(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")

        with patch("linux_assistant.cli.main.Explainer") as MockExplainerClass:
            mock_instance = MockExplainerClass.return_value
            mock_instance.suggest_fix.return_value = "ls /correct-directory"

            result = runner.invoke(
                app, ["run", "ls /no-such-directory-xyz", "--check", "--suggest-fix"]
            )

        assert result.exit_code == 2  # real `ls` failure code, unchanged by suggestion

    def test_run_suggest_fix_handles_missing_api_key_gracefully(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        result = runner.invoke(
            app,
            ["run", "ls /no-such-directory-xyz", "--check", "--suggest-fix"],
            catch_exceptions=False,
        )

        assert result.exit_code == 2  # still the real exit code, not a crash
        assert "GROQ_API_KEY" in result.output

    def test_run_suggest_fix_reports_no_confident_fix(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")

        with patch("linux_assistant.cli.main.Explainer") as MockExplainerClass:
            mock_instance = MockExplainerClass.return_value
            mock_instance.suggest_fix.return_value = None

            result = runner.invoke(
                app, ["run", "ls /no-such-directory-xyz", "--check", "--suggest-fix"]
            )

        assert result.exit_code == 2
        assert "No confident fix" in result.output
        
    def test_run_suggest_fix_without_check_is_rejected(self) -> None:
        result = runner.invoke(app, ["run", "echo hello", "--suggest-fix"])
        assert result.exit_code == 2
        assert "--check" in result.output
        
    def test_run_records_history_on_success(self) -> None:
        with patch("linux_assistant.cli.main.HistoryRepository") as MockHistoryRepo:
            mock_instance = MockHistoryRepo.return_value
            result = runner.invoke(app, ["run", "echo hello"])

        assert result.exit_code == 0
        mock_instance.record.assert_called_once()
        call_kwargs = mock_instance.record.call_args.kwargs
        assert call_kwargs["command"] == "echo hello"
        assert call_kwargs["exit_code"] == 0

    def test_run_records_history_on_failure(self) -> None:
        with patch("linux_assistant.cli.main.HistoryRepository") as MockHistoryRepo:
            mock_instance = MockHistoryRepo.return_value
            result = runner.invoke(app, ["run", "ls /no-such-directory-xyz", "--check"])

        assert result.exit_code == 2
        mock_instance.record.assert_called_once()
        call_kwargs = mock_instance.record.call_args.kwargs
        assert call_kwargs["exit_code"] == 2

    def test_run_respects_history_opt_out_env_var(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("SMART_LINUX_NO_HISTORY", "1")

        with patch("linux_assistant.cli.main.HistoryRepository") as MockHistoryRepo:
            result = runner.invoke(app, ["run", "echo hello"])

        assert result.exit_code == 0
        MockHistoryRepo.assert_not_called()

    def test_run_does_not_crash_when_history_recording_fails(self) -> None:
        with patch("linux_assistant.cli.main.HistoryRepository") as MockHistoryRepo:
            from linux_assistant.exceptions import HistoryError

            MockHistoryRepo.return_value.record.side_effect = HistoryError("disk full")
            result = runner.invoke(app, ["run", "echo hello"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "hello" in result.output
        
    def test_run_records_history_on_success(self, _mock_history_repository) -> None:
        mock_instance = _mock_history_repository.return_value
        result = runner.invoke(app, ["run", "echo hello"])

        assert result.exit_code == 0
        mock_instance.record.assert_called_once()
        call_kwargs = mock_instance.record.call_args.kwargs
        assert call_kwargs["command"] == "echo hello"
        assert call_kwargs["exit_code"] == 0

    def test_run_records_history_on_failure(self, _mock_history_repository) -> None:
        mock_instance = _mock_history_repository.return_value
        result = runner.invoke(app, ["run", "ls /no-such-directory-xyz", "--check"])

        assert result.exit_code == 2
        mock_instance.record.assert_called_once()
        call_kwargs = mock_instance.record.call_args.kwargs
        assert call_kwargs["exit_code"] == 2

    def test_run_respects_history_opt_out_env_var(
        self, _mock_history_repository, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("SMART_LINUX_NO_HISTORY", "1")
        result = runner.invoke(app, ["run", "echo hello"])

        assert result.exit_code == 0
        _mock_history_repository.assert_not_called()

    def test_run_does_not_crash_when_history_recording_fails(
        self, _mock_history_repository
    ) -> None:
        from linux_assistant.exceptions import HistoryError

        _mock_history_repository.return_value.record.side_effect = HistoryError("disk full")
        result = runner.invoke(app, ["run", "echo hello"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "hello" in result.output
        
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
        
class TestFixCommand:
    """Tests for `smart-linux fix`."""

    def test_fix_reports_success_when_command_succeeds(self) -> None:
        result = runner.invoke(app, ["fix", "echo hello"])
        assert result.exit_code == 0
        assert "nothing to fix" in result.output

    def test_fix_fails_cleanly_without_api_key(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        result = runner.invoke(
            app, ["fix", "ls /no-such-directory-xyz"], catch_exceptions=False
        )
        assert result.exit_code == 1
        assert "GROQ_API_KEY" in result.output

    def test_fix_prints_suggestion_on_failure(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")

        with patch("linux_assistant.cli.main.Explainer") as MockExplainerClass:
            mock_instance = MockExplainerClass.return_value
            mock_instance.suggest_fix.return_value = "git status"

            result = runner.invoke(app, ["fix", "gti status"])

        assert result.exit_code == 1
        assert "git status" in result.output

    def test_fix_reports_no_fix_available(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")

        with patch("linux_assistant.cli.main.Explainer") as MockExplainerClass:
            mock_instance = MockExplainerClass.return_value
            mock_instance.suggest_fix.return_value = None

            result = runner.invoke(app, ["fix", "ls /no-such-directory-xyz"])

        assert result.exit_code == 1
        assert "No confident fix" in result.output
        
class TestSearchCommand:
    """Tests for `smart-linux search`."""

    def test_search_fails_cleanly_without_api_key(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        result = runner.invoke(
            app, ["search", "find large files"], catch_exceptions=False
        )
        assert result.exit_code == 1
        assert "GROQ_API_KEY" in result.output

    def test_search_returns_answer_on_success(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")

        with patch("linux_assistant.cli.main.Searcher") as MockSearcherClass:
            mock_instance = MockSearcherClass.return_value
            mock_instance.search.return_value = "$ find . -size +100M"

            result = runner.invoke(app, ["search", "find large files"])

        assert result.exit_code == 0
        assert "find . -size +100M" in result.output

    def test_search_rejects_empty_query(self) -> None:
        result = runner.invoke(app, ["search", ""])
        assert result.exit_code == 2
        
class TestVerboseLogging:
    """Tests for the global --verbose flag and console log suppression."""

    def test_run_is_quiet_by_default(self) -> None:
        result = runner.invoke(app, ["run", "echo hello"])
        assert result.exit_code == 0
        assert "hello" in result.output

    def test_verbose_flag_unlocks_console_handler_level(self) -> None:
        from linux_assistant.utils.logger import _console_handlers
        import logging

        result = runner.invoke(app, ["--verbose", "run", "echo hello"])
        assert result.exit_code == 0
        assert all(h.level == logging.INFO for h in _console_handlers)

    def test_default_state_suppresses_console_handler_level(self) -> None:
        from linux_assistant.utils.logger import _console_handlers
        import logging

        result = runner.invoke(app, ["run", "echo hello"])
        assert result.exit_code == 0
        assert all(h.level > logging.INFO for h in _console_handlers)