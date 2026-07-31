from __future__ import annotations

from typing import Any

from linux_assistant.config.defaults import DEFAULT_CONFIG
from linux_assistant.config.models import (
    AIConfig,
    AppConfig,
    HistoryConfig,
    LoggingConfig,
    PrivacyConfig,
)
from linux_assistant.exceptions import ConfigurationError


def validate_config(data: dict[str, Any]) -> AppConfig:
    """
    Validate and normalize a parsed TOML configuration.
    Missing sections and fields fall back to DEFAULT_CONFIG.
    Invalid field types raise ConfigurationError.
    """

    if not isinstance(data, dict):
        raise ConfigurationError(
            "Configuration root must be a TOML table."
        )

    ai = data.get("ai", {})
    history = data.get("history", {})
    logging = data.get("logging", {})
    privacy = data.get("privacy", {})

    _require_table(ai, "ai")
    _require_table(history, "history")
    _require_table(logging, "logging")
    _require_table(privacy, "privacy")

    return AppConfig(
        ai=AIConfig(
            provider=_get_str(
                ai,
                "provider",
                DEFAULT_CONFIG.ai.provider,
            ),
            model=_get_str(
                ai,
                "model",
                DEFAULT_CONFIG.ai.model,
            ),
            timeout_seconds=_get_float(
                ai,
                "timeout_seconds",
                DEFAULT_CONFIG.ai.timeout_seconds,
            ),
            max_retries=_get_int(
                ai,
                "max_retries",
                DEFAULT_CONFIG.ai.max_retries,
            ),
        ),
        history=HistoryConfig(
            enabled=_get_bool(
                history,
                "enabled",
                DEFAULT_CONFIG.history.enabled,
            ),
            max_entries=_get_int(
                history,
                "max_entries",
                DEFAULT_CONFIG.history.max_entries,
            ),
        ),
        logging=LoggingConfig(
            verbose=_get_bool(
                logging,
                "verbose",
                DEFAULT_CONFIG.logging.verbose,
            ),
        ),
        privacy=PrivacyConfig(
            redaction_enabled=_get_bool(
                privacy,
                "redaction_enabled",
                DEFAULT_CONFIG.privacy.redaction_enabled,
            ),
        ),
    )


def _require_table(value: Any, section: str) -> None:
    if not isinstance(value, dict):
        raise ConfigurationError(
            f"Configuration section '{section}' must be a TOML table."
        )


def _get_str(
    table: dict[str, Any],
    key: str,
    default: str,
) -> str:
    value = table.get(key, default)

    if not isinstance(value, str):
        raise ConfigurationError(
            f"'{key}' must be a string."
        )

    return value


def _get_int(
    table: dict[str, Any],
    key: str,
    default: int,
) -> int:
    value = table.get(key, default)

    if not isinstance(value, int):
        raise ConfigurationError(
            f"'{key}' must be an integer."
        )

    return value


def _get_float(
    table: dict[str, Any],
    key: str,
    default: float,
) -> float:
    value = table.get(key, default)

    if not isinstance(value, (int, float)):
        raise ConfigurationError(
            f"'{key}' must be a number."
        )

    return float(value)


def _get_bool(
    table: dict[str, Any],
    key: str,
    default: bool,
) -> bool:
    value = table.get(key, default)

    if not isinstance(value, bool):
        raise ConfigurationError(
            f"'{key}' must be a boolean."
        )

    return value