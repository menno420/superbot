"""Dynamic cog loader utilities."""

from __future__ import annotations

import logging
from importlib import import_module
from pathlib import Path

from discord.ext import commands

FEATURES_PATH = Path(__file__).resolve().parents[1] / "features"
logger = logging.getLogger(__name__)


def discover_feature_modules() -> list[str]:
    """Discover feature modules containing a ``setup`` function."""
    modules: list[str] = []
    base_package = "superbot"
    for path in FEATURES_PATH.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(FEATURES_PATH.parent)
        module_name = ".".join((base_package, *rel.with_suffix("").parts))
        try:
            module = import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to import %s", module_name, exc_info=exc)
            continue
        if hasattr(module, "setup"):
            modules.append(module_name)
    return modules


async def load_all(bot: commands.Bot) -> None:
    """Load all discovered feature modules."""
    for module in discover_feature_modules():
        await bot.load_extension(module)


async def unload_all(bot: commands.Bot) -> None:
    """Unload all discovered feature modules."""
    for module in discover_feature_modules():
        await bot.unload_extension(module)
