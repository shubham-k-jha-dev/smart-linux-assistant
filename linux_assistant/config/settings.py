"""
centralised configuration to make the project easier to maintain, test, and extend as new features are added.
"""

from __future__ import annotations
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
            
    # Fallback to the original static resolution if the marker is missing
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _find_project_root()


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Store shared project configuration.
    """
    project_root: Path
    logs_directory: Path
    data_directory: Path
    documentation_directory: Path


settings = Settings(
    project_root=PROJECT_ROOT,
    logs_directory=PROJECT_ROOT / "logs",
    data_directory=PROJECT_ROOT / "data",
    documentation_directory=PROJECT_ROOT / "docs",
)


def initialize_app_filesystem() -> None:
    """
    Ensure required runtime directories exist with appropriate permissions.
    
    must be called explicitly during application startup to prevent 
    unintended side-effects during standard imports or automated testing.
    """
    for directory in (settings.logs_directory, settings.data_directory):
        directory.mkdir(parents=True, exist_ok=True)