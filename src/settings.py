"""
Centralized settings management for Soul Kiln.

Loads configuration from environment variables with sensible defaults.
Uses python-dotenv to load .env files in development.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from functools import lru_cache

# Load .env file if it exists
from dotenv import load_dotenv

# Find .env file relative to this file or in working directory
_env_paths = [
    Path(__file__).parent.parent / ".env",
    Path.cwd() / ".env",
]
for _path in _env_paths:
    if _path.exists():
        load_dotenv(_path)
        break


def _get_env(key: str, default: str = None, required: bool = False) -> Optional[str]:
    """Get environment variable with optional requirement check."""
    value = os.environ.get(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def _get_env_int(key: str, default: int) -> int:
    """Get environment variable as integer."""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean."""
    value = os.environ.get(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


@dataclass
class DatabaseSettings:
    """FalkorDB connection settings."""
    host: str = field(default_factory=lambda: _get_env("FALKORDB_HOST", "localhost"))
    port: int = field(default_factory=lambda: _get_env_int("FALKORDB_PORT", 6379))
    graph: str = field(default_factory=lambda: _get_env("FALKORDB_GRAPH", "soul_kiln"))


@dataclass
class LLMSettings:
    """Anthropic LLM settings."""
    api_key: str = field(default_factory=lambda: _get_env("ANTHROPIC_API_KEY", ""))
    model: str = field(default_factory=lambda: _get_env("LLM_MODEL", "claude-sonnet-4-20250514"))
    max_tokens: int = field(default_factory=lambda: _get_env_int("LLM_MAX_TOKENS", 4096))

    @property
    def is_configured(self) -> bool:
        """Check if LLM is properly configured."""
        return bool(self.api_key and self.api_key.startswith("sk-"))


@dataclass
class APISettings:
    """API server settings."""
    host: str = field(default_factory=lambda: _get_env("API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _get_env_int("API_PORT", 8080))
    secret_key: str = field(default_factory=lambda: _get_env("API_SECRET_KEY", "dev-secret-change-me"))
    rate_limit_per_minute: int = field(default_factory=lambda: _get_env_int("RATE_LIMIT_PER_MINUTE", 60))


@dataclass
class Settings:
    """Main settings container."""
    environment: str = field(default_factory=lambda: _get_env("ENVIRONMENT", "development"))
    log_level: str = field(default_factory=lambda: _get_env("LOG_LEVEL", "INFO"))
    debug: bool = field(default_factory=lambda: _get_env_bool("DEBUG", False))

    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    api: APISettings = field(default_factory=APISettings)

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience access
settings = get_settings()
