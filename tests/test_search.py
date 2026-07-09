"""
Unit tests for the Searcher service.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from linux_assistant.exceptions import ServiceError, ValidationError
from linux_assistant.services.search import Searcher


class TestSearcherSearch:
    """Tests for Searcher.search(), with the Groq API mocked out."""

    def _make_searcher_with_mocked_client(
        self, monkeypatch: pytest.MonkeyPatch, response_text: str | None
    ) -> Searcher:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")
        searcher = Searcher()

        mock_response = MagicMock()
        mock_response.choices[0].message.content = response_text
        searcher._client.chat.completions.create = MagicMock(
            return_value=mock_response
        )
        return searcher

    def test_search_raises_validation_error_on_empty_query(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        searcher = self._make_searcher_with_mocked_client(monkeypatch, "irrelevant")
        with pytest.raises(ValidationError):
            searcher.search("")

    def test_search_raises_validation_error_on_whitespace_query(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        searcher = self._make_searcher_with_mocked_client(monkeypatch, "irrelevant")
        with pytest.raises(ValidationError):
            searcher.search("     ")

    def test_search_returns_stripped_answer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        searcher = self._make_searcher_with_mocked_client(
            monkeypatch, "  $ find . -size +100M  "
        )
        result = searcher.search("find large files")
        assert result == "$ find . -size +100M"

    def test_search_raises_service_error_when_content_is_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        searcher = self._make_searcher_with_mocked_client(monkeypatch, None)
        with pytest.raises(ServiceError):
            searcher.search("some query")

    def test_search_wraps_api_exceptions_in_service_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")
        searcher = Searcher()
        searcher._client.chat.completions.create = MagicMock(
            side_effect=RuntimeError("network exploded")
        )
        with pytest.raises(ServiceError):
            searcher.search("some query")