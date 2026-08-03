"""
Linux documentation lookup service.
"""

from __future__ import annotations

from linux_assistant.exceptions import DocumentationError, ValidationError
from linux_assistant.utils.logger import get_logger
from linux_assistant.utils.shell import capture_output, command_exists

logger = get_logger(__name__)


class DocumentationService:
    """
    Retrieve and format local Linux manual pages.
    """

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

        if not command_exists("man"):
            raise DocumentationError(
                "The 'man' command is not available on this system."
            )

        return capture_output(f"man {command}")