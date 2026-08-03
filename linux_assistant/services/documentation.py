"""
Linux documentation lookup service.
"""

from __future__ import annotations


class DocumentationService:
    """
    Retrieve and format local Linux manual pages.
    """

    def get_documentation(self, command: str) -> str:
        """
        Return formatted documentation for a Linux command.
        """
        raise NotImplementedError