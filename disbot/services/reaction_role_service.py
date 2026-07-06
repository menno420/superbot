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

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import discord

from utils import db, role_feasibility
from utils.db import role_menus as menus_db

logger = logging.getLogger("bot.services.reaction_role")


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
    actor_type: str = "admin",
) -> None:
    """Remove an emoji → role binding from a message (audited).

    ``actor_type`` defaults to ``"admin"`` (an operator removal); the listener
    self-heal passes ``"system"`` so an automatic dead-binding cleanup is
    distinguishable in the audit stream.
    """
    prev_role = await db.get_reaction_role(guild_id, message_id, emoji)
    await db.remove_reaction_role(guild_id, message_id, emoji)
    await _emit(
        guild_id,
        mutation_type="remove_reaction_role",
        role_id=prev_role,
        prev_value=f"message={message_id},emoji={emoji}",
        new_value=None,
        actor_id=actor_id,
        actor_type=actor_type,
    )


async def get_binding(guild_id: int, message_id: int, emoji: str) -> int | None:
    """Resolve the role bound to an emoji on a message (the listener read)."""
    return await db.get_reaction_role(guild_id, message_id, emoji)


async def list_bindings(guild_id: int) -> list[dict]:
    """All emoji reaction-role bindings configured in a guild."""
    return await db.get_all_reaction_roles(guild_id)


async def count_dead_bindings(guild: discord.Guild) -> int:
    """How many emoji bindings point to a role that no longer exists (read-only)."""
    from core.runtime import resources

    return sum(
        1
        for r in await list_bindings(guild.id)
        if resources.resolve_role(guild, role_id=int(r["role_id"])) is None
    )


async def prune_dead_bindings(
    guild: discord.Guild,
    *,
    actor_id: int | None,
) -> list[dict]:
    """Remove every emoji binding whose role no longer exists (audited).

    Reaction-role config silently rots when a bound role is deleted — the binding
    lingers as ``emoji → (deleted role N)`` and can never assign anything. This
    clears those dead rows through the audited :func:`unbind_emoji` seam and
    returns the removed rows (for an operator-facing summary). Live bindings are
    untouched. The creation-side fix lives in the Add flow (#1234); this is the
    cleanup for rows already left behind.
    """
    from core.runtime import resources

    removed: list[dict] = []
    for r in await list_bindings(guild.id):
        if resources.resolve_role(guild, role_id=int(r["role_id"])) is None:
            await unbind_emoji(
                guild.id,
                int(r["message_id"]),
                r["emoji"],
                actor_id=actor_id,
            )
            removed.append(r)
    return removed


# ===========================================================================
# Emoji-surface modes (PR 3) — Carl's `rr <mode> <msg_id>`, per message
# ===========================================================================
# A mode is a property of a reaction-role *message*: 'normal' (react adds /
# un-react removes), 'unique' (one role per message — reacting swaps the
# member's previous pick), or 'verify' (react only ever ADDS; the bot removes
# the reaction afterward and un-reacting never strips the role). Config writes
# are audited; the member self-assign path is not (high-volume, plan §9).


async def reaction_roles_enabled(guild_id: int) -> bool:
    """Whether the emoji reaction-role surface is active for a guild.

    Defaults to ``True`` so every existing binding keeps working after the
    overhaul (the PR-1 zero-behaviour-change guarantee) — an operator can turn
    the whole emoji surface off per guild via the Role settings
    (``reaction_roles_enabled``). Consumed by the ``role_cog`` reaction
    listeners; this is the settings-bridge read (plan §4 PR 3).
    """
    from services.settings_resolution import resolve_value

    return bool(await resolve_value(guild_id, "role", "reaction_roles_enabled", True))


async def set_message_mode(
    *,
    guild_id: int,
    message_id: int,
    mode: str,
    actor_id: int | None,
) -> str:
    """Set a reaction-role message's mode (audited). Returns the stored mode."""
    mode = _validate_mode(mode)
    await db.set_reaction_message_mode(guild_id, message_id, mode)
    await _emit_mode(
        guild_id,
        message_id=message_id,
        prev_value=None,
        new_value=mode,
        actor_id=actor_id,
    )
    return mode


async def get_message_mode(guild_id: int, message_id: int) -> str:
    """Resolve a message's reaction mode (``'normal'`` when unset)."""
    return await db.get_reaction_message_mode(guild_id, message_id)


async def clear_message_mode(
    *,
    guild_id: int,
    message_id: int,
    actor_id: int | None,
) -> None:
    """Reset a message back to the default ``'normal'`` mode (audited)."""
    await db.clear_reaction_message_mode(guild_id, message_id)
    await _emit_mode(
        guild_id,
        message_id=message_id,
        prev_value=None,
        new_value="normal",
        actor_id=actor_id,
    )


async def list_message_modes(guild_id: int) -> dict[int, str]:
    """Map of ``message_id → mode`` for every message with a non-default mode."""
    rows = await db.get_reaction_message_modes(guild_id)
    return {int(r["message_id"]): r["mode"] for r in rows}


async def handle_reaction_add(
    guild: discord.Guild,
    member: discord.Member,
    message_id: int,
    emoji: str,
) -> tuple[RoleMenuOutcome | None, bool]:
    """Apply a reaction-add for the emoji surface, honoring the message's mode.

    Returns ``(outcome, remove_reaction)`` — ``outcome`` is ``None`` when the
    emoji isn't bound to a role; ``remove_reaction`` is ``True`` for ``verify``
    mode so the caller strips the member's reaction (the message stays clean).
    """
    role_id = await db.get_reaction_role(guild.id, message_id, emoji)
    if role_id is None:
        return None, False
    if not await reaction_roles_enabled(guild.id):
        return None, False
    if await _self_heal_dead_binding(guild, message_id, emoji, role_id):
        return None, False
    mode = await db.get_reaction_message_mode(guild.id, message_id)
    if mode == "unique":
        siblings = await _held_sibling_reaction_roles(
            guild,
            member,
            message_id,
            keep=role_id,
        )
        return (
            await _apply(
                member,
                to_add=(role_id,),
                to_remove=siblings,
                guild=guild,
            ),
            False,
        )
    if mode == "verify":
        return (
            await _apply(
                member,
                to_add=(role_id,),
                to_remove=(),
                guild=guild,
            ),
            True,
        )
    return await _apply(member, to_add=(role_id,), to_remove=(), guild=guild), False


async def handle_reaction_remove(
    guild: discord.Guild,
    member: discord.Member,
    message_id: int,
    emoji: str,
) -> RoleMenuOutcome | None:
    """Apply a reaction-remove for the emoji surface, honoring the message's mode.

    ``normal`` / ``unique`` strip the role on un-react; ``verify`` never does
    (it is add-only), so this is a no-op there.
    """
    role_id = await db.get_reaction_role(guild.id, message_id, emoji)
    if role_id is None:
        return None
    if not await reaction_roles_enabled(guild.id):
        return None
    if await _self_heal_dead_binding(guild, message_id, emoji, role_id):
        return None
    mode = await db.get_reaction_message_mode(guild.id, message_id)
    if mode == "verify":
        return None
    return await _apply(member, to_add=(), to_remove=(role_id,), guild=guild)


async def _self_heal_dead_binding(
    guild: discord.Guild,
    message_id: int,
    emoji: str,
    role_id: int,
) -> bool:
    """Drop a binding whose role was deleted, the moment a member reacts on it.

    A binding to a deleted role can never assign anything, so the first reaction
    that hits it is a definitive signal it is dead — remove it (audited as a
    ``system`` action) so dead config self-heals without an operator opening the
    panel (the manual 🧹 Clean up button covers the rest). Roles are fully cached
    in discord.py, so ``resolve_role`` returning ``None`` means genuinely deleted,
    not a transient cache miss.
    """
    from core.runtime import resources

    if resources.resolve_role(guild, role_id=role_id) is not None:
        return False
    await unbind_emoji(guild.id, message_id, emoji, actor_id=None, actor_type="system")
    return True


async def _held_sibling_reaction_roles(
    guild: discord.Guild,
    member: discord.Member,
    message_id: int,
    *,
    keep: int,
) -> tuple[int, ...]:
    """The other roles on this message the member holds (unique-mode swap set)."""
    rows = await db.get_reaction_roles_for_message(guild.id, message_id)
    sibling_ids = {int(r["role_id"]) for r in rows}
    held = {r.id for r in member.roles}
    return tuple((sibling_ids & held) - {keep})


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
    card_template: str | None = None,
    card_text: str | None = None,
    show_counts: bool = False,
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
        card_template=card_template or None,
        card_text=card_text or None,
        show_counts=bool(show_counts),
    )
    await menus_db.replace_options(menu_id, _options_to_rows(options))
    await _emit_menu_audit(
        mutation_type="create_role_menu",
        menu_id=menu_id,
        guild_id=guild_id,
        actor_id=actor_id,
        prev_value=None,
        new_value=_summarize(title, style, mode, max_roles, options, show_counts),
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
    card_template: str | None = None,
    card_text: str | None = None,
    show_counts: bool = False,
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
        card_template=card_template or None,
        card_text=card_text or None,
        show_counts=bool(show_counts),
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
                bool(prev.get("show_counts")),
            )
            if prev
            else None
        ),
        new_value=_summarize(title, style, mode, max_roles, options, show_counts),
    )


async def set_menu_message(menu_id: int, message_id: int) -> None:
    """Record the posted message id (part of the create/post flow, not audited)."""
    await menus_db.set_menu_message(menu_id, message_id)


async def set_menu_location(menu_id: int, channel_id: int, message_id: int) -> None:
    """Record a reposted menu's new channel + message (post-flow, not audited).

    Used by the manager's **Repost** action, which re-sends a saved menu (e.g.
    after its message was deleted, or to relocate it). The menu's config is
    unchanged, so this mirrors :func:`set_menu_message` rather than the audited
    ``update_menu`` seam.
    """
    await menus_db.set_menu_location(menu_id, channel_id, message_id)


# ===========================================================================
# Colour-role auto-create — pick a colour, get a role (audited via lifecycle)
# ===========================================================================
# The builder lets an operator pick colours that don't exist as roles yet and
# have the bot create them in one step (owner direction, 2026-06-21). Creation
# goes through the audited ``RoleLifecycleService`` (the only sanctioned
# ``create_role`` caller), never raw ``guild.create_role`` from the view.


def supports_role_gradients(guild: discord.Guild) -> bool:
    """Whether the guild can use Enhanced Role Styles (gradient / holographic).

    Discord unlocks the perk at **3 applied server boosts** (independent of boost
    *level*) and advertises it as a guild feature. Matched defensively — the exact
    flag string shifted during rollout — so the builder offers gradient options
    only when the server can actually use them. The create path also degrades on a
    rejected gradient, so a stale ``True`` here is never fatal.
    """
    feats = {str(f).upper() for f in (getattr(guild, "features", None) or [])}
    if {"ENHANCED_ROLE_COLORS", "ENHANCED_ROLE_COLOURS"} & feats:
        return True
    return any("ROLE" in f and ("COLOR" in f or "COLOUR" in f) for f in feats)


async def ensure_role(
    guild: discord.Guild,
    *,
    name: str,
    color: discord.Color,
    hoist: bool = False,
    mentionable: bool = False,
    secondary: discord.Color | None = None,
    tertiary: discord.Color | None = None,
    actor: object | None,
    reason: str = "Bulk role creation",
) -> tuple[int | None, bool, str]:
    """Reuse a same-named role, or create one via the audited lifecycle seam.

    The general "make sure this role exists" primitive shared by the colour
    auto-create flow (:func:`ensure_color_role`) and the bulk role-pack flows
    (creation panel + menu builder). Returns ``(role_id, created, note)``.

    When ``secondary`` is given it attempts an Enhanced-Role-Styles gradient; a
    gradient Discord rejects falls back to a solid colour so the operator still
    gets a role. The **caller** decides whether a gradient is appropriate (e.g.
    only on guilds with the perk — see :func:`ensure_color_role`); this seam just
    attempts what it's handed and degrades. Creation goes through the audited
    ``RoleLifecycleService`` (the only sanctioned ``create_role`` caller), never
    raw ``guild.create_role`` from a view.
    """
    from core.runtime import resources
    from services.role_lifecycle_service import (
        RoleLifecycleRequest,
        RoleLifecycleService,
    )

    name = (name or "").strip()[:100] or "role"
    existing = resources.resolve_role(guild, name=name)
    if existing is not None:
        return existing.id, False, ""

    svc = RoleLifecycleService()

    async def _create(
        sec: discord.Color | None,
        ter: discord.Color | None,
    ) -> tuple[int | None, str]:
        result = await svc.apply(
            guild,
            RoleLifecycleRequest(
                operation="create",
                name=name,
                color=color,
                hoist=hoist,
                mentionable=mentionable,
                secondary_color=sec,
                tertiary_color=ter,
                reason=reason,
            ),
            actor,
            actor_type="admin",
        )
        applied = result.applied
        if applied and applied[0].target_id:
            return int(applied[0].target_id), ""
        return None, result.first_error

    role_id, note = await _create(secondary, tertiary)
    if role_id is None and secondary is not None:
        # The gradient may have been rejected — retry as a plain solid colour.
        role_id, note = await _create(None, None)
        if role_id is not None:
            note = "Gradient unavailable here — created a solid colour role."
    return role_id, role_id is not None, note


async def ensure_color_role(
    guild: discord.Guild,
    *,
    name: str,
    color: discord.Color,
    secondary: discord.Color | None = None,
    tertiary: discord.Color | None = None,
    actor: object | None,
) -> tuple[int | None, bool, str]:
    """Reuse a same-named role, or create a colour role via the audited seam.

    Thin colour-specialised wrapper over :func:`ensure_role`: a gradient/
    holographic style is offered **only** when the guild supports Enhanced Role
    Styles (the perk gate lives here; the create + solid fallback live in
    ``ensure_role``). Returns ``(role_id, created, note)``.
    """
    name = (name or "").strip()[:100] or "colour"
    want_gradient = secondary is not None and supports_role_gradients(guild)
    return await ensure_role(
        guild,
        name=name,
        color=color,
        secondary=secondary if want_gradient else None,
        tertiary=tertiary if want_gradient else None,
        actor=actor,
        reason="Colour role (reaction-role menu)",
    )


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

    if added or removed:
        await _record_pickups(guild.id, added, removed)

    note = ""
    if blocked and not (added or removed):
        note = "I can't manage that role (it's above my highest role)."
    return RoleMenuOutcome(added=added, removed=removed, blocked=blocked, note=note)


async def _record_pickups(
    guild_id: int,
    added: tuple[int, ...],
    removed: tuple[int, ...],
) -> None:
    """Tally pickup analytics (PR 5, plan §10) — best-effort, aggregate only.

    Counted for every self-assignment (menu *and* emoji surfaces both funnel
    through :func:`_apply`). A stats-write blip must never block the actual role
    mutation, so failures are swallowed at debug level.
    """
    try:
        for role_id in added:
            await menus_db.record_pickup(guild_id, role_id)
        for role_id in removed:
            await menus_db.record_removal(guild_id, role_id)
    except Exception:  # noqa: BLE001 — analytics is non-critical; never block assignment
        logger.debug("reaction_role_service: pickup-stat write failed", exc_info=True)


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
    show_counts: bool = False,
) -> str:
    limit = "∞" if not max_roles else str(max_roles)
    counts = ", counts" if show_counts else ""
    return f"{title!r} [{style}/{mode}, limit={limit}, {len(options)} role(s){counts}]"


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


async def _emit_mode(
    guild_id: int,
    *,
    message_id: int,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
) -> None:
    """Emit ``audit.action_recorded`` for a per-message reaction-mode change."""
    from services.audit_events import emit_audit_action

    await emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="role",
        mutation_type="set_reaction_mode",
        target=f"reaction_message:{message_id}",
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
    actor_type: str = "admin",
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
        actor_type=actor_type,
        occurred_at=datetime.now(tz=timezone.utc),
    )


__all__ = [
    "VALID_MODES",
    "VALID_STYLES",
    "RoleMenuOutcome",
    "RoleOption",
    "apply_selection",
    "bind_emoji",
    "clear_message_mode",
    "count_dead_bindings",
    "create_menu",
    "delete_menu",
    "ensure_color_role",
    "ensure_role",
    "get_binding",
    "get_menu",
    "get_menu_options",
    "get_message_mode",
    "handle_reaction_add",
    "handle_reaction_remove",
    "list_bindings",
    "list_menus",
    "list_message_modes",
    "list_posted_menus",
    "prune_dead_bindings",
    "reaction_roles_enabled",
    "set_menu_location",
    "set_menu_message",
    "set_message_mode",
    "supports_role_gradients",
    "toggle_role",
    "unbind_emoji",
    "update_menu",
]
