from __future__ import annotations

import tomllib
from pathlib import Path

from linux_assistant.config.defaults import DEFAULT_CONFIG
from linux_assistant.config.models import AppConfig


CONFIG_FILE_NAME = "config.toml"


def get_config_path() -> Path:
    """
    Return the location of the user configuration file.
    """
    return Path.home() / ".config" / "smart-linux-assistant" / CONFIG_FILE_NAME


def load_config() -> AppConfig:
    """
    Load the application configuration.

    Currently returns the default configuration until TOML
    parsing is implemented.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return DEFAULT_CONFIG

    with config_path.open("rb") as file:
        tomllib.load(file)

    return DEFAULT_CONFIG