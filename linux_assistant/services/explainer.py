"""
AI-powered explanations for Linux commands and error messages.
"""

from __future__ import annotations
import groq
from linux_assistant.utils.groq_client import GROQ_MODEL, build_groq_client
from linux_assistant.exceptions import MissingAPIKeyError, ServiceError, ValidationError, RateLimitError
from linux_assistant.utils.logger import get_logger
from linux_assistant.utils.groq_client import GROQ_MODEL, build_groq_client, truncate_for_api

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an elite Linux System Administrator and DevOps expert. Your primary role is to analyze, explain, and troubleshoot Linux shell commands, shell scripts, error messages, and terminal output. 

Your tone should be professional, direct, and accessible, translating complex technical concepts into plain language without losing accuracy. 

When responding, strictly adhere to the following guidelines:

1. STRUCTURED BREAKDOWNS: When explaining a command, break it down logically. Briefly explain what the entire command does, then use standard dashes (-) to list and explain each specific flag, option, and argument.
2. TROUBLESHOOTING PROTOCOL: If the user provides an error message or broken script, always include:
   - Root Cause: A brief explanation of why it failed.
   - The Fix: The exact, corrected command or action required.
   - Verification: How the user can verify the fix worked.
3. SAFETY FIRST: If a command is destructive (e.g., involves rm -rf, dd, chmod 777, or partition changes), clearly prepend a [WARNING] to your response explaining the risk and how to execute it safely.
4. BEST PRACTICES: Where applicable, suggest modern or more efficient alternatives (e.g., using ip instead of ifconfig).
5. TERMINAL-SAFE FORMATTING: Do NOT use any Markdown formatting. Your output is being displayed in a raw text terminal. Do not use asterisks for bolding, hashes for headers, or backticks for code. Instead, use ALL CAPS for section headers. To highlight commands or file paths, simply indent them with spaces on a new line or wrap them in single quotes (' ').

Keep responses concise and scannable. Limit your response to the essential information needed to solve the user's problem or answer their question, avoiding unnecessary fluff.
"""

FIX_SYSTEM_PROMPT = """You are an automated Linux command correction tool operating in a raw terminal. You receive a failed shell command and its corresponding error message. Your single purpose is to output the exact, executable corrected command.

CRITICAL CONSTRAINTS:
1. Output ONLY the corrected command on a single line.
2. Provide zero conversational filler (do not start with "Here is the command" or "Try this").
3. Use zero Markdown formatting (no backticks or formatting blocks).
4. Do not include quotes or a leading '$' prompt.
5. Retain the user's original filenames, paths, and valid arguments exactly as provided; do not substitute them with generic placeholders.
6. If you cannot determine a highly confident fix, output exactly: NO_FIX_AVAILABLE
"""


class Explainer:
    """
    Generate plain-language explanations of Linux commands or errors
    using an LLM.
    """

    def __init__(self) -> None:
        self._client = build_groq_client()

    def explain(self, text: str) -> str:
        """
        Explain a command or error message in plain language.
        ValidationError: If text is empty or whitespace-only.
        ServiceError: If the underlying API call fails.
        """
        text = text.strip()

        if not text:
            from linux_assistant.exceptions import ValidationError

            raise ValidationError("Text to explain cannot be empty.")

        text = truncate_for_api(text)

        logger.info("Requesting explanation for: %s", text)

        try:
            response = self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
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
        
        explanation = response.choices[0].message.content
        if explanation is None:
            raise ServiceError("Received an empty explanation from the API.")
        logger.info("Explanation received (%d characters).", len(explanation))

        return explanation.strip()
    
    def suggest_fix(self, command: str, error: str) -> str | None:
        """
        Suggest a corrected version of a failed shell command.
        """
        command = command.strip()

        if not command:
            from linux_assistant.exceptions import ValidationError

            raise ValidationError("Command to fix cannot be empty.")

        error = truncate_for_api(error, keep_end=True)

        user_content = f"Command: {command}\nError: {error.strip()}"

        logger.info("Requesting fix suggestion for: %s", command)

        try:
            response = self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": FIX_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
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

        suggestion = response.choices[0].message.content

        if suggestion is None:
            raise ServiceError("Received an empty fix suggestion from the API.")

        suggestion = suggestion.strip()

        if suggestion == "NO_FIX_AVAILABLE":
            logger.info("No confident fix available for: %s", command)
            return None

        logger.info("Fix suggestion received: %s", suggestion)

        return suggestion