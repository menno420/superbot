"""Moderation service — single audited path for moderation actions.

Mirrors :mod:`services.economy_service`: every moderation action
(warn, timeout, kick, ban, unban, clear_warnings) routes through one
function that:

  1. Performs the underlying Discord-API or DB write.
  2. Appends an immutable row to ``mod_logs`` via
     :func:`utils.db.log_mod_action`.
  3. Emits the catalogued ``EVT_MOD_ACTION`` event on the EventBus
     so subscribers (panel-refresh, audit dashboards, future
     analytics) can react without polling the DB.

The function signatures accept the resolved Discord object
(``discord.Member`` for member actions, ``discord.Guild`` +
``discord.User`` for guild-level actions) so the caller has already
authorized the action; the service does not re-check permissions.
Permission checks live at the cog/view layer where the interacting
member's identity is available.

Public API
----------
- :func:`warn(member, *, reason, actor_id)`               — adds a warning
- :func:`timeout(member, *, until, reason, actor_id)`     — Discord timeout
- :func:`kick(member, *, reason, actor_id)`               — guild kick
- :func:`ban(guild, user, *, reason, actor_id)`           — guild ban
- :func:`unban(guild, user, *, reason, actor_id)`         — guild unban
- :func:`clear_warnings(guild_id, user_id, *, actor_id)`  — reset warnings

All functions emit ``EVT_MOD_ACTION`` with the same payload shape so
subscribers can dispatch on the ``action`` field.

Discord-API exceptions (``discord.Forbidden``, ``discord.HTTPException``)
are NOT caught here — callers handle them, since the appropriate
user-facing response (ephemeral DM "I can't ban that user") is
context-dependent.
"""

from __future__ import annotations

import logging
from datetime import datetime

import discord

from core.events import bus
from utils import db

logger = logging.getLogger("bot.moderation_service")

# Single event covers every moderation action; subscribers dispatch
# on payload["action"].  Also listed in core/events_catalogue.KNOWN_EVENTS.
EVT_MOD_ACTION = "moderation.action_taken"


async def warn(
    member: discord.Member,
    *,
    reason: str,
    actor_id: int | None = None,
) -> int:
    """Record a warning for *member*; return new warning count.

    Args:
        member: target Discord member.
        reason: short attribution string.
        actor_id: invoking moderator's ID; None for system actions.

    Returns:
        The post-increment warning count.
    """
    new_count = await db.add_warning(member.id, member.guild.id)
    await db.log_mod_action(
        member.guild.id,
        "warn",
        member.id,
        actor_id or 0,
        reason,
    )
    await bus.emit(
        EVT_MOD_ACTION,
        guild_id=member.guild.id,
        target_id=member.id,
        actor_id=actor_id,
        action="warn",
        reason=reason,
    )
    return new_count


async def timeout(
    member: discord.Member,
    *,
    until: datetime,
    reason: str,
    actor_id: int | None = None,
) -> None:
    """Timeout *member* until *until*; log + emit event.

    Discord-side timeout failures propagate; the audit row is only
    written on successful timeout.
    """
    await member.timeout(until, reason=reason)
    await db.log_mod_action(
        member.guild.id,
        "timeout",
        member.id,
        actor_id or 0,
        reason,
    )
    await bus.emit(
        EVT_MOD_ACTION,
        guild_id=member.guild.id,
        target_id=member.id,
        actor_id=actor_id,
        action="timeout",
        reason=reason,
        until=until.isoformat() if until else None,
    )


async def kick(
    member: discord.Member,
    *,
    reason: str,
    actor_id: int | None = None,
) -> None:
    """Kick *member* from their guild; log + emit event."""
    guild_id = member.guild.id
    target_id = member.id
    await member.kick(reason=reason)
    await db.log_mod_action(guild_id, "kick", target_id, actor_id or 0, reason)
    await bus.emit(
        EVT_MOD_ACTION,
        guild_id=guild_id,
        target_id=target_id,
        actor_id=actor_id,
        action="kick",
        reason=reason,
    )


async def ban(
    guild: discord.Guild,
    user: discord.abc.Snowflake,
    *,
    reason: str,
    actor_id: int | None = None,
) -> None:
    """Ban *user* from *guild*; log + emit event.

    Accepts ``discord.abc.Snowflake`` (Member or User) so the caller
    can ban users who are not currently in the guild.
    """
    await guild.ban(user, reason=reason)
    await db.log_mod_action(guild.id, "ban", user.id, actor_id or 0, reason)
    await bus.emit(
        EVT_MOD_ACTION,
        guild_id=guild.id,
        target_id=user.id,
        actor_id=actor_id,
        action="ban",
        reason=reason,
    )


async def unban(
    guild: discord.Guild,
    user: discord.abc.Snowflake,
    *,
    reason: str,
    actor_id: int | None = None,
) -> None:
    """Unban *user* from *guild*; log + emit event."""
    await guild.unban(user, reason=reason)
    await db.log_mod_action(guild.id, "unban", user.id, actor_id or 0, reason)
    await bus.emit(
        EVT_MOD_ACTION,
        guild_id=guild.id,
        target_id=user.id,
        actor_id=actor_id,
        action="unban",
        reason=reason,
    )


async def clear_warnings(
    guild_id: int,
    user_id: int,
    *,
    actor_id: int | None = None,
    reason: str = "Warnings cleared",
) -> None:
    """Reset *user_id*'s warning count to zero; log + emit event."""
    await db.clear_warnings(user_id, guild_id)
    await db.log_mod_action(guild_id, "clear_warnings", user_id, actor_id or 0, reason)
    await bus.emit(
        EVT_MOD_ACTION,
        guild_id=guild_id,
        target_id=user_id,
        actor_id=actor_id,
        action="clear_warnings",
        reason=reason,
    )
