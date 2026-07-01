"""
Expose the public exception hierarchy for the application.
Importing exceptions from this package keeps call sites concise and
avoids exposing the internal module structure.
"""

from .base import (
    CommandExecutionError,
    CommandFailedError,
    CommandTimeoutError,
    ConfigurationError,
    RepositoryError,
    ServiceError,
    SmartLinuxAssistantError,
    ValidationError,
)

__all__ = [
    "SmartLinuxAssistantError",
    "ConfigurationError",
    "RepositoryError",
    "ServiceError",
    "ValidationError",
    "CommandExecutionError",
    "CommandTimeoutError",
    "CommandFailedError",
]