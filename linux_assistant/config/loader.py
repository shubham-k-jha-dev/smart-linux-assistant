from __future__ import annotations

import os
import tomllib
from pathlib import Path

from linux_assistant.config.defaults import DEFAULT_CONFIG
from linux_assistant.config.models import AppConfig
from linux_assistant.config.validator import validate_config
from linux_assistant.exceptions import ConfigurationError

CONFIG_FILE_NAME = "config.toml"


def get_config_path() -> Path:
    """
    Return the location of the user configuration file.

    The configuration file follows the XDG Base Directory specification.
    If XDG_CONFIG_HOME is not set, ~/.config is used.
    """
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")

    if xdg_config_home:
        config_home = Path(xdg_config_home)
    else:
        config_home = Path.home() / ".config"

    return config_home / "smart-linux-assistant" / CONFIG_FILE_NAME


def load_config() -> AppConfig:
    """
    Load the application configuration.

    Returns the default configuration if no configuration file exists.

    Raises:
        ConfigurationError:
            If the configuration file cannot be read or contains
            invalid TOML or invalid configuration values.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return DEFAULT_CONFIG

    try:
        with config_path.open("rb") as file:
            data = tomllib.load(file)

    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(
            f"Invalid TOML syntax in '{config_path}'."
        ) from exc

    except OSError as exc:
        raise ConfigurationError(
            f"Unable to read configuration file '{config_path}'."
        ) from exc

    return validate_config(data)