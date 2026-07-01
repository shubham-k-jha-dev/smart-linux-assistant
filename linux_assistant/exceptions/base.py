"""
exception hierarchy for the Smart Linux Assistant.
"""

from __future__ import annotations


class SmartLinuxAssistantError(Exception):
    """
    Base exception for the entire application.
    """


class ConfigurationError(SmartLinuxAssistantError):
    """
    Raised when the application configuration is missing, invalid,
    or cannot be initialized correctly.
    """


class RepositoryError(SmartLinuxAssistantError):
    """
    Raised when a repository cannot read from or write to its
    underlying data source.
    """


class ServiceError(SmartLinuxAssistantError):
    """
    Raised when a business service cannot complete the requested
    operation due to an application-level failure.
    """


class ValidationError(SmartLinuxAssistantError):
    """
    Raised when user-provided or internally generated data fails
    validation before processing.
    """
    
class CommandExecutionError(ServiceError):
    """
    Raised when a shell command cannot be executed at all, for
    example because the shell could not be spawned or the system
    refused to run it. This does NOT cover commands that ran but
    returned a non-zero exit code; a non-zero exit code is a normal,
    successfully-reported outcome captured in CommandResult.
    """


class CommandTimeoutError(CommandExecutionError):
    """
    Raised when a shell command exceeds its allotted timeout and is
    forcibly terminated before completion.
    """