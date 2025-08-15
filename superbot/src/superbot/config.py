"""Runtime configuration for the bot."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_env() -> None:
    """Load .env files from common locations."""
    locations = [
        Path(__file__).with_name(".env"),
        Path(__file__).resolve().parent.parent / ".env",
        Path.cwd() / ".env",
    ]
    for path in locations:
        if path.is_file():
            load_dotenv(path, override=False)


_load_env()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    discord_token: str = Field(alias="DISCORD_TOKEN")
    command_prefix: str = Field("!", alias="COMMAND_PREFIX")
    owner_ids: list[int] = Field(default_factory=list, alias="OWNER_IDS")
    guild_ids: list[int] = Field(default_factory=list, alias="GUILD_IDS")
    startup_channel_id: int = Field(0, alias="STARTUP_CHANNEL_ID")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_webhook_url: str = Field("", alias="LOG_WEBHOOK_URL")
    db_path: Path = Field(Path("superbot/data/superbot.db"), alias="DB_PATH")
    data_dir: Path = Field(Path("superbot/data"), alias="DATA_DIR")
    log_dir: Path = Field(Path("superbot/logs"), alias="LOG_DIR")
    tmp_dir: Path = Field(Path("superbot/tmp"), alias="TMP_DIR")
    preload_cogs: list[str] = [
        "superbot.features.admin.admin_core",
        "superbot.features.help.help_cog",
    ]

    @field_validator("owner_ids", "guild_ids", mode="before")
    @classmethod
    def _parse_ids(cls: type[Settings], value: object) -> list[int]:
        """Normalize IDs from JSON array, CSV, or single int."""
        if value in (None, "", [], ()):
            return []
        if isinstance(value, list):
            items = value
        elif isinstance(value, int):
            items = [value]
        elif isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = value.split(",")
            items = parsed if isinstance(parsed, list) else [parsed]
        else:
            return []
        return [int(v) for v in items]

    def model_post_init(self: Settings, __context: object) -> None:
        """Create required directories after validation."""
        for path in (self.data_dir, self.log_dir, self.tmp_dir):
            os.makedirs(path, exist_ok=True)
