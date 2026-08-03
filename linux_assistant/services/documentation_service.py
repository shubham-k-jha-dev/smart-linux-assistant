"""
Linux documentation lookup service.
"""

from __future__ import annotations

import re

from linux_assistant.exceptions import DocumentationError, ValidationError
from linux_assistant.utils.logger import get_logger
from linux_assistant.utils.shell import capture_output, command_exists

logger = get_logger(__name__)


class DocumentationService:
    """
    Retrieve and format local Linux manual pages.
    """

    _IMPORTANT_SECTIONS = {
        "NAME",
        "SYNOPSIS",
        "DESCRIPTION",
        "OPTIONS",
        "EXAMPLES",
    }

    def get_documentation(self, command: str) -> str:
        """
        Retrieve documentation for a Linux command.
        """
        command = command.strip()

        if not command:
            raise ValidationError(
                "Command name cannot be empty."
            )

        logger.info(
            "Looking up documentation for '%s'.",
            command,
        )

        man_page = self._fetch_man_page(command)

        return self._extract_sections(man_page)

    def _fetch_man_page(self, command: str) -> str:
        """
        Retrieve the raw manual page.
        """
        if not command_exists("man"):
            raise DocumentationError(
                "The 'man' command is not available on this system."
            )

        return capture_output(f"man {command}")

    def _extract_sections(self, man_page: str) -> str:
        """
        Extract the most useful sections from a manual page.
        """
        output: list[str] = []

        current_section: str | None = None

        for line in man_page.splitlines():
            stripped = line.strip()

            if not stripped:
                if current_section:
                    output.append("")
                continue

            if re.fullmatch(r"[A-Z][A-Z ]+", stripped):
                if stripped in self._IMPORTANT_SECTIONS:
                    current_section = stripped
                    output.append(stripped)
                else:
                    current_section = None
                continue

            if current_section:
                output.append(line)

        if not output:
            return man_page

        return "\n".join(output).strip()