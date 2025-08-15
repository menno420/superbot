"""Dynamic cog discovery and management."""

from __future__ import annotations

import pkgutil
from pathlib import Path

from discord.ext import commands

from ..core.services.logging_service import log_error, log_info

FEATURES_ROOT = Path(__file__).resolve().parents[1] / "features"
BASE_PACKAGE = "superbot.features"


def discover_cogs() -> list[str]:
    """Return a list of extension module paths."""
    modules: list[str] = []
    for module in pkgutil.walk_packages(
        [str(FEATURES_ROOT)], prefix=f"{BASE_PACKAGE}.",
    ):
        if module.ispkg:
            continue
        name = module.name
        modules.append(name)
    return modules


async def load_cog(bot: commands.Bot, name: str) -> tuple[bool, str | None]:
    """Load a single cog by module name."""
    try:
        await bot.load_extension(name)
        log_info("Loaded cog %s", name)
        return True, None
    except Exception as exc:  # noqa: BLE001
        log_error("Failed to load cog %s", name, exc_info=exc)
        return False, str(exc)


async def unload_cog(bot: commands.Bot, name: str) -> tuple[bool, str | None]:
    """Unload a loaded cog."""
    try:
        await bot.unload_extension(name)
        log_info("Unloaded cog %s", name)
        return True, None
    except Exception as exc:  # noqa: BLE001
        log_error("Failed to unload cog %s", name, exc_info=exc)
        return False, str(exc)


async def reload_cog(bot: commands.Bot, name: str) -> tuple[bool, str | None]:
    """Reload an already loaded cog."""
    try:
        await bot.reload_extension(name)
        log_info("Reloaded cog %s", name)
        return True, None
    except Exception as exc:  # noqa: BLE001
        log_error("Failed to reload cog %s", name, exc_info=exc)
        return False, str(exc)


async def load_all(bot: commands.Bot) -> tuple[list[str], dict[str, str]]:
    """Load all discoverable cogs and return (loaded, failed)."""
    loaded: list[str] = []
    failed: dict[str, str] = {}
    for name in discover_cogs():
        ok, err = await load_cog(bot, name)
        if ok:
            loaded.append(name)
        else:
            failed[name] = err or "unknown"
    return loaded, failed
