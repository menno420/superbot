"""Owner-aware permission checks for command decorators + gates (Q-0212).

:func:`config.is_platform_owner` grants the configured bot owner the ability to
**do everything with the bot** in any guild they are a member of — not just
``administrator``-gated surfaces but every specific-permission gate
(``manage_roles``, ``manage_guild``, ``manage_channels``, ``moderate_members``,
…).  The governance, service-mutation, setup-access, and view seams honour it;
this module is the **permission-gate** seam (command decorators + the shared
predicate the view/panel gates call).

Drop-in replacements for the ``has_permissions`` decorators — they pass for a
member holding the required permission **or** the platform owner, and raise the
*same* ``MissingPermissions`` for everyone else, so non-owners see identical
behaviour and the existing denial UX is unchanged:

    # before                                             # after
    @commands.has_permissions(manage_roles=True)         @perms_or_owner(manage_roles=True)
    @app_commands.checks.has_permissions(manage_guild=True)   @app_perms_or_owner(manage_guild=True)
    @commands.has_permissions(administrator=True)        @admin_or_owner()          # thin wrapper
    if member.guild_permissions.manage_roles: ...        if member_has_perms_or_owner(member, manage_roles=True): ...

Layer: ``core`` — imports only ``config`` (a layer-free leaf) and discord.
"""

from __future__ import annotations

from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from config import is_platform_owner


def member_has_perms_or_owner(user: Any, **perms: bool) -> bool:
    """True iff ``user`` is the platform owner OR holds all the named guild permissions.

    ``perms`` is the same keyword shape as ``discord`` permission checks, e.g.
    ``member_has_perms_or_owner(member, manage_roles=True)``.  Only keywords set
    to ``True`` are required (mirroring ``has_permissions``).  The platform-owner
    check is the single source of truth (:func:`config.is_platform_owner`); the
    permission fallback matches the ``has_permissions(...)`` bar these gates replace.
    """
    if is_platform_owner(getattr(user, "id", None)):
        return True
    required = [name for name, wanted in perms.items() if wanted]
    if not required:
        return True
    gp = getattr(user, "guild_permissions", None)
    if gp is None:
        return False
    return all(getattr(gp, name, False) for name in required)


def member_has_admin_or_owner(user: Any) -> bool:
    """True iff ``user`` holds Discord administrator OR is the platform owner.

    Back-compat alias (used by ``views.base``); delegates to
    :func:`member_has_perms_or_owner`.
    """
    return member_has_perms_or_owner(user, administrator=True)


def _missing(perms: dict[str, bool]) -> list[str]:
    """The required permission names, for the raised ``MissingPermissions``."""
    return [name for name, wanted in perms.items() if wanted] or ["administrator"]


def perms_or_owner(**perms: bool) -> Any:
    """Prefix-command check: holds the named permission(s) **or** platform owner.

    Drop-in for ``@commands.has_permissions(**perms)``; raises the same
    :class:`commands.MissingPermissions` for non-owners.
    """

    async def predicate(ctx: commands.Context) -> bool:
        if member_has_perms_or_owner(ctx.author, **perms):
            return True
        raise commands.MissingPermissions(_missing(perms))

    return commands.check(predicate)


def app_perms_or_owner(**perms: bool) -> Any:
    """Slash-command check: holds the named permission(s) **or** platform owner.

    Drop-in for ``@app_commands.checks.has_permissions(**perms)``; raises the same
    :class:`app_commands.MissingPermissions` for non-owners.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        if member_has_perms_or_owner(interaction.user, **perms):
            return True
        raise app_commands.MissingPermissions(_missing(perms))

    return app_commands.check(predicate)


def admin_or_owner() -> Any:
    """Prefix-command check: administrator **or** platform owner (thin wrapper)."""
    return perms_or_owner(administrator=True)


def app_admin_or_owner() -> Any:
    """Slash-command check: administrator **or** platform owner (thin wrapper)."""
    return app_perms_or_owner(administrator=True)


__all__ = [
    "admin_or_owner",
    "app_admin_or_owner",
    "app_perms_or_owner",
    "member_has_admin_or_owner",
    "member_has_perms_or_owner",
    "perms_or_owner",
]
