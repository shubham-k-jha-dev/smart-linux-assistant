"""
Centralized logging configuration for the Smart Linux Assistant.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from linux_assistant.config.settings import settings


LOG_FILE = settings.logs_directory / "smart_linux_assistant.log"


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