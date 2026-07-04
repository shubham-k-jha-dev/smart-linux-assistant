"""
AI-powered explanations for Linux commands and error messages.
"""

from __future__ import annotations

import os
from groq import Groq
from linux_assistant.exceptions import MissingAPIKeyError, ServiceError, ValidationError
from linux_assistant.utils.logger import get_logger

logger = get_logger(__name__)

GROQ_API_KEY = "GROQ_API_KEY"
GROQ_MODEL = "llama-3.3-70b-versatile"

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


class Explainer:
    """
    Generate plain-language explanations of Linux commands or errors
    using an LLM.
    """

    def __init__(self) -> None:
        api_key = os.environ.get(GROQ_API_KEY)

        if not api_key:
            raise MissingAPIKeyError(GROQ_API_KEY)

        self._client = Groq(api_key=api_key)

    def explain(self, text: str) -> str:
        """
        Explain a command or error message in plain language.
        ValidationError: If text is empty or whitespace-only.
        ServiceError: If the underlying API call fails.
        """
        text = text.strip()

        if not text:
            raise ValidationError("Text to explain cannot be empty.")

        logger.info("Requesting explanation for: %s", text)

        try:
            response = self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
            )
        except Exception as exc:
            logger.error("Explanation request failed: %s", exc)
            raise ServiceError(f"Failed to get explanation: {exc}") from exc
        explanation = response.choices[0].message.content
        if explanation is None:
            raise ServiceError("Received an empty explanation from the API.")
        logger.info("Explanation received (%d characters).", len(explanation))

        return explanation.strip()