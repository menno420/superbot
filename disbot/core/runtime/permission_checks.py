"""Owner-aware permission checks for command decorators (Q-0212).

:func:`config.is_platform_owner` grants the configured bot owner full
bot-configuration authority in any guild they are a member of.  The governance,
service-mutation, setup-access, and view seams already honour it; this module is
the **command-decorator** seam.

``admin_or_owner`` / ``app_admin_or_owner`` are drop-in replacements for the
``has_permissions(administrator=True)`` decorators: they pass for an
administrator **or** the platform owner, and raise the *same*
``MissingPermissions`` for everyone else — so non-owners see identical behaviour
and the existing error-handling / denial UX is unchanged.

    # before                                   # after
    @commands.has_permissions(administrator=True)      @admin_or_owner()
    @app_commands.checks.has_permissions(administrator=True)   @app_admin_or_owner()

Layer: ``core`` — imports only ``config`` (a layer-free leaf) and discord.
"""

from __future__ import annotations

from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from config import is_platform_owner


def member_has_admin_or_owner(user: Any) -> bool:
    """True iff ``user`` holds Discord administrator OR is the platform owner.

    The platform-owner check is the single source of truth
    (:func:`config.is_platform_owner`); the administrator fallback matches the
    ``has_permissions(administrator=True)`` bar these checks replace.
    """
    if is_platform_owner(getattr(user, "id", None)):
        return True
    perms = getattr(user, "guild_permissions", None)
    return bool(perms is not None and getattr(perms, "administrator", False))


def admin_or_owner() -> Any:
    """Prefix-command check: administrator **or** platform owner.

    Drop-in for ``@commands.has_permissions(administrator=True)``; raises the same
    :class:`commands.MissingPermissions` for non-owners.
    """

    async def predicate(ctx: commands.Context) -> bool:
        if member_has_admin_or_owner(ctx.author):
            return True
        raise commands.MissingPermissions(["administrator"])

    return commands.check(predicate)


def app_admin_or_owner() -> Any:
    """Slash-command check: administrator **or** platform owner.

    Drop-in for ``@app_commands.checks.has_permissions(administrator=True)``;
    raises the same :class:`app_commands.MissingPermissions` for non-owners.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        if member_has_admin_or_owner(interaction.user):
            return True
        raise app_commands.MissingPermissions(["administrator"])

    return app_commands.check(predicate)


__all__ = ["admin_or_owner", "app_admin_or_owner", "member_has_admin_or_owner"]
