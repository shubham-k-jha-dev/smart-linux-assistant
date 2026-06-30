"""
Expose the application's public domain models.
Importing models from this package keeps the rest of the project
independent of the underlying file layout.
"""

from .command_result import CommandResult

__all__ = [
    "CommandResult",
]