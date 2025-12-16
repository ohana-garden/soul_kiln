"""
Centralized configuration loading for Soul Kiln.

Provides a single source of truth for loading config.yml.
Import from here rather than defining get_config() locally.
"""

import os
from pathlib import Path
from typing import Any

import yaml

# Cache the loaded config
_config_cache: dict | None = None
_config_path: Path | None = None


def _find_config_path() -> Path:
    """Find the config.yml file relative to project root."""
    # Try multiple locations
    candidates = [
        Path(__file__).parent.parent.parent / "config.yml",  # src/utils/ -> root
        Path.cwd() / "config.yml",  # Current working directory
        Path(os.environ.get("SOUL_KILN_CONFIG", "")) if os.environ.get("SOUL_KILN_CONFIG") else None,
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    raise FileNotFoundError(
        "config.yml not found. Searched:\n" +
        "\n".join(f"  - {c}" for c in candidates if c)
    )


def load_config(force_reload: bool = False) -> dict[str, Any]:
    """
    Load configuration from config.yml.

    Args:
        force_reload: If True, reload even if cached

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config.yml cannot be found
        yaml.YAMLError: If config.yml is malformed
    """
    global _config_cache, _config_path

    if _config_cache is not None and not force_reload:
        return _config_cache

    _config_path = _find_config_path()

    with open(_config_path, "r") as f:
        _config_cache = yaml.safe_load(f)

    return _config_cache


def get_config() -> dict[str, Any]:
    """
    Get the configuration dictionary.

    Convenience wrapper around load_config() that never forces reload.
    This is the primary function to use throughout the codebase.

    Returns:
        Configuration dictionary
    """
    return load_config()


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value by dot-notation key.

    Args:
        key: Dot-notation key (e.g., "mercy.max_warnings")
        default: Default value if key not found

    Returns:
        Configuration value or default

    Example:
        >>> get_config_value("mercy.max_warnings", 3)
        3
    """
    config = get_config()
    parts = key.split(".")

    value = config
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default

    return value


def get_config_path() -> Path | None:
    """Get the path to the loaded config file."""
    return _config_path
