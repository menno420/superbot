"""Shared resource-lookup helpers for selector / panel code.

Phase 0 of the platform roadmap pulled these helpers out of
``views/channels/_helpers.py`` and ``views/roles/_helpers.py`` into a
shared module.  Phase 2a absorbed the *implementation* into
:mod:`core.resources` — this module now exists only as a back-compat
shim that delegates to the canonical location.

New code should import directly from :mod:`core.resources.channel_service`
or :mod:`core.resources.discovery`; this shim stays in place for one
release so the existing panel code does not need to touch its imports.
"""

from __future__ import annotations

import discord

from core.resources.channel_service import build_select_options
from core.resources.discovery import find_role_by_name


def _build_channel_options(guild: discord.Guild) -> list[discord.SelectOption]:
    """Back-compat shim for :func:`core.resources.channel_service.build_select_options`."""
    return build_select_options(guild, include_voice=True, limit=25)


def _find_role_normalized(
    guild: discord.Guild,
    name: str,
) -> discord.Role | None:
    """Back-compat shim for :func:`core.resources.discovery.find_role_by_name`."""
    return find_role_by_name(guild, name)


__all__ = ["_build_channel_options", "_find_role_normalized"]
