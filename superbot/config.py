"""Configuration management for Superbot."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DISCORD_TOKEN: str
    COMMAND_PREFIX: str = "!"
    OWNER_IDS: list[int] = []
    GUILD_IDS: list[int] = []
    LOG_LEVEL: str = "INFO"
    LOG_WEBHOOK_URL: str | None = None
    STARTUP_CHANNEL_ID: int | None = None
    DB_PATH: str = "superbot/data/superbot.db"
    DATA_DIR: str = "superbot/data"
    LOG_DIR: str = "superbot/logs"
    TMP_DIR: str = "superbot/tmp"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("OWNER_IDS", "GUILD_IDS", mode="before")
    @classmethod
    def _split_csv(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, str):
            if not value.strip():
                return []
            return [int(part.strip()) for part in value.split(",") if part.strip()]
        return value

    @field_validator("DB_PATH", "DATA_DIR", "LOG_DIR", "TMP_DIR", mode="before")
    @classmethod
    def _resolve_path(cls, value: str) -> str:
        path = Path(value)
        if not path.is_absolute():
            root = Path(__file__).resolve().parent
            path = root / path
        return str(path)

    @field_validator("LOG_LEVEL", mode="after")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.upper()

    @staticmethod
    def _ensure_dir(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def model_post_init(self) -> None:  # type: ignore[override]
        for attr in ("DATA_DIR", "LOG_DIR", "TMP_DIR"):
            self._ensure_dir(getattr(self, attr))

    def secret_values(self) -> Iterable[str]:
        """Return values that should be redacted from logs."""
        secrets = [self.DISCORD_TOKEN]
        if self.LOG_WEBHOOK_URL:
            secrets.append(self.LOG_WEBHOOK_URL)
        return secrets


@lru_cache()
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
