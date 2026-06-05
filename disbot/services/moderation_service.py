"""Moderation service — single audited path for moderation actions.

Mirrors :mod:`services.economy_service`: every moderation action
(warn, timeout, kick, ban, unban, clear_warnings) routes through one
function that fans out **three distinct signals** via the shared
:func:`_record_action` helper (the same shape
:mod:`services.resource_provisioning` uses):

  1. **``mod_logs`` row** via :func:`utils.db.log_mod_action` — the
     authoritative, append-only moderation history.  It is the source of
     truth for ``modlogs`` lookups and never carries a ``mutation_id``
     column.
  2. **``audit.action_recorded``** via :func:`services.audit_events.emit_audit_action`
     — the *generic audit-routing companion* consumed by
     ``services.server_logging`` (single canonical embed to the audit
     channel).  It is NOT a second moderation-history store.
  3. **``EVT_MOD_ACTION``** (``moderation.action_taken``) — the domain
     event panel-refresh / analytics subscribers dispatch on, carrying
     the same ``mutation_id`` for correlation.

Signals (2) and (3) are **best-effort**: the audit companion swallows
bus failures internally (returns ``False``) and never invalidates the
``mod_logs`` row.

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
context-dependent.  The audit/log fan-out only runs after the Discord
action succeeds.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import discord

from core.events import bus
from services.audit_events import emit_audit_action
from utils import db

logger = logging.getLogger("bot.moderation_service")

# Single event covers every moderation action; subscribers dispatch
# on payload["action"].  Also listed in core/events_catalogue.KNOWN_EVENTS.
EVT_MOD_ACTION = "moderation.action_taken"


def _now_utc() -> datetime:
    """Return a tz-aware "now" — INV-N forbids bare datetime.utcnow."""
    return datetime.now(timezone.utc)


async def _record_action(
    *,
    guild_id: int,
    action: str,
    target_id: int,
    actor_id: int | None,
    reason: str,
    actor_type: str = "moderator",
    event_extra: dict[str, Any] | None = None,
) -> str:
    """Append the canonical ``mod_logs`` row and fan out both events.

    Three signals per call (see module docstring):

      1. ``mod_logs`` row — authoritative history (issued first).
      2. ``audit.action_recorded`` — best-effort audit-routing companion.
      3. ``EVT_MOD_ACTION`` — best-effort domain event.

    Returns the issued ``mutation_id`` (shared by both events).  The
    companion / event emits are best-effort and must never invalidate
    the ``mod_logs`` row; the audit helper already swallows bus errors,
    and a domain-event failure is not the service's concern here.
    """
    mutation_id = str(uuid.uuid4())
    await db.log_mod_action(guild_id, action, target_id, actor_id or 0, reason)
    logger.info(
        "MOD | %s | target=%s | actor=%s | %s",
        action.upper(),
        target_id,
        actor_id,
        reason,
    )
    await emit_audit_action(
        mutation_id=mutation_id,
        subsystem="moderation",
        mutation_type=action,
        target=f"user:{target_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=None,
        new_value=reason or None,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=_now_utc(),
    )
    await bus.emit(
        EVT_MOD_ACTION,
        mutation_id=mutation_id,
        guild_id=guild_id,
        target_id=target_id,
        actor_id=actor_id,
        action=action,
        reason=reason,
        **(event_extra or {}),
    )
    return mutation_id


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
    await _record_action(
        guild_id=member.guild.id,
        action="warn",
        target_id=member.id,
        actor_id=actor_id,
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
    await _record_action(
        guild_id=member.guild.id,
        action="timeout",
        target_id=member.id,
        actor_id=actor_id,
        reason=reason,
        event_extra={"until": until.isoformat() if until else None},
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
    await _record_action(
        guild_id=guild_id,
        action="kick",
        target_id=target_id,
        actor_id=actor_id,
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
    await _record_action(
        guild_id=guild.id,
        action="ban",
        target_id=user.id,
        actor_id=actor_id,
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
    await _record_action(
        guild_id=guild.id,
        action="unban",
        target_id=user.id,
        actor_id=actor_id,
        reason=reason,
    )


async def clear_warnings(
    guild_id: int,
    user_id: int,
    *,
    actor_id: int | None = None,
    reason: str = "Warnings cleared",
) -> None:
    """Reset *user_id*'s warning count to zero; log + emit event.

    The stored ``mod_logs`` action token is ``"clearwarnings"`` (one
    word) to match every row written by the pre-convergence cog/modal
    surfaces, so history stays consistent and ``modlogs`` renders a
    single label.
    """
    await db.clear_warnings(user_id, guild_id)
    await _record_action(
        guild_id=guild_id,
        action="clearwarnings",
        target_id=user_id,
        actor_id=actor_id,
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

    await _record_action(
        guild_id=message.guild.id,
        action=composite_action,
        target_id=message.author.id,
        actor_id=actor_id,
        reason=reason,
        actor_type="system",
    )
    return True
