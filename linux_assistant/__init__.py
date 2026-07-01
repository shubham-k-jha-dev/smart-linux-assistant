"""
Expose shared utility functions for the application.
"""

from linux_assistant.utils.logger import get_logger
from linux_assistant.utils.shell import command_exists

__all__ = [
    "get_logger",
    "command_exists",
]