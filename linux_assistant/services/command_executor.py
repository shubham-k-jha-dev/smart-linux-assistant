"""
Execute Linux commands and return structured results.
"""

from __future__ import annotations

import subprocess
import time
from datetime import datetime, timezone
from linux_assistant.exceptions import ValidationError, CommandExecutionError, CommandTimeoutError
from linux_assistant.models import CommandResult
from linux_assistant.utils.logger import get_logger

logger = get_logger(__name__)


class CommandExecutor:
    """
    Execute Linux shell commands.
    """

    def execute(
        self,
        command: str,
        timeout: int = 30,
    ) -> CommandResult:
        """
        Execute a Linux command.
        """
        command = command.strip()
        
        if not command:
            raise ValidationError("Command cannot be empty.")
        
        if timeout <= 0:
            raise ValidationError("Timeout must be greater than zero.")
        logger.info("Executing command: %s", command)

        start_time = time.perf_counter()
        try:
            completed_process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - start_time
            logger.error(
                "Command timed out after %.3f seconds: %s",
                duration,
                command,
            )
            raise CommandTimeoutError(
                f"Command '{command}' timed out after {timeout} seconds."
            ) from exc
        except OSError as exc:
            duration = time.perf_counter() - start_time
            logger.error(
                "Command could not be executed: %s (%s)",
                command,
                exc,
            )
            raise CommandExecutionError(
                f"Command '{command}' could not be executed: {exc}"
            ) from exc
            
        duration = time.perf_counter() - start_time

        logger.info(
            "Command finished with exit code %d in %.3f seconds.",
            completed_process.returncode,
            duration,
        )

        return CommandResult(
            command=command,
            exit_code=completed_process.returncode,
            stdout=completed_process.stdout.strip(),
            stderr=completed_process.stderr.strip(),
            executed_at=datetime.now(timezone.utc),
            duration_seconds=duration,
        )