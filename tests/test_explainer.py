"""
Unit tests for the Explainer service.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from linux_assistant.exceptions import MissingAPIKeyError, ServiceError, ValidationError
from linux_assistant.services.explainer import Explainer


class TestExplainerInitialization:
    """Tests for Explainer construction and API key handling."""

    def test_raises_missing_api_key_error_when_env_var_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(MissingAPIKeyError):
            Explainer()

    def test_constructs_successfully_when_env_var_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")
        explainer = Explainer()
        assert explainer is not None


class TestExplainerExplain:
    """Tests for Explainer.explain(), with the Groq API mocked out."""

    def _make_explainer_with_mocked_client(
        self, monkeypatch: pytest.MonkeyPatch, response_text: str | None
    ) -> Explainer:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")
        explainer = Explainer()

        mock_response = MagicMock()
        mock_response.choices[0].message.content = response_text
        explainer._client.chat.completions.create = MagicMock(
            return_value=mock_response
        )
        return explainer

    def test_explain_raises_validation_error_on_empty_text(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        explainer = self._make_explainer_with_mocked_client(
            monkeypatch, "irrelevant"
        )
        with pytest.raises(ValidationError):
            explainer.explain("")

    def test_explain_returns_stripped_response_text(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        explainer = self._make_explainer_with_mocked_client(
            monkeypatch, "  This is the explanation.  "
        )
        result = explainer.explain("some error")
        assert result == "This is the explanation."

    def test_explain_raises_service_error_when_content_is_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        explainer = self._make_explainer_with_mocked_client(monkeypatch, None)
        with pytest.raises(ServiceError):
            explainer.explain("some error")

    def test_explain_wraps_api_exceptions_in_service_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-testing")
        explainer = Explainer()
        explainer._client.chat.completions.create = MagicMock(
            side_effect=RuntimeError("network exploded")
        )
        with pytest.raises(ServiceError):
            explainer.explain("some error")