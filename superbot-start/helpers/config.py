from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Tuple

import discord
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Runtime configuration for the bot."""

    token: str
    prefixes: Tuple[str, ...]
    intents: discord.Intents
    cog_mode: Literal["manual", "auto"] = "manual"
    cogs: List[str] = field(default_factory=list)
    cogs_path: str = "minebot.cogs"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    reload_retries: int = 1
    cog_timeout: float = 10.0
    sentry_dsn: Optional[str] = None


def _parse_intents(value: str) -> discord.Intents:
    if value.lower() == "all":
        return discord.Intents.all()
    intents = discord.Intents.none()
    for name in value.split(","):
        name = name.strip()
        if not name:
            continue
        if hasattr(intents, name):
            setattr(intents, name, True)
    return intents


def load_settings() -> Settings:
    """Load configuration from environment variables."""

    token = os.getenv("TOKEN") or os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("TOKEN or BOT_TOKEN environment variable is required")

    prefixes = tuple(p.strip() for p in os.getenv("PREFIXES", "!").split(",") if p.strip())
    intents = _parse_intents(os.getenv("INTENTS", "all"))
    cog_mode = os.getenv("COG_MODE", "manual").lower()
    cogs_env = os.getenv("COGS", "")
    cogs = [c.strip() for c in cogs_env.split(",") if c.strip()]
    cogs_path = os.getenv("COGS_PATH", "minebot.cogs")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    reload_retries = int(os.getenv("COG_RETRIES", "1"))
    cog_timeout = float(os.getenv("COG_TIMEOUT", "10.0"))
    sentry_dsn = os.getenv("SENTRY_DSN")

    return Settings(
        token=token,
        prefixes=prefixes,
        intents=intents,
        cog_mode=cog_mode, 
        cogs=cogs,
        cogs_path=cogs_path,
        log_level=log_level,
        log_format=log_format,
        reload_retries=reload_retries,
        cog_timeout=cog_timeout,
        sentry_dsn=sentry_dsn,
    )
