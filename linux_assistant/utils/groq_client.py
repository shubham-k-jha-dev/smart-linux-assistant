"""
Shared Groq client construction for AI-powered services.
"""

from __future__ import annotations
import os
from groq import Groq
from linux_assistant.exceptions import MissingAPIKeyError

GROQ_API_KEY = "GROQ_API_KEY"
GROQ_MODEL = "llama-3.3-70b-versatile"


def build_groq_client() -> Groq:
    """
    Construct an authenticated Groq client using the GROQ_API_KEY
    environment variable.

    Raises:
        MissingAPIKeyError: If the environment variable is not set.
    """
    api_key = os.environ.get(GROQ_API_KEY)

    if not api_key:
        raise MissingAPIKeyError(GROQ_API_KEY)

    return Groq(api_key=api_key)