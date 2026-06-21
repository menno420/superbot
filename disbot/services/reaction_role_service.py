"""Reaction-role config writes — the audited mutation seam.

Closes a long-standing finding (``audits/general-feature-layer-analysis``): the
role cog wrote reaction-role bindings straight to ``utils.db.roles`` with no
audit trail, unlike every other role mutation (time/XP thresholds, exemptions,
lifecycle) which routes through an audited service. This module is now the
sanctioned write path for emoji reaction-role bindings — it persists via the DB
layer and emits ``audit.action_recorded``, so reaction-role config changes show
up in the same audit/``server_logging`` stream as the rest of the role hub.

Scope (PR 1): the *config* writes (bind/unbind an emoji → role) are audited.
The member self-assign path (adding/removing the role when someone reacts) is a
Discord mutation, not a DB write, and stays in the cog listener for now; PR 3
layers the unique/verify modes onto the read seam here. The role-menu write
methods land in PR 2 on top of ``utils.db.role_menus``.

Cycle discipline mirrors the rest of ``services``: cross-package ``services.*``
imports are function-local; top-level imports are limited to stdlib + ``utils``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from utils import db


async def bind_emoji(
    guild_id: int,
    message_id: int,
    emoji: str,
    role_id: int,
    *,
    actor_id: int | None,
) -> None:
    """Bind an emoji on a message to a role (audited).

    Upserts the ``reaction_roles`` row and emits ``audit.action_recorded`` so
    the operator action is traceable.
    """
    await db.add_reaction_role(guild_id, message_id, emoji, role_id)
    await _emit(
        guild_id,
        mutation_type="set_reaction_role",
        role_id=role_id,
        prev_value=None,
        new_value=f"message={message_id},emoji={emoji}",
        actor_id=actor_id,
    )


async def unbind_emoji(
    guild_id: int,
    message_id: int,
    emoji: str,
    *,
    actor_id: int | None,
) -> None:
    """Remove an emoji → role binding from a message (audited)."""
    prev_role = await db.get_reaction_role(guild_id, message_id, emoji)
    await db.remove_reaction_role(guild_id, message_id, emoji)
    await _emit(
        guild_id,
        mutation_type="remove_reaction_role",
        role_id=prev_role,
        prev_value=f"message={message_id},emoji={emoji}",
        new_value=None,
        actor_id=actor_id,
    )


async def get_binding(guild_id: int, message_id: int, emoji: str) -> int | None:
    """Resolve the role bound to an emoji on a message (the listener read)."""
    return await db.get_reaction_role(guild_id, message_id, emoji)


async def list_bindings(guild_id: int) -> list[dict]:
    """All emoji reaction-role bindings configured in a guild."""
    return await db.get_all_reaction_roles(guild_id)


async def _emit(
    guild_id: int,
    *,
    mutation_type: str,
    role_id: int | None,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
) -> None:
    """Emit ``audit.action_recorded`` for a reaction-role config mutation."""
    from services.audit_events import emit_audit_action

    await emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="role",
        mutation_type=mutation_type,
        target=f"role:{role_id}" if role_id is not None else "role:unknown",
        scope="guild",
        guild_id=guild_id,
        prev_value=prev_value,
        new_value=new_value,
        actor_id=actor_id,
        actor_type="admin",
        occurred_at=datetime.now(tz=timezone.utc),
    )


__all__ = [
    "bind_emoji",
    "get_binding",
    "list_bindings",
    "unbind_emoji",
]
