"""Shared **📦 Role Packs** flow — bulk role creation from a curated catalogue.

Mirrors the 🎨 Colours auto-create UX (``role_menu_builder._ColourRolesView``):
pick a **category** (gaming / staff / pronouns / …), then a **multiselect** of the
predefined roles in it, and the bot bulk-creates them in one step (reuse a
same-named role, else create through the audited
:func:`services.reaction_role_service.ensure_role` → ``RoleLifecycleService``).

Used by two surfaces so the behaviour is identical on both:

* the standalone role-creation panel (:class:`views.roles.creation_panel.RoleCreatePanel`)
  — bulk-create roles into the server;
* the role-menu builder (:mod:`views.roles.role_menu_builder`) — bulk-create **and**
  add the new roles to the menu draft (pass an ``on_created`` hook).

Layer: a thin UI over the service — no DB writes, no role math here. Authority
(``manage_roles``) is re-checked at commit time (``.claude/rules/discord-views.md``).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import discord

from core.runtime.interaction_helpers import safe_defer
from utils import role_packs
from views.base import BaseView
from views.roles._helpers import _parse_color
from views.selectors import attach_multi_select

# Invoked after roles are created/reused, with the resulting role ids — lets the
# menu builder fold the new roles into its draft. ``None`` = create-only.
OnRolesReady = Callable[[discord.Interaction, "list[int]"], Awaitable[None]]


def _can_manage(interaction: discord.Interaction) -> bool:
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms is not None and (perms.manage_roles or perms.administrator))


class _PackCategorySelect(discord.ui.Select):
    """Pick which role pack (category) to create roles from."""

    def __init__(self, flow: RolePackView) -> None:
        self._flow = flow
        super().__init__(
            placeholder="Pick a role pack…",
            row=0,
            options=[
                discord.SelectOption(
                    label=pack.label[:100],
                    value=pack.key,
                    description=(pack.description[:100] or None),
                )
                for pack in role_packs.packs()
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._flow._on_pack(interaction, self.values[0])


class RolePackView(BaseView):
    """Two-step bulk-create flow: pick a pack → multiselect its roles → create."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild: discord.Guild,
        *,
        on_created: OnRolesReady | None = None,
    ) -> None:
        super().__init__(author, timeout=180)
        self.guild = guild
        self.on_created = on_created
        self._pack: role_packs.RolePack | None = None
        self.add_item(_PackCategorySelect(self))

    async def _on_pack(self, interaction: discord.Interaction, key: str) -> None:
        pack = role_packs.get_pack(key)
        if pack is None:  # pragma: no cover - select can only emit known keys
            await safe_defer(interaction)
            return
        self._pack = pack
        self.clear_items()
        options = [
            discord.SelectOption(
                label=role.name[:100],
                value=role.name,
                description=(role.description[:100] or None),
                emoji=role.emoji,
            )
            for role in pack.roles
        ]
        attach_multi_select(
            self,
            options,
            self._on_roles,
            placeholder=f"Roles to create from {pack.label}…"[:150],
            max_values=len(options),
            select_row=0,
        )
        await interaction.response.edit_message(
            content=(
                f"Pick the roles to create from **{pack.label}** "
                "(existing same-named roles are reused, not duplicated):"
            ),
            view=self,
        )

    async def _on_roles(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        await _commit_pack_roles(interaction, self, values)


async def _commit_pack_roles(
    interaction: discord.Interaction,
    view: RolePackView,
    names: list[str],
) -> None:
    """Create/reuse one role per picked name; report, then run the on_created hook."""
    from services import reaction_role_service

    if not _can_manage(interaction):
        await interaction.response.send_message(
            "You need the **Manage Roles** permission to do that.",
            ephemeral=True,
        )
        return
    pack = view._pack
    if pack is None or not names:
        await interaction.response.send_message(
            "Pick at least one role.",
            ephemeral=True,
        )
        return
    # Creating several roles is multiple API calls — defer first, report after.
    if not await safe_defer(interaction, ephemeral=True, thinking=True):
        return

    by_name = {role.name: role for role in pack.roles}
    created: list[str] = []
    reused: list[str] = []
    role_ids: list[int] = []
    notes: list[str] = []
    for name in names:
        spec = by_name.get(name)
        if spec is None:  # pragma: no cover - select only emits catalogue names
            continue
        try:
            color = _parse_color(spec.color)
        except (ValueError, OverflowError):  # pragma: no cover - constant data
            color = discord.Color.default()
        role_id, was_created, note = await reaction_role_service.ensure_role(
            view.guild,
            name=spec.name,
            color=color,
            hoist=spec.hoist,
            actor=interaction.user,
            reason="Bulk role creation (role pack)",
        )
        if role_id is None:
            notes.append(f"{name}: {note or 'could not be created'}")
            continue
        role_ids.append(role_id)
        (created if was_created else reused).append(name)
        if note:
            notes.append(f"{name}: {note}")

    parts: list[str] = []
    if created:
        parts.append(f"📦 Created {', '.join(created)}")
    if reused:
        parts.append(f"♻️ Reused existing {', '.join(reused)}")
    if notes:
        parts.append("\n".join(notes))
    await interaction.followup.send(
        "\n".join(parts) or "No roles were created.",
        ephemeral=True,
    )
    if view.on_created is not None and role_ids:
        await view.on_created(interaction, role_ids)


__all__ = ["OnRolesReady", "RolePackView"]
