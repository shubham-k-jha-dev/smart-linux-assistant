import pytest

from linux_assistant.config.defaults import DEFAULT_CONFIG
from linux_assistant.config.validator import validate_config
from linux_assistant.exceptions import ConfigurationError


def test_empty_configuration_returns_defaults() -> None:
    config = validate_config({})

    assert config == DEFAULT_CONFIG


def test_partial_configuration_overrides_defaults() -> None:
    config = validate_config(
        {
            "logging": {
                "verbose": True,
            }
        }
    )

    assert config.logging.verbose is True
    assert config.ai == DEFAULT_CONFIG.ai
    assert config.history == DEFAULT_CONFIG.history
    assert config.privacy == DEFAULT_CONFIG.privacy


def test_invalid_boolean_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        validate_config(
            {
                "logging": {
                    "verbose": "yes",
                }
            }
        )


def test_invalid_integer_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        validate_config(
            {
                "history": {
                    "max_entries": "5000",
                }
            }
        )


def test_invalid_section_type_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        validate_config(
            {
                "history": True,
            }
        )