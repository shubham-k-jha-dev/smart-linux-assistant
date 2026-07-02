"""
centralised configuration to make the project easier to maintain, test, and extend as new features are added.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

def _find_project_root(marker: str = "pyproject.toml") -> Path:
    """
    Dynamically locate the project root by searching upwards for a marker file.
    This prevents breakage if the settings module is moved to a different depth.
    """
    current_dir = Path(__file__).resolve().parent
    for parent in [current_dir, *current_dir.parents]:
        if (parent / marker).exists():
            return parent
    return None 

def _get_user_data_home() -> Path:
    """
    Resolve the user's data directory following the XDG Base Directory
    specification, with a Windows/macOS fallback. This is where the
    application should write logs and runtime data regardless of where
    the code itself is installed.
    """
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "smart-linux-assistant"
    return Path.home() / ".local" / "share" / "smart-linux-assistant"


PROJECT_ROOT = _find_project_root()
USER_DATA_HOME = _get_user_data_home()

@dataclass(frozen=True, slots=True)
class Settings:
    """
    Store shared project configuration.
    """
    project_root: Path  | None
    logs_directory: Path
    data_directory: Path
    documentation_directory: Path | None


settings = Settings(
    project_root=PROJECT_ROOT,
    logs_directory=USER_DATA_HOME / "logs",
    data_directory=USER_DATA_HOME / "data",
    documentation_directory=(PROJECT_ROOT / "docs") if PROJECT_ROOT else None,
)


def initialize_app_filesystem() -> None:
    """
    Ensure required runtime directories exist with appropriate permissions.
    
    must be called explicitly during application startup to prevent 
    unintended side-effects during standard imports or automated testing.
    """
    for directory in (settings.logs_directory, settings.data_directory):
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o755)