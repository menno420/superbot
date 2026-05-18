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
- :func:`auto_delete(message, *, reason, rule, actor_id)` — rule-based
                                                            auto-mod delete
                                                            (§3.2 hook)

All functions emit ``EVT_MOD_ACTION`` with the same payload shape so
subscribers can dispatch on the ``action`` field.  Auto-mod deletions
prefix their rule id under ``"auto_delete:<rule>"`` so dashboards can
filter per-rule.

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


async def auto_delete(
    message: discord.Message,
    *,
    reason: str,
    rule: str,
    actor_id: int | None = None,
) -> bool:
    """Auto-mod message deletion; log + emit event.

    System-initiated counterpart to :func:`warn` / :func:`timeout` / etc.
    The action is rule-based (e.g. blocked-command policy, prohibited-words
    list, counting violation), not authorized by a moderator — pass
    ``actor_id=None`` so the audit row records ``actor_id=0``.

    Discord-API exceptions are caught here (unlike the other functions in
    this module) because rule-based moderation has no useful error surface
    to escalate to: a single failed delete shouldn't crash the message
    pipeline or block subsequent stages.  The exception is logged with the
    rule id for triage.

    Args:
        message: target Discord message (must be in a guild).
        reason: short human-readable attribution string surfaced to the
                audit dashboard (e.g. "prohibited word: <redacted>").
        rule: machine-readable rule id (e.g. ``"cleanup.command_policy"``
              or ``"cleanup.prohibited_words"``).  Stored as the suffix on
              the ``action`` column so dashboards can filter per-rule:
              ``action == "auto_delete:cleanup.prohibited_words"``.
        actor_id: invoking user's id, or ``None`` for system-initiated.

    Returns:
        True if the delete succeeded (or the message was already gone, in
        which case the rule trigger is still logged for audit completeness);
        False on Forbidden / HTTPException.
    """
    if message.guild is None:
        # Can't audit a DM delete — the schema is keyed on guild_id.
        return False

    composite_action = f"auto_delete:{rule}"

    try:
        await message.delete()
    except discord.NotFound:
        # Already deleted by another stage or out-of-band — still record
        # the rule trigger so the audit row exists.
        pass
    except discord.Forbidden:
        logger.warning(
            "auto_delete: missing permission to delete message %d in guild %s "
            "(rule=%s)",
            message.id,
            message.guild.name,
            rule,
        )
        return False
    except discord.HTTPException as exc:
        logger.warning(
            "auto_delete: HTTP error deleting message %d (rule=%s): %s",
            message.id,
            rule,
            exc,
        )
        return False

    await db.log_mod_action(
        message.guild.id,
        composite_action,
        message.author.id,
        actor_id or 0,
        reason,
    )
    await bus.emit(
        EVT_MOD_ACTION,
        guild_id=message.guild.id,
        target_id=message.author.id,
        actor_id=actor_id,
        action=composite_action,
        reason=reason,
    )
    return True
