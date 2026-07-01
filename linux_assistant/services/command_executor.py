"""
Execute Linux commands and return structured results.
"""

from __future__ import annotations

import subprocess
import time
from datetime import datetime, timezone
from linux_assistant.exceptions import ValidationError
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

        completed_process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

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