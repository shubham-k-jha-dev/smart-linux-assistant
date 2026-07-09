"""
AI-powered natural-language search for Linux commands and tasks.
"""

from __future__ import annotations
import groq
from linux_assistant.exceptions import ServiceError, ValidationError, RateLimitError
from linux_assistant.utils.groq_client import GROQ_MODEL, build_groq_client
from linux_assistant.utils.logger import get_logger

logger = get_logger(__name__)

SEARCH_SYSTEM_PROMPT = """You are a Linux command lookup tool operating in a raw terminal. The user will describe a desired action in plain language. Your objective is to provide a concrete, ready-to-run command and a brief explanation.

CRITICAL CONSTRAINTS:
1. COMMAND FORMAT: Place the suggested command on its own line, prefixed with exactly "$ ". 
2. EXPLANATION: Provide a 1-2 sentence practical explanation on the line immediately below the command.
3. ZERO MARKDOWN: Do NOT use backticks (`), asterisks (*), or hashes (#). Output pure raw text.
4. ZERO FILLER: Do not use conversational openings like "Sure" or "Here is the command". Start immediately with the "$ " command line.
5. READY-TO-RUN (NO PLACEHOLDERS): Always use realistic, runnable values in the command itself. Use standard defaults (like '.' for the current directory) or plausible example filenames (like 'example.txt'). NEVER use angle-bracket placeholders like <directory_path> or <filename>. The user should be able to copy and run the command directly.
6. BREVITY: Keep the entire response strictly under 120 words.
"""


class Searcher:
    """
    Answer natural-language questions about Linux commands and tasks.
    """

    def __init__(self) -> None:
        self._client = build_groq_client()

    def search(self, query: str) -> str:
        """
        Answer a natural-language question about a Linux task.

        Args:
            query: The user's question, e.g. "how do I find large files".

        Returns:
            A short, practical answer.
        """
        query = query.strip()

        if not query:
            raise ValidationError("Search query cannot be empty.")

        logger.info("Searching for: %s", query)

        try:
            response = self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
            )
        except groq.RateLimitError as exc:
            logger.error("Rate limit hit: %s", exc)
            raise RateLimitError(
                "Groq API rate limit reached. Please wait a moment and try again."
            ) from exc
        except Exception as exc:
            logger.error("Explanation request failed: %s", exc)
            raise ServiceError(f"Failed to get explanation: {exc}") from exc

        answer = response.choices[0].message.content

        if answer is None:
            raise ServiceError("Received an empty answer from the API.")

        logger.info("Search answer received (%d characters).", len(answer))

        return answer.strip()