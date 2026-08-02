from __future__ import annotations

from linux_assistant.config.models import (
    AIConfig,
    AppConfig,
    HistoryConfig,
    LoggingConfig,
    PrivacyConfig,
)


DEFAULT_AI_CONFIG = AIConfig(
    provider="groq",
    model="llama-3.3-70b-versatile",
    timeout_seconds=30.0,
    max_retries=3,
)

DEFAULT_HISTORY_CONFIG = HistoryConfig(
    enabled=True,
    max_entries=5000,
)

DEFAULT_LOGGING_CONFIG = LoggingConfig(
    verbose=False,
)

DEFAULT_PRIVACY_CONFIG = PrivacyConfig(
    redaction_enabled=True,
)

DEFAULT_CONFIG = AppConfig(
    ai=DEFAULT_AI_CONFIG,
    history=DEFAULT_HISTORY_CONFIG,
    logging=DEFAULT_LOGGING_CONFIG,
    privacy=DEFAULT_PRIVACY_CONFIG,
)