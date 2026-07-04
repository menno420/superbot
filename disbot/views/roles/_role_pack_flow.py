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

import re
from collections.abc import Awaitable, Callable

import discord

from core.runtime.interaction_helpers import safe_defer
from core.runtime.permission_checks import member_has_perms_or_owner
from utils import role_packs
from views.base import BaseView
from views.roles._helpers import _COLOR_OPTIONS, _parse_color
from views.selectors import attach_multi_select

# Invoked after roles are created/reused, with the resulting role ids — lets the
# menu builder fold the new roles into its draft. ``None`` = create-only.
OnRolesReady = Callable[[discord.Interaction, "list[int]"], Awaitable[None]]


def _can_manage(interaction: discord.Interaction) -> bool:
    # Owner OR manage_roles (admins implicitly hold manage_roles). Q-0212.
    return member_has_perms_or_owner(interaction.user, manage_roles=True)


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

    @discord.ui.button(
        label="✏️ Custom (bulk)",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def custom_bulk_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        """Type several custom role names → optional colour → bulk-create them."""
        if not _can_manage(interaction):
            await interaction.response.send_message(
                "You need the **Manage Roles** permission to do that.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(_CustomBulkModal(self))

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
    """Create/reuse one role per picked pack name; report + run the on_created hook."""
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
    by_name = {role.name: role for role in pack.roles}
    specs: list[tuple[str, discord.Color, bool]] = []
    for name in names:
        spec = by_name.get(name)
        if spec is None:  # pragma: no cover - select only emits catalogue names
            continue
        try:
            color = _parse_color(spec.color)
        except (ValueError, OverflowError):  # pragma: no cover - constant data
            color = discord.Color.default()
        specs.append((spec.name, color, spec.hoist))
    await _create_roles(interaction, view, specs, reason="Bulk role creation (pack)")


# ---------------------------------------------------------------------------
# Custom bulk creation — type many names, optional preset colour
# ---------------------------------------------------------------------------


def _parse_role_names(raw: str, *, limit: int = 25) -> list[str]:
    """Split free-text into role names (one per line / comma-separated), deduped.

    Case-insensitive de-dup preserving first-seen order; names capped at 100
    chars (Discord's limit) and the batch capped at ``limit`` (extras dropped).
    """
    seen: set[str] = set()
    names: list[str] = []
    for part in re.split(r"[\n,]+", raw or ""):
        name = part.strip()[:100]
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
        if len(names) >= limit:
            break
    return names


class _CustomBulkModal(discord.ui.Modal, title="Bulk-create custom roles"):  # type: ignore[call-arg]
    """Collect several custom role names, then offer an optional preset colour."""

    names_in = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Role names",
        style=discord.TextStyle.paragraph,
        placeholder="One per line, or comma-separated — e.g.\nArtist\nWriter, Gamer",
        max_length=2000,
    )

    def __init__(self, flow: RolePackView) -> None:
        super().__init__()
        self.flow = flow

    async def on_submit(self, interaction: discord.Interaction) -> None:
        names = _parse_role_names(self.names_in.value)
        if not names:
            await interaction.response.send_message(
                "❌ Enter at least one role name.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            content=(
                f"Creating **{len(names)}** role(s): {', '.join(names)[:1400]}\n\n"
                "Pick **one colour for them all**, **🎨 Per-role colours** to choose "
                "each one, or **Create with no colour**:"
            ),
            view=_BulkColourView(self.flow, names),
            ephemeral=True,
        )


class _ColourPresetSelect(discord.ui.Select):
    """Single-pick preset colour applied to every custom role in the batch."""

    def __init__(self, view: _BulkColourView) -> None:
        self._view = view
        super().__init__(
            placeholder="Pick a colour for these roles (optional)…",
            row=0,
            max_values=1,
            options=[
                discord.SelectOption(label=label, value=hex_value)
                for label, hex_value in _COLOR_OPTIONS
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            color = _parse_color(self.values[0])
        except (ValueError, OverflowError):  # pragma: no cover - constant data
            color = None
        await _commit_custom_roles(interaction, self._view, color)


class _BulkColourView(BaseView):
    """Optional preset-colour picker for a batch of custom roles."""

    def __init__(self, flow: RolePackView, names: list[str]) -> None:
        super().__init__(flow._author, timeout=180)
        self.flow = flow
        self.names = names
        self.add_item(_ColourPresetSelect(self))

    @discord.ui.button(
        label="🎨 Per-role colours",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def per_role_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        """Walk each name with its own colour picker (the emote→role-walk method)."""
        if not _can_manage(interaction):
            await interaction.response.send_message(
                "You need the **Manage Roles** permission to do that.",
                ephemeral=True,
            )
            return
        walker = _PerRoleColourView(self.flow, self.names)
        await interaction.response.edit_message(content=walker.prompt(), view=walker)

    @discord.ui.button(
        label="Create with no colour",
        style=discord.ButtonStyle.grey,
        row=1,
    )
    async def no_colour_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await _commit_custom_roles(interaction, self, None)


async def _commit_custom_roles(
    interaction: discord.Interaction,
    view: _BulkColourView,
    color: discord.Color | None,
) -> None:
    """Bulk-create the typed custom names with one shared colour (or default)."""
    if not _can_manage(interaction):
        await interaction.response.send_message(
            "You need the **Manage Roles** permission to do that.",
            ephemeral=True,
        )
        return
    specs = [(name, color or discord.Color.default(), False) for name in view.names]
    await _create_roles(
        interaction,
        view.flow,
        specs,
        reason="Bulk role creation (custom)",
    )


# ---------------------------------------------------------------------------
# Per-role colour walk — one colour picker per name (the emote→role-walk method)
# ---------------------------------------------------------------------------


class _PerRoleColourSelect(discord.ui.Select):
    """One step of the walk: pick the current role's colour (or no colour)."""

    def __init__(self, walker: _PerRoleColourView) -> None:
        self._walker = walker
        super().__init__(
            placeholder=f"Colour for {walker.current_name}…"[:150],
            row=0,
            max_values=1,
            options=[
                discord.SelectOption(label="⬜ No colour (default)", value=""),
                *(
                    discord.SelectOption(label=label, value=hex_value)
                    for label, hex_value in _COLOR_OPTIONS
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._walker._on_pick(interaction, self.values[0])


class _PerRoleColourView(BaseView):
    """Walk each custom name, picking its own colour — mirrors ``_BindEmotesView``.

    The reaction-role flow walks each emote with its own role picker; this walks
    each role name with its own colour picker, then bulk-creates them all with
    their chosen colours through the shared :func:`_create_roles` seam.
    """

    def __init__(self, flow: RolePackView, names: list[str]) -> None:
        super().__init__(flow._author, timeout=300)
        self.flow = flow
        self.names = names
        self.index = 0
        self.specs: list[tuple[str, discord.Color, bool]] = []
        self._attach()

    @property
    def current_name(self) -> str:
        return self.names[self.index]

    def prompt(self) -> str:
        return (
            f"Pick a colour for **{self.current_name}** "
            f"({self.index + 1}/{len(self.names)}):"
        )

    def _attach(self) -> None:
        self.clear_items()
        self.add_item(_PerRoleColourSelect(self))

    async def _on_pick(self, interaction: discord.Interaction, hex_value: str) -> None:
        if self.index >= len(self.names):  # pragma: no cover - guards a stale click
            await safe_defer(interaction)
            return
        color = discord.Color.default()
        if hex_value:
            try:
                color = _parse_color(hex_value)
            except (ValueError, OverflowError):  # pragma: no cover - constant data
                color = discord.Color.default()
        self.specs.append((self.current_name, color, False))
        self.index += 1
        if self.index < len(self.names):
            self._attach()
            await interaction.response.edit_message(content=self.prompt(), view=self)
            return
        # All colours chosen — clear the picker, then create through the shared seam
        # (safe_defer is a no-op once the response is done, so followup still works).
        await interaction.response.edit_message(content="🎨 Creating roles…", view=None)
        self.stop()
        await _create_roles(
            interaction,
            self.flow,
            self.specs,
            reason="Bulk role creation (custom, per-role colour)",
        )


# ---------------------------------------------------------------------------
# Shared creator
# ---------------------------------------------------------------------------


async def _create_roles(
    interaction: discord.Interaction,
    flow: RolePackView,
    specs: list[tuple[str, discord.Color, bool]],
    *,
    reason: str,
) -> None:
    """Create/reuse each ``(name, colour, hoist)`` spec; report + run on_created.

    The shared tail of both bulk paths (pack picks + custom names): defer (several
    role creations are multiple API calls), create through the audited
    ``ensure_role`` seam, report created/reused/failed, then fold the new ids into
    the menu draft via the optional ``on_created`` hook.
    """
    from services import reaction_role_service

    if not specs:
        await interaction.response.send_message(
            "Nothing to create.",
            ephemeral=True,
        )
        return
    if not await safe_defer(interaction, ephemeral=True, thinking=True):
        return

    created: list[str] = []
    reused: list[str] = []
    role_ids: list[int] = []
    notes: list[str] = []
    for name, color, hoist in specs:
        role_id, was_created, note = await reaction_role_service.ensure_role(
            flow.guild,
            name=name,
            color=color,
            hoist=hoist,
            actor=interaction.user,
            reason=reason,
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
    if flow.on_created is not None and role_ids:
        await flow.on_created(interaction, role_ids)


__all__ = ["OnRolesReady", "RolePackView"]
