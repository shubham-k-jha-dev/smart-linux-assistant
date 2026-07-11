"""
exception hierarchy for the Smart Linux Assistant.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from linux_assistant.models import CommandResult

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


class HistoryError(RepositoryError):
    """
    Raised when the command history store cannot be read from,
    written to, or cleared. Callers that record history as a
    side-effect (rather than an explicit user request) should catch
    this, log it, and continue — a history-recording failure must
    never interrupt the command the user actually asked to run.
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
    
class CommandFailedError(ServiceError):
    """
    Raised by execute_checked() when a command runs to completion but
    exits with a non-zero status code. This is distinct from
    CommandExecutionError: the command DID execute successfully at
    the OS level, it simply reported failure via its exit code.
    """

    def __init__(self, result: "CommandResult") -> None:
        self.result = result
        message = (
            f"Command '{result.command}' failed with exit code "
            f"{result.exit_code}."
        )
        super().__init__(message)
        
        
class MissingAPIKeyError(ConfigurationError):
    """
    Raised when an AI-powered feature is used but the required API
    key environment variable is not set.
    """

    def __init__(self, env_var_name: str) -> None:
        self.env_var_name = env_var_name
        message = (
            f"The '{env_var_name}' environment variable is not set. "
            f"Get a free API key at https://console.groq.com and set it with:\n"
            f"  export {env_var_name}=\"your-key-here\""
        )
        super().__init__(message)
        
        
class RateLimitError(ServiceError):
    """
    Raised when an AI-powered feature hits the API provider's rate
    limit. This is a transient condition — retrying after a short
    delay will typically succeed.
    """