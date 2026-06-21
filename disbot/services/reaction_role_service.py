"""Reaction-role config writes — the audited mutation seam.

Closes a long-standing finding (``audits/general-feature-layer-analysis``): the
role cog wrote reaction-role bindings straight to ``utils.db.roles`` with no
audit trail, unlike every other role mutation (time/XP thresholds, exemptions,
lifecycle) which routes through an audited service. This module is now the
sanctioned write path for emoji reaction-role bindings — it persists via the DB
layer and emits ``audit.action_recorded``, so reaction-role config changes show
up in the same audit/``server_logging`` stream as the rest of the role hub.

Scope: the emoji *config* writes (bind/unbind an emoji → role) are audited.
The emoji member self-assign path (adding/removing the role when someone reacts)
is a Discord mutation, not a DB write, and stays in the cog listener for now;
PR 3 layers the unique/verify modes onto the read seam here.

PR 2 adds the role-**menu** surface on top of ``utils.db.role_menus``: the
audited menu config writes (``create_menu`` / ``update_menu`` / ``delete_menu``)
and the server-side member assignment (``toggle_role`` for the button surface,
``apply_selection`` for the dropdown) with ``unique`` / ``verify`` / ``max_roles``
enforcement. Menu config changes are audited; member self-assignment is not
(high-volume + opt-in per plan §9 — the PR 5 pickup analytics cover usage).

Cycle discipline mirrors the rest of ``services``: cross-package ``services.*``
imports are function-local; top-level imports are limited to stdlib + ``utils``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import discord

from utils import db, role_feasibility
from utils.db import role_menus as menus_db


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


# ===========================================================================
# Role menus (PR 2) — config writes (audited) + member assignment (not audited)
# ===========================================================================

# Menu surface styles + assignment modes, validated at the service boundary so a
# bad value never reaches the DB or the renderer.
VALID_STYLES = ("dropdown", "button", "reaction")
VALID_MODES = ("normal", "unique", "verify")


@dataclass(frozen=True)
class RoleOption:
    """One role a menu offers (an immutable view of a ``role_menu_options`` row)."""

    role_id: int
    emoji: str | None = None
    label: str | None = None


@dataclass(frozen=True)
class RoleMenuOutcome:
    """Result of a member interaction, for the ephemeral confirmation."""

    added: tuple[int, ...] = ()
    removed: tuple[int, ...] = ()
    blocked: tuple[int, ...] = ()
    note: str = ""

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed)


async def create_menu(
    *,
    guild_id: int,
    channel_id: int,
    title: str,
    description: str | None,
    style: str,
    mode: str,
    max_roles: int,
    options: list[RoleOption],
    theme: str = "default",
    actor_id: int | None,
) -> int:
    """Create a role menu (+ its options) and return ``menu_id`` (audited)."""
    style = _validate_style(style)
    mode = _validate_mode(mode)
    max_roles = max(0, int(max_roles))

    menu_id = await menus_db.create_menu(
        guild_id,
        channel_id,
        title=title,
        description=description,
        style=style,
        mode=mode,
        max_roles=max_roles,
        theme=theme or "default",
    )
    await menus_db.replace_options(menu_id, _options_to_rows(options))
    await _emit_menu_audit(
        mutation_type="create_role_menu",
        menu_id=menu_id,
        guild_id=guild_id,
        actor_id=actor_id,
        prev_value=None,
        new_value=_summarize(title, style, mode, max_roles, options),
    )
    return menu_id


async def update_menu(
    *,
    menu_id: int,
    guild_id: int,
    title: str,
    description: str | None,
    style: str,
    mode: str,
    max_roles: int,
    options: list[RoleOption],
    theme: str = "default",
    actor_id: int | None,
) -> None:
    """Overwrite a menu's fields + options in place (edit-in-place, audited)."""
    style = _validate_style(style)
    mode = _validate_mode(mode)
    max_roles = max(0, int(max_roles))

    prev = await menus_db.get_menu(menu_id)
    prev_opts = await menus_db.get_options(menu_id)

    await menus_db.update_menu(
        menu_id,
        title=title,
        description=description,
        style=style,
        mode=mode,
        max_roles=max_roles,
        theme=theme or "default",
    )
    await menus_db.replace_options(menu_id, _options_to_rows(options))
    await _emit_menu_audit(
        mutation_type="update_role_menu",
        menu_id=menu_id,
        guild_id=guild_id,
        actor_id=actor_id,
        prev_value=(
            _summarize(
                prev["title"],
                prev["style"],
                prev["mode"],
                prev["max_roles"],
                [RoleOption(int(o["role_id"])) for o in prev_opts],
            )
            if prev
            else None
        ),
        new_value=_summarize(title, style, mode, max_roles, options),
    )


async def set_menu_message(menu_id: int, message_id: int) -> None:
    """Record the posted message id (part of the create/post flow, not audited)."""
    await menus_db.set_menu_message(menu_id, message_id)


async def delete_menu(
    *,
    menu_id: int,
    guild_id: int,
    actor_id: int | None,
) -> None:
    """Delete a menu and its options (audited)."""
    prev = await menus_db.get_menu(menu_id)
    await menus_db.delete_menu(menu_id)
    await _emit_menu_audit(
        mutation_type="delete_role_menu",
        menu_id=menu_id,
        guild_id=guild_id,
        actor_id=actor_id,
        prev_value=(prev["title"] if prev else None),
        new_value=None,
    )


# --- Reads (thin pass-throughs so callers never import the DB layer directly) --


async def get_menu(menu_id: int) -> dict | None:
    return await menus_db.get_menu(menu_id)


async def get_menu_options(menu_id: int) -> list[RoleOption]:
    rows = await menus_db.get_options(menu_id)
    return [RoleOption(int(r["role_id"]), r.get("emoji"), r.get("label")) for r in rows]


async def list_menus(guild_id: int) -> list[dict]:
    return await menus_db.list_menus(guild_id)


async def list_posted_menus() -> list[dict]:
    return await menus_db.list_posted_menus()


# --- Member self-assignment (server-side mode enforcement, NOT audited) --------


async def toggle_role(
    *,
    menu_id: int,
    member: discord.Member,
    guild: discord.Guild,
    clicked_role_id: int,
) -> RoleMenuOutcome:
    """Toggle one role for a member (button surface), honoring the menu's mode.

    Re-reads the menu + options from the DB so the menu config (mode / limit) is
    always authoritative — the caller's view state is never trusted for a
    privileged mutation.
    """
    menu = await menus_db.get_menu(menu_id)
    if menu is None:
        return RoleMenuOutcome(note="This menu no longer exists.")
    option_ids = await _option_ids(menu_id)
    if clicked_role_id not in option_ids:
        return RoleMenuOutcome(note="That role isn't part of this menu.")

    mode = menu["mode"]
    max_roles = int(menu["max_roles"])
    held = _held_menu_roles(member, option_ids)
    has_clicked = clicked_role_id in held

    if has_clicked and mode != "verify":
        return await _apply(
            member,
            to_add=(),
            to_remove=(clicked_role_id,),
            guild=guild,
        )
    if has_clicked and mode == "verify":
        return RoleMenuOutcome(note="You already have that role (verify menu).")

    # Adding a role the member doesn't hold yet.
    if mode == "unique":
        siblings = tuple(r for r in held if r != clicked_role_id)
        return await _apply(
            member,
            to_add=(clicked_role_id,),
            to_remove=siblings,
            guild=guild,
        )
    if max_roles and len(held) >= max_roles:
        return RoleMenuOutcome(
            blocked=(clicked_role_id,),
            note=f"You can pick at most {max_roles} role(s) here — remove one first.",
        )
    return await _apply(member, to_add=(clicked_role_id,), to_remove=(), guild=guild)


async def apply_selection(
    *,
    menu_id: int,
    member: discord.Member,
    guild: discord.Guild,
    selected_ids: list[int],
) -> RoleMenuOutcome:
    """Reconcile a member's menu roles to ``selected_ids`` (dropdown surface).

    The dropdown is stateless on a shared message, so each submission *sets* the
    member's menu-roles to exactly what they picked: add the newly-selected,
    remove the de-selected. Mode rules: ``unique`` keeps at most one; ``verify``
    only ever adds; ``max_roles`` caps the count.
    """
    menu = await menus_db.get_menu(menu_id)
    if menu is None:
        return RoleMenuOutcome(note="This menu no longer exists.")
    option_ids = await _option_ids(menu_id)
    mode = menu["mode"]
    max_roles = int(menu["max_roles"])

    desired = [rid for rid in selected_ids if rid in option_ids]
    if mode == "unique":
        desired = desired[:1]
    elif max_roles:
        desired = desired[:max_roles]
    desired_set = set(desired)

    held = _held_menu_roles(member, option_ids)
    to_add = tuple(rid for rid in desired_set if rid not in held)
    # verify mode never removes a role the member already earned.
    to_remove = (
        () if mode == "verify" else tuple(rid for rid in held if rid not in desired_set)
    )
    return await _apply(member, to_add=to_add, to_remove=to_remove, guild=guild)


# --- Internal helpers ------------------------------------------------------


async def _option_ids(menu_id: int) -> set[int]:
    rows = await menus_db.get_options(menu_id)
    return {int(r["role_id"]) for r in rows}


def _held_menu_roles(member: discord.Member, option_ids: set[int]) -> set[int]:
    """The subset of this menu's roles the member currently holds."""
    return {r.id for r in member.roles} & option_ids


async def _apply(
    member: discord.Member,
    *,
    to_add: tuple[int, ...],
    to_remove: tuple[int, ...],
    guild: discord.Guild,
) -> RoleMenuOutcome:
    """Resolve role ids, drop ones the bot can't manage, then add/remove."""
    add_roles, add_blocked = _resolve_manageable(guild, to_add)
    remove_roles, remove_blocked = _resolve_manageable(guild, to_remove)

    added: tuple[int, ...] = ()
    removed: tuple[int, ...] = ()
    blocked = tuple(add_blocked) + tuple(remove_blocked)

    if add_roles:
        try:
            await member.add_roles(*add_roles, reason="Role menu")
            added = tuple(r.id for r in add_roles)
        except discord.Forbidden:
            blocked += tuple(r.id for r in add_roles)
    if remove_roles:
        try:
            await member.remove_roles(*remove_roles, reason="Role menu")
            removed = tuple(r.id for r in remove_roles)
        except discord.Forbidden:
            blocked += tuple(r.id for r in remove_roles)

    note = ""
    if blocked and not (added or removed):
        note = "I can't manage that role (it's above my highest role)."
    return RoleMenuOutcome(added=added, removed=removed, blocked=blocked, note=note)


def _resolve_manageable(
    guild: discord.Guild,
    role_ids: tuple[int, ...],
) -> tuple[list[discord.Role], list[int]]:
    """Split role ids into (manageable Role objects, blocked ids)."""
    from core.runtime import resources

    manageable: list[discord.Role] = []
    blocked: list[int] = []
    for rid in role_ids:
        role = resources.resolve_role(guild, role_id=rid)
        if role is None:
            blocked.append(rid)
            continue
        if role_feasibility.evaluate_role(role, bot_member=guild.me).ok:
            manageable.append(role)
        else:
            blocked.append(rid)
    return manageable, blocked


def _validate_style(style: str) -> str:
    return style if style in VALID_STYLES else "dropdown"


def _validate_mode(mode: str) -> str:
    return mode if mode in VALID_MODES else "normal"


def _options_to_rows(
    options: list[RoleOption],
) -> list[tuple[int, str | None, str | None]]:
    return [(o.role_id, o.emoji, o.label) for o in options]


def _summarize(
    title: str,
    style: str,
    mode: str,
    max_roles: int,
    options: list[RoleOption],
) -> str:
    limit = "∞" if not max_roles else str(max_roles)
    return f"{title!r} [{style}/{mode}, limit={limit}, {len(options)} role(s)]"


async def _emit_menu_audit(
    *,
    mutation_type: str,
    menu_id: int,
    guild_id: int,
    actor_id: int | None,
    prev_value: str | None,
    new_value: str | None,
) -> None:
    from services.audit_events import emit_audit_action

    await emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="role",
        mutation_type=mutation_type,
        target=f"role_menu:{menu_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=prev_value,
        new_value=new_value,
        actor_id=actor_id,
        actor_type="admin",
        occurred_at=datetime.now(tz=timezone.utc),
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
    "VALID_MODES",
    "VALID_STYLES",
    "RoleMenuOutcome",
    "RoleOption",
    "apply_selection",
    "bind_emoji",
    "create_menu",
    "delete_menu",
    "get_binding",
    "get_menu",
    "get_menu_options",
    "list_bindings",
    "list_menus",
    "list_posted_menus",
    "set_menu_message",
    "toggle_role",
    "unbind_emoji",
    "update_menu",
]
