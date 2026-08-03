"""
Tests for the documentation lookup service.
"""

from __future__ import annotations

import pytest
import subprocess
from unittest.mock import MagicMock
from linux_assistant.exceptions import DocumentationError, ValidationError
from linux_assistant.services.documentation_service import DocumentationService


class TestDocumentationService:
    """Tests for DocumentationService."""

    def test_empty_command_is_rejected(self) -> None:
        service = DocumentationService()

        with pytest.raises(ValidationError):
            service.get_documentation("")

    def test_missing_man_binary_raises_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = DocumentationService()

        monkeypatch.setattr(
            "linux_assistant.services.documentation_service.command_exists",
            lambda _: False,
        )

        with pytest.raises(DocumentationError):
            service.get_documentation("ls")

    def test_fetches_ls_documentation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        service = DocumentationService()
        
        # Mock whatever execution mechanism it uses. Example for subprocess:
        mock_process = MagicMock()
        mock_process.stdout = "NAME\n       ls - list directory contents"
        mock_process.returncode = 0  # <--- ADD THIS LINE
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_process)

        output = service.get_documentation("ls")
        assert "NAME" in output