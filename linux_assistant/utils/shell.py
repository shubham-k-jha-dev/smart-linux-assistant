"""
Shell-level utilities for checking the system environment.
"""

from __future__ import annotations

import shutil

from linux_assistant.exceptions import ValidationError
from linux_assistant.utils.logger import get_logger

logger = get_logger(__name__)


def command_exists(name: str) -> bool:
    """
    Check whether a command is available on the system's PATH.
    """
    name = name.strip()

    if not name:
        raise ValidationError("Command name cannot be empty.")

    found_path = shutil.which(name)

    if found_path is None:
        logger.info("Command '%s' was not found on PATH.", name)
        return False

    logger.info("Command '%s' found at '%s'.", name, found_path)
    return True