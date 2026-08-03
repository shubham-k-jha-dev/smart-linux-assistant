"""
Shell-level utilities for checking the system environment.
"""

from __future__ import annotations

import shutil
import subprocess
from linux_assistant.exceptions import DocumentationError, ValidationError
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

def capture_output(
    command: str,
    *,
    timeout: int = 10,
) -> str:
    """
    Execute a shell command and return its standard output.

    This utility is intended for internal shell queries such as
    retrieving manual pages or checking system metadata. It is not
    intended for executing arbitrary user commands.

    Args:
        command:
            Shell command to execute.

        timeout:
            Maximum execution time in seconds.

    Returns:
        Standard output produced by the command.

    Raises:
        ValidationError:
            If the command is empty.

        DocumentationError:
            If the command cannot be executed or exits with a
            non-zero status.
    """
    command = command.strip()

    if not command:
        raise ValidationError("Command cannot be empty.")

    logger.info("Capturing output from: %s", command)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except OSError as exc:
        logger.error("Failed to execute '%s': %s", command, exc)
        raise DocumentationError(
            f"Unable to execute '{command}'."
        ) from exc

    except subprocess.TimeoutExpired as exc:
        logger.error("Command timed out: %s", command)
        raise DocumentationError(
            f"Command '{command}' timed out."
        ) from exc

    if result.returncode != 0:
        logger.info(
            "Command returned exit code %d.",
            result.returncode,
        )
        raise DocumentationError(
            result.stderr.strip() or "Command failed."
        )

    return result.stdout.strip()