"""
Centralized logging configuration for the Smart Linux Assistant.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from linux_assistant.config.settings import settings


LOG_FILE = settings.logs_directory / "smart_linux_assistant.log"

# Level used to effectively silence the console handler by default.
_SUPPRESSED_CONSOLE_LEVEL = logging.CRITICAL + 1

# Every console handler this module has ever created, so set_verbose() can retroactively unlock them regardless of when/where each logger was originally instantiated (module import order is not controllable).
_console_handlers: list[logging.Handler] = []


def set_verbose(enabled: bool) -> None:
    """
    Enable or disable console log output across all loggers created
    by get_logger(). File logging is always active regardless of
    this setting.

    Args:
        enabled: If True, console handlers show INFO and above.
            If False, console handlers are silenced (the default).
    """
    level = logging.INFO if enabled else _SUPPRESSED_CONSOLE_LEVEL
    for handler in _console_handlers:
        handler.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger for the given module.
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(_SUPPRESSED_CONSOLE_LEVEL)
    _console_handlers.append(console_handler)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger