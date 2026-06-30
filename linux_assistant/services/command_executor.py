"""
Service responsible for executing Linux commands.
"""

from __future__ import annotations
import subprocess
import time
from datetime import datetime
from linux_assistant.models import CommandResult
from linux_assistant.utils.logger import get_logger

logger = get_logger(__name__)


class CommandExecutor:
    """
    Execute Linux commands and return structured results.
    """
    def execute(self, command: str) -> CommandResult:
        """
        Execute a shell command.
        """
        logger.info("Executing command: %s", command)
        start_time = time.perf_counter()
        completed_process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
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
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
            executed_at=datetime.now(),
            duration_seconds=duration,
        )