"""Shared helpers for the role-management panel views.

Hosts the colour-picker presets (``_COLOR_OPTIONS``), the role-creation presets
(``ROLE_PRESETS`` — quick-create templates shown ONLY in the role creation
menu), and the ``_parse_color`` helper.

The generic ``_find_role_normalized`` lookup now lives in
``views.selectors._resource_helpers`` so it can be consumed by code that
does not belong to the role-management subsystem (Phase 0 of the
platform roadmap). This module re-exports it for back-compat.

**2026-06-21:** the hardcoded ``_DEFAULT_THRESHOLDS`` tier names
(``Neu/Normal/Iron/Gold/Diamand/Netherite/Beacon``) and the ``_ensure_defaults``
seed routine were **removed** (owner directive).  Role automation now loads only
roles that exist on the server — no fictional name-based rows are ever
persisted.  Curated *names* live on as ``ROLE_PRESETS``, but exclusively as a
convenience in the role creation menu (``RoleCreatePanel``); they never touch
automation, diagnostics, or any other surface.
"""

from __future__ import annotations

from dataclasses import dataclass

import discord

from utils import role_packs
from views.selectors._resource_helpers import _find_role_normalized

__all__ = [
    "_COLOR_OPTIONS",
    "ROLE_PRESETS",
    "RolePreset",
    "_find_role_normalized",
    "_parse_color",
]

_COLOR_OPTIONS = [
    ("Red", "#e74c3c"),
    ("Crimson", "#c0392b"),
    ("Orange", "#e67e22"),
    ("Gold", "#f1c40f"),
    ("Yellow", "#ffeb3b"),
    ("Lime", "#a4d007"),
    ("Green", "#2ecc71"),
    ("Emerald", "#1abc9c"),
    ("Teal", "#009688"),
    ("Cyan", "#00bcd4"),
    ("Blue", "#3498db"),
    ("Blurple", "#5865f2"),
    ("Navy", "#34495e"),
    ("Purple", "#9b59b6"),
    ("Magenta", "#e91e63"),
    ("Pink", "#ff79c6"),
    ("Brown", "#795548"),
    ("Grey", "#95a5a6"),
    ("White", "#ffffff"),
    ("Black", "#000000"),
]


@dataclass(frozen=True)
class RolePreset:
    """A quick-create role template.

    Presets are *creation conveniences only* — a name + appearance starting
    point an operator can pick instead of typing everything by hand.  They are
    surfaced **exclusively** in the role creation menu (``RoleCreatePanel``):
    deliberately absent from diagnostics, time/XP automation, and every other
    surface, and they persist nothing until the operator actually creates the
    role.  This replaced the old hardcoded ``_DEFAULT_THRESHOLDS`` tier names,
    which leaked into automation as phantom "missing role" rows.
    """

    name: str
    color: str  # hex, e.g. "#3498db"
    hoist: bool = False
    description: str = ""


# The quick-create presets ARE the ⭐ Essentials role pack (``utils.role_packs``)
# — one data source, so enlarging the pack enlarges this single-create dropdown
# too (and the bulk-create flow shows the same names as a multiselect). Converted
# to ``RolePreset`` for the creation menu's name+colour staging, which only reads
# name / color / hoist / description. Extend via the pack, not here.
_ESSENTIALS = role_packs.get_pack("essentials")
ROLE_PRESETS: list[RolePreset] = [
    RolePreset(r.name, r.color, hoist=r.hoist, description=r.description)
    for r in (_ESSENTIALS.roles if _ESSENTIALS else ())
]


def _parse_color(value: str) -> discord.Color:
    """Parse '#ff0000' or 'ff0000' into a discord.Color."""
    value = value.strip().lstrip("#")
    return discord.Color(int(value, 16))
