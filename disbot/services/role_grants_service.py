"""Temporary role grants — the audited grant + expiry-sweep seam (PR 4).

Carl-bot's timed roles are a Patreon perk; this offers them free. An operator
grants a role "for 2h" (``!temprole`` / a future menu option); the grant is
persisted with an ``expires_at`` and ``RoleGrantsCog`` periodically calls
:func:`sweep_expired` to remove the role once it lapses.

All DB access goes through :mod:`utils.db.role_grants`; both the grant and the
expiry removal emit ``audit.action_recorded`` (the grant as an ``admin`` action,
the expiry as a ``system`` one), per the mutation contract
(``docs/runtime_contracts.md`` §9).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

import discord

from core.runtime import resources
from utils.db import role_grants as grants_db

logger = logging.getLogger("bot.services.role_grants")


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


async def grant_temp_role(
    guild: discord.Guild,
    member: discord.Member,
    role: discord.Role,
    *,
    seconds: int,
    actor_id: int | None,
) -> datetime:
    """Give ``member`` ``role`` until ``now + seconds`` (audited). Returns the expiry.

    The caller is expected to have verified the role is manageable; a late
    ``Forbidden`` from :meth:`add_roles` propagates so the command surfaces it.
    """
    expires_at = _utcnow() + timedelta(seconds=seconds)
    await member.add_roles(role, reason="Temporary role")
    await grants_db.grant(
        guild.id,
        member.id,
        role.id,
        expires_at,
        granted_by=actor_id,
    )
    await _emit(
        guild.id,
        member_id=member.id,
        role_id=role.id,
        mutation_type="grant_temp_role",
        new_value=f"expires={expires_at.isoformat()}",
        actor_id=actor_id,
        actor_type="admin",
    )
    return expires_at


async def sweep_expired(guild: discord.Guild) -> int:
    """Remove every lapsed temp role in ``guild`` and drop its row.

    Returns the number of grants resolved. A role the bot can no longer manage
    (moved above it) is **kept** so a later sweep retries once hierarchy is
    fixed; a member/role that has gone away is cleaned up with no mutation.
    """
    now = _utcnow()
    expired = await grants_db.list_expired(guild.id, now)
    resolved = 0
    for row in expired:
        grant_id = int(row["grant_id"])
        member = resources.resolve_member(guild, int(row["member_id"]))
        role = resources.resolve_role(guild, role_id=int(row["role_id"]))
        if member is None or role is None:
            await grants_db.delete_grant(grant_id)
            resolved += 1
            continue

        did_remove = False
        if role in member.roles:
            try:
                await member.remove_roles(role, reason="Temporary role expired")
                did_remove = True
            except discord.Forbidden:
                logger.warning(
                    "role_grants: cannot remove expired role %s from member %s in "
                    "guild %s (above my top role); keeping the grant to retry",
                    role.id,
                    member.id,
                    guild.id,
                )
                continue
            except discord.HTTPException:
                continue

        await grants_db.delete_grant(grant_id)
        if did_remove:
            await _emit(
                guild.id,
                member_id=member.id,
                role_id=role.id,
                mutation_type="expire_temp_role",
                new_value=None,
                actor_id=None,
                actor_type="system",
            )
        resolved += 1
    return resolved


async def _emit(
    guild_id: int,
    *,
    member_id: int,
    role_id: int,
    mutation_type: str,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str,
) -> None:
    """Emit ``audit.action_recorded`` for a temp-role grant / expiry."""
    from services.audit_events import emit_audit_action

    await emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="role",
        mutation_type=mutation_type,
        target=f"role:{role_id}:member:{member_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=None,
        new_value=new_value,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=_utcnow(),
    )


__all__ = ["grant_temp_role", "sweep_expired"]
