"""
Shared Groq client construction for AI-powered services.
"""

from __future__ import annotations
import os
from groq import Groq
from linux_assistant.exceptions import MissingAPIKeyError

GROQ_API_KEY = "GROQ_API_KEY"
GROQ_MODEL = "llama-3.3-70b-versatile"

MAX_INPUT_CHARACTERS = 4000
REQUEST_TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 2


def build_groq_client() -> Groq:
    """
    Construct an authenticated Groq client using the GROQ_API_KEY
    environment variable.

    The client is configured with a request timeout and automatic
    retries for transient failures (connection errors, timeouts, and
    5xx server errors), handled internally by the Groq SDK.

    Raises:
        MissingAPIKeyError: If the environment variable is not set.
    """
    api_key = os.environ.get(GROQ_API_KEY)

    if not api_key:
        raise MissingAPIKeyError(GROQ_API_KEY)

    return Groq(
        api_key=api_key,
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=MAX_RETRIES,
    )
    
def truncate_for_api(text: str, *, keep_end: bool = False) -> str:
    """
    Truncate text to a safe length before sending it to the API,
    avoiding excessive token usage or provider-side length limits.

    Args:
        text: The text to truncate.
        keep_end: If True, keep the end of the text and truncate from
            the start (useful for error output, where the final lines
            are usually most relevant). If False, keep the beginning
            and truncate from the end.

    Returns:
        The original text if already within the limit, otherwise a
        truncated version with a marker indicating truncation occurred.
    """
    if len(text) <= MAX_INPUT_CHARACTERS:
        return text

    marker = "...[truncated]..."
    available = MAX_INPUT_CHARACTERS - len(marker)

    if keep_end:
        return marker + text[-available:]
    return text[:available] + marker