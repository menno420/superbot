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
from utils.db import role_menus as menu_db


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


# ---------------------------------------------------------------------------
# Role menus (PR 2) — the modern button/dropdown surface, audited at the
# *config* level (create / edit / delete). Member self-assignment is a Discord
# mutation handled in the view; per-assignment audit is an opt-in toggle (plan
# §9) and is not emitted here.
# ---------------------------------------------------------------------------


async def create_menu(
    guild_id: int,
    channel_id: int,
    *,
    title: str,
    description: str | None,
    style: str,
    mode: str,
    max_roles: int,
    theme: str,
    role_options: list[dict],
    actor_id: int | None,
) -> int:
    """Create a role menu + its options (audited); return the new ``menu_id``.

    ``role_options`` is a list of ``{"role_id", "emoji"?, "label"?, "position"?}``
    dicts. The caller posts the menu message afterward and records its id via
    :func:`set_menu_message`.
    """
    menu_id = await menu_db.create_menu(
        guild_id,
        channel_id,
        title=title,
        description=description,
        style=style,
        mode=mode,
        max_roles=max_roles,
        theme=theme,
    )
    await _replace_options(menu_id, role_options)
    await _emit(
        guild_id,
        mutation_type="create_role_menu",
        role_id=None,
        prev_value=None,
        new_value=_menu_summary(menu_id, title, style, mode, role_options),
        actor_id=actor_id,
    )
    return menu_id


async def update_menu(
    menu_id: int,
    guild_id: int,
    *,
    title: str,
    description: str | None,
    style: str,
    mode: str,
    max_roles: int,
    theme: str,
    role_options: list[dict],
    actor_id: int | None,
) -> None:
    """Edit a menu's fields + options in place (audited; plan §4.6a).

    The caller re-renders and edits the live message afterward so the posted
    menu and the row stay in step without a repost.
    """
    await menu_db.update_menu(
        menu_id,
        title=title,
        description=description,
        style=style,
        mode=mode,
        max_roles=max_roles,
        theme=theme,
    )
    await _replace_options(menu_id, role_options)
    await _emit(
        guild_id,
        mutation_type="update_role_menu",
        role_id=None,
        prev_value=f"menu={menu_id}",
        new_value=_menu_summary(menu_id, title, style, mode, role_options),
        actor_id=actor_id,
    )


async def delete_menu(menu_id: int, guild_id: int, *, actor_id: int | None) -> None:
    """Delete a menu (and, by cascade, its options) — audited."""
    await menu_db.delete_menu(menu_id)
    await _emit(
        guild_id,
        mutation_type="delete_role_menu",
        role_id=None,
        prev_value=f"menu={menu_id}",
        new_value=None,
        actor_id=actor_id,
    )


async def set_menu_message(menu_id: int, message_id: int) -> None:
    """Record the posted message id for a menu (build → post → store)."""
    await menu_db.set_menu_message(menu_id, message_id)


async def get_menu(menu_id: int) -> dict | None:
    """Read a single menu row (the view/builder load path)."""
    return await menu_db.get_menu(menu_id)


async def get_menu_by_message(guild_id: int, message_id: int) -> dict | None:
    """Resolve the menu bound to a posted message."""
    return await menu_db.get_menu_by_message(guild_id, message_id)


async def get_menu_options(menu_id: int) -> list[dict]:
    """All role options for a menu, in display order."""
    return await menu_db.get_options(menu_id)


async def list_menus(guild_id: int) -> list[dict]:
    """All role menus configured in a guild (newest first)."""
    return await menu_db.list_menus(guild_id)


async def _replace_options(menu_id: int, role_options: list[dict]) -> None:
    """Set a menu's options to exactly ``role_options`` (add/update + prune)."""
    desired = {int(o["role_id"]): o for o in role_options}
    existing = {int(o["role_id"]) for o in await menu_db.get_options(menu_id)}
    for role_id in existing - desired.keys():
        await menu_db.remove_option(menu_id, role_id)
    for position, (role_id, opt) in enumerate(desired.items()):
        await menu_db.add_option(
            menu_id,
            role_id,
            emoji=opt.get("emoji"),
            label=opt.get("label"),
            position=int(opt.get("position", position)),
        )


def _menu_summary(
    menu_id: int,
    title: str,
    style: str,
    mode: str,
    role_options: list[dict],
) -> str:
    """Compact, log-safe description of a menu mutation for the audit row."""
    return (
        f"menu={menu_id},title={title!r},style={style},"
        f"mode={mode},roles={len(role_options)}"
    )


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
    "create_menu",
    "delete_menu",
    "get_binding",
    "get_menu",
    "get_menu_by_message",
    "get_menu_options",
    "list_bindings",
    "list_menus",
    "set_menu_message",
    "unbind_emoji",
    "update_menu",
]
