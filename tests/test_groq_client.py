"""
Unit tests for shared Groq client utilities.
"""

from __future__ import annotations

from linux_assistant.utils.groq_client import MAX_INPUT_CHARACTERS, truncate_for_api


class TestTruncateForApi:
    """Tests for truncate_for_api()."""

    def test_returns_text_unchanged_when_within_limit(self) -> None:
        text = "a short string"
        assert truncate_for_api(text) == text

    def test_truncates_from_end_by_default(self) -> None:
        text = "a" * (MAX_INPUT_CHARACTERS + 500)
        result = truncate_for_api(text)
        assert len(result) <= MAX_INPUT_CHARACTERS
        assert result.startswith("a")
        assert result.endswith("...[truncated]...")

    def test_truncates_from_start_when_keep_end_is_true(self) -> None:
        text = "a" * 500 + "b" * (MAX_INPUT_CHARACTERS + 500)
        result = truncate_for_api(text, keep_end=True)
        assert len(result) <= MAX_INPUT_CHARACTERS
        assert result.startswith("...[truncated]...")
        assert result.endswith("b")

    def test_result_never_exceeds_max_length(self) -> None:
        text = "x" * 100_000
        result = truncate_for_api(text)
        assert len(result) <= MAX_INPUT_CHARACTERS