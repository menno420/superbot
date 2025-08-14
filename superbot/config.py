"""Application settings management."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseModel):
    """Application settings loaded from environment and configuration files."""

    discord_token: str = Field(alias="DISCORD_TOKEN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    db_path: str = Field(default="superbot/data/db/superbot.sqlite3", alias="DB_PATH")
    guild_id: int | None = Field(default=None, alias="GUILD_ID")

    model_config = {"populate_by_name": True}


def _read_env_file(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.is_file():
        return data
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _read_yaml_file(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}
    if not isinstance(loaded, dict):
        return {}
    return {str(k): v for k, v in loaded.items()}


@lru_cache()
def get_settings() -> Settings:
    """Return application settings.

    Raises:
        RuntimeError: If required settings are missing.
    """

    env_data = _read_env_file(BASE_DIR / ".env")
    yaml_data = _read_yaml_file(BASE_DIR / "settings.yml")
    data = {**env_data, **yaml_data, **os.environ}
    try:
        settings = Settings(**data)
    except ValidationError as exc:
        raise RuntimeError("Invalid configuration") from exc

    if not settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is required")

    return settings
