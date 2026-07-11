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
    HistoryError,
    MissingAPIKeyError,
    RateLimitError,
    RepositoryError,
    ServiceError,
    SmartLinuxAssistantError,
    ValidationError,
)

__all__ = [
    "SmartLinuxAssistantError",
    "ConfigurationError",
    "RepositoryError",
    "HistoryError",
    "ServiceError",
    "ValidationError",
    "CommandExecutionError",
    "CommandTimeoutError",
    "CommandFailedError",
    "MissingAPIKeyError",
    "RateLimitError",
]