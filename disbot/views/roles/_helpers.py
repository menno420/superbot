"""Shared helpers for the role-management panel views.

Hosts the time-based threshold defaults, the color-picker presets, the
``_ensure_defaults`` seeding routine, and the ``_parse_color`` helper.

The generic ``_find_role_normalized`` lookup now lives in
``views.selectors._resource_helpers`` so it can be consumed by code that
does not belong to the role-management subsystem (Phase 0 of the
platform roadmap). This module re-exports it for back-compat.
"""

from __future__ import annotations

import discord

from views.selectors._resource_helpers import _find_role_normalized

__all__ = [
    "_COLOR_OPTIONS",
    "_DEFAULT_THRESHOLDS",
    "_ensure_defaults",
    "_find_role_normalized",
    "_parse_color",
]

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


async def _ensure_defaults(guild: discord.Guild) -> None:
    """Seed default time tiers for a guild that has none yet — *suggestions only*.

    PR6: only a default whose named role **actually exists** is seeded (capturing
    its ``role_id`` + name snapshot), so this path never persists a threshold for
    a nonexistent role.  A brand-new guild without the default-named roles is left
    empty; operators add tiers via the selector or the panel's "Seed Defaults"
    button.  Accepts the guild (not just its id) to resolve role existence.
    """
    from core.runtime import resources
    from utils import db

    existing = await db.get_role_thresholds(guild.id)
    if existing:
        return
    for name, days in _DEFAULT_THRESHOLDS:
        role = resources.resolve_role(guild, name=name)
        if role is None:
            continue
        await db.set_role_threshold(
            guild.id,
            role.name,
            days,
            role_id=role.id,
            display_name=role.name,
        )


def _parse_color(value: str) -> discord.Color:
    """Parse '#ff0000' or 'ff0000' into a discord.Color."""
    value = value.strip().lstrip("#")
    return discord.Color(int(value, 16))
