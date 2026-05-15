from __future__ import annotations

import discord
from utils.helpers import normalize_name

_DEFAULT_THRESHOLDS: list[tuple[str, int]] = [
    ("Neu", 0),
    ("Normal", 1),
    ("Iron", 7),
    ("Gold", 30),
    ("Diamand", 365),
    ("Netherite", 730),
    ("Beacon", 1825),
]

_COLOR_OPTIONS = [
    ("Red", "#e74c3c"),
    ("Blue", "#3498db"),
    ("Green", "#2ecc71"),
    ("Yellow", "#f1c40f"),
    ("Purple", "#9b59b6"),
    ("Orange", "#e67e22"),
    ("White", "#ffffff"),
    ("Black", "#000000"),
]


async def _ensure_defaults(guild_id: int) -> None:
    """Seed default time-based thresholds for a guild that has none yet."""
    from utils import db

    existing = await db.get_role_thresholds(guild_id)
    if not existing:
        for name, days in _DEFAULT_THRESHOLDS:
            await db.set_role_threshold(guild_id, name, days)


def _parse_color(value: str) -> discord.Color:
    """Parse '#ff0000' or 'ff0000' into a discord.Color."""
    value = value.strip().lstrip("#")
    return discord.Color(int(value, 16))


def _find_role_normalized(guild: discord.Guild, name: str) -> discord.Role | None:
    """Case-insensitive, space-insensitive role lookup."""
    key = normalize_name(name)
    return discord.utils.find(lambda r: normalize_name(r.name) == key, guild.roles)
