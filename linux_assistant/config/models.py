from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrivacyConfig:
    """
    Privacy-related configuration.
    """

    redaction_enabled: bool


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """
    Logging-related configuration.
    """

    verbose: bool


@dataclass(frozen=True, slots=True)
class HistoryConfig:
    """
    History-related configuration.
    """

    enabled: bool
    max_entries: int


@dataclass(frozen=True, slots=True)
class AIConfig:
    """
    AI provider configuration.
    """

    provider: str
    model: str
    timeout_seconds: float
    max_retries: int


@dataclass(frozen=True, slots=True)
class AppConfig:
    """
    Root application configuration.
    """

    ai: AIConfig
    history: HistoryConfig
    logging: LoggingConfig
    privacy: PrivacyConfig