"""Help overlay editor — the operator UI for guild Help appearance (PR A).

Audit Phase 5 over the shipped HLP-3 seams: edit what ``#659`` made
storable — per-guild **hide / rename / re-describe** of hubs and
subsystems — with per-field and full reset. The flow is
``HelpEditorHomeView`` (counts + reset-all) → ``EntityPickerView``
(paginated catalogue picker) → ``HelpEntityEditorView`` (one entity).

Contract (plan §4, decisions Q-0055/Q-0056/Q-0058 + Q-0032):

* **Writes only through** :mod:`services.help_overlay_mutation` — one
  service call per editor action; the views never touch
  ``utils.db.help_overlay`` and never import an admission path (the
  Q-0055 fence stays untouched: hiding is display-only, and the editor
  copy says so).
* **Authority re-checked at every callback** (opening a panel never
  authorizes later clicks); the mutation seam re-checks again — the view
  check exists for friendly copy, not as the gate.
* **Q-0058 rendering:** every entity shows custom + default + stable key.
* **Entity choice happens in views** — modals carry only text inputs
  (a Discord modal cannot contain a select).
* Entry points (Q-0032 — no new command names): the Server-Management
  staff hub's ``✏️ Help editor`` button and the Settings hub's
  "Help appearance" domain group. Both open this view **ephemerally**.
"""

from __future__ import annotations

import logging

import discord

from services.help_catalogue import build_help_catalogue
from services.help_overlay import get_guild_help_overlay
from services.help_overlay_mutation import (
    HelpOverlayMutationError,
    UnauthorizedHelpOverlayMutationError,
    reset_guild_overlay,
    set_overlay_fields,
)
from utils.ui_constants import ADMIN_COLOR
from views.base import BaseView, interaction_is_admin

logger = logging.getLogger("bot.views.help.editor")

# Discord's select-option cap; entity lists paginate past it.
_PAGE_SIZE = 25

_FOOTER = "Changes are live in Help immediately — verify with 👁 Help Preview"

# Q-0055 copy — hiding never carries execution meaning.
_HIDDEN_NOTE = "hidden from Help but still executable"


# ---------------------------------------------------------------------------
# Read-model helpers (pure renders over catalogue + overlay)
# ---------------------------------------------------------------------------


def _catalogue_entities(kind: str) -> list[tuple[str, str, str]]:
    """``(key, default_name, default_description)`` rows for one kind,
    in the catalogue's render order.
    """
    catalogue = build_help_catalogue()
    if kind == "hub":
        return [
            (row.key, row.entry.display_name, row.entry.purpose)
            for row in catalogue.hubs
        ]
    return [
        (row.key, row.display_name, row.description) for row in catalogue.subsystems
    ]


async def build_editor_home_embed(guild_id: int) -> discord.Embed:
    """The editor landing embed: current override counts + orphan report."""
    overlay = await get_guild_help_overlay(guild_id)
    catalogue = build_help_catalogue()
    hidden = sum(1 for r in overlay.rows if r.display_hidden)
    renamed = sum(1 for r in overlay.rows if r.display_name is not None)
    redescribed = sum(1 for r in overlay.rows if r.description is not None)
    orphans = [
        r
        for r in overlay.rows
        if (
            catalogue.hub(r.entity_key)
            if r.entity_kind == "hub"
            else catalogue.subsystem(r.entity_key)
        )
        is None
    ]
    embed = discord.Embed(
        title="✏️ Help appearance editor",
        description=(
            "Customize what **Help** shows in this server: hide entries "
            f"({_HIDDEN_NOTE}), rename them, or re-describe them. "
            "Changes apply to Help only — never to permissions or execution."
        ),
        color=ADMIN_COLOR,
    )
    embed.add_field(
        name="Current overrides",
        value=(
            f"🙈 hidden: **{hidden}** · ✏️ renamed: **{renamed}** · "
            f"📝 re-described: **{redescribed}**"
            if overlay.rows
            else "*(none — Help renders its defaults)*"
        ),
        inline=False,
    )
    if orphans:
        keys = ", ".join(f"`{r.entity_key}`" for r in orphans)
        embed.add_field(
            name=f"⚠️ Orphaned overrides ({len(orphans)})",
            value=(
                f"{keys} — these reference retired Help entries and are "
                "never rendered. **Reset all** clears them."
            ),
            inline=False,
        )
    embed.set_footer(text=_FOOTER)
    return embed


async def build_entity_editor_embed(
    guild_id: int,
    kind: str,
    key: str,
) -> discord.Embed:
    """One entity's edit card — custom + default + stable key (Q-0058)."""
    overlay = await get_guild_help_overlay(guild_id)
    row = overlay.get(kind, key)
    entities = dict((k, (name, desc)) for k, name, desc in _catalogue_entities(kind))
    default_name, default_desc = entities.get(key, (key, ""))

    custom_name = row.display_name if row else None
    custom_desc = row.description if row else None
    hidden = bool(row.display_hidden) if row else False

    embed = discord.Embed(
        title=f"✏️ {custom_name or default_name}",
        description=(
            f"Editing the **{kind}** `{key}` — every field shows the "
            "custom value and the default it overrides."
        ),
        color=ADMIN_COLOR,
    )
    embed.add_field(
        name="Name",
        value=(
            f"custom: **{custom_name}**\ndefault: {default_name}"
            if custom_name
            else f"default: **{default_name}** *(no override)*"
        ),
        inline=False,
    )
    embed.add_field(
        name="Description",
        value=(
            f"custom: **{custom_desc}**\ndefault: {default_desc or '*(none)*'}"
            if custom_desc
            else f"default: **{default_desc or '*(none)*'}** *(no override)*"
        ),
        inline=False,
    )
    embed.add_field(
        name="Visibility",
        value=(f"🙈 **Hidden** — {_HIDDEN_NOTE}" if hidden else "👁 Shown (default)"),
        inline=False,
    )
    embed.set_footer(text=f"{_FOOTER} · stable key: {key}")
    return embed


# ---------------------------------------------------------------------------
# Shared authority shell
# ---------------------------------------------------------------------------


class _EditorViewBase(BaseView):
    """Owner-locked ephemeral view + live admin re-check on every click."""

    def __init__(self, author: discord.abc.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await super().interaction_check(interaction):
            return False
        if interaction_is_admin(interaction):
            return True
        await interaction.response.send_message(
            "❌ You need **Administrator** permission to edit Help appearance.",
            ephemeral=True,
        )
        return False


async def _apply_edit(
    interaction: discord.Interaction,
    view: HelpEntityEditorView,
    **fields,
) -> None:
    """One editor action → one audited service call → re-render in place.

    Mutation-contract errors surface as ephemeral copy and leave the
    editor untouched; the re-read after a successful write is truthful
    because the seam invalidates the overlay cache.
    """
    try:
        await set_overlay_fields(
            view.guild_id,
            view.kind,
            view.key,
            actor=interaction.user,
            **fields,
        )
    except UnauthorizedHelpOverlayMutationError:
        await interaction.response.send_message(
            "❌ You need **Administrator** permission to edit Help appearance.",
            ephemeral=True,
        )
        return
    except HelpOverlayMutationError as exc:
        await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
        return
    embed = await build_entity_editor_embed(view.guild_id, view.kind, view.key)
    refreshed = HelpEntityEditorView(
        interaction.user,
        view.guild_id,
        view.kind,
        view.key,
        hidden=_embed_says_hidden(embed),
    )
    await interaction.response.edit_message(embed=embed, view=refreshed)


def _embed_says_hidden(embed: discord.Embed) -> bool:
    visibility = next((f.value for f in embed.fields if f.name == "Visibility"), "")
    return "Hidden" in visibility


# ---------------------------------------------------------------------------
# Modals (text inputs only — entity choice already happened in the view)
# ---------------------------------------------------------------------------


class _RenameModal(discord.ui.Modal, title="Rename in Help"):  # type: ignore[call-arg]
    name_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Custom display name (Help only)",
        max_length=100,  # MAX_DISPLAY_NAME_LEN — the seam re-validates
    )

    def __init__(self, view: HelpEntityEditorView):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await _apply_edit(interaction, self.view, display_name=self.name_input.value)


class _RedescribeModal(discord.ui.Modal, title="Re-describe in Help"):  # type: ignore[call-arg]
    description_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Custom description (Help only)",
        max_length=100,  # MAX_DESCRIPTION_LEN — the seam re-validates
    )

    def __init__(self, view: HelpEntityEditorView):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await _apply_edit(
            interaction,
            self.view,
            description=self.description_input.value,
        )


# ---------------------------------------------------------------------------
# Entity editor (one hub/subsystem)
# ---------------------------------------------------------------------------


class HelpEntityEditorView(_EditorViewBase):
    """Edit one entity's overlay fields — every button is one seam call."""

    def __init__(
        self,
        author: discord.abc.User,
        guild_id: int,
        kind: str,
        key: str,
        *,
        hidden: bool = False,
    ) -> None:
        super().__init__(author, guild_id)
        self.kind = kind
        self.key = key
        self._relabel_hide_button(hidden)

    def _relabel_hide_button(self, hidden: bool) -> None:
        self.hide_btn.label = "👁 Unhide" if hidden else "🙈 Hide"
        self.hide_btn.style = (
            discord.ButtonStyle.success if hidden else discord.ButtonStyle.secondary
        )
        self._hidden = hidden

    @discord.ui.button(label="🙈 Hide", style=discord.ButtonStyle.secondary, row=0)
    async def hide_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Unhide resets the field to inherit (None) — the store keeps only
        # deviations, so an all-default row disappears entirely.
        await _apply_edit(
            interaction,
            self,
            display_hidden=None if self._hidden else True,
        )

    @discord.ui.button(label="✏️ Rename…", style=discord.ButtonStyle.primary, row=0)
    async def rename_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_RenameModal(self))

    @discord.ui.button(
        label="📝 Re-describe…",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def redescribe_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(_RedescribeModal(self))

    @discord.ui.button(
        label="♻️ Reset name",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def reset_name_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await _apply_edit(interaction, self, display_name=None)

    @discord.ui.button(
        label="♻️ Reset description",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def reset_desc_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await _apply_edit(interaction, self, description=None)

    @discord.ui.button(label="🗑 Reset entity", style=discord.ButtonStyle.danger, row=1)
    async def reset_entity_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await _apply_edit(
            interaction,
            self,
            display_hidden=None,
            display_name=None,
            description=None,
        )

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.secondary, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        picker = EntityPickerView(interaction.user, self.guild_id, self.kind)
        await interaction.response.edit_message(
            embed=await picker.build_embed(),
            view=picker,
        )


# ---------------------------------------------------------------------------
# Entity picker (paginated catalogue select)
# ---------------------------------------------------------------------------


class _EntitySelect(discord.ui.Select):
    """One page of catalogue entities; label = effective display (Q-0058)."""

    def __init__(
        self,
        kind: str,
        page_rows: list[tuple[str, str, bool, str]],
        *,
        page: int,
        pages: int,
    ) -> None:
        options = [
            discord.SelectOption(
                label=(f"🙈 {label}" if hidden else label)[:100],
                value=key,
                description=f"default: {default} · {key}"[:100],
            )
            for key, label, hidden, default in page_rows
        ]
        placeholder = f"Pick a {kind} to edit…"
        if pages > 1:
            placeholder += f" (page {page + 1}/{pages})"
        super().__init__(
            placeholder=placeholder,
            options=options
            or [discord.SelectOption(label="(nothing to edit)", value="-")],
        )
        self.kind = kind

    async def callback(self, interaction: discord.Interaction) -> None:
        from core.runtime.interaction_helpers import safe_defer

        view: EntityPickerView = self.view  # type: ignore[assignment]
        key = self.values[0]
        if key == "-":
            await safe_defer(interaction)
            return
        embed = await build_entity_editor_embed(view.guild_id, self.kind, key)
        editor = HelpEntityEditorView(
            interaction.user,
            view.guild_id,
            self.kind,
            key,
            hidden=_embed_says_hidden(embed),
        )
        await interaction.response.edit_message(embed=embed, view=editor)


class EntityPickerView(_EditorViewBase):
    """Paginated picker over the Help catalogue (hubs or subsystems)."""

    def __init__(
        self,
        author: discord.abc.User,
        guild_id: int,
        kind: str,
        *,
        page: int = 0,
    ) -> None:
        super().__init__(author, guild_id)
        self.kind = kind
        self.page = page

    async def build_embed(self) -> discord.Embed:
        """(Re)compose the page: select + nav, embed describing the kind."""
        overlay = await get_guild_help_overlay(self.guild_id)
        rows: list[tuple[str, str, bool, str]] = []
        for key, default_name, _desc in _catalogue_entities(self.kind):
            override = overlay.get(self.kind, key)
            label = (
                override.display_name
                if override is not None and override.display_name is not None
                else default_name
            )
            hidden = bool(override.display_hidden) if override is not None else False
            rows.append((key, label, hidden, default_name))

        pages = max(1, -(-len(rows) // _PAGE_SIZE))
        self.page = max(0, min(self.page, pages - 1))
        start = self.page * _PAGE_SIZE
        page_rows = rows[start : start + _PAGE_SIZE]

        self.clear_items()
        self.add_item(_EntitySelect(self.kind, page_rows, page=self.page, pages=pages))
        if pages > 1:
            self.add_item(_PageNavButton(delta=-1, page=self.page, pages=pages))
            self.add_item(_PageNavButton(delta=+1, page=self.page, pages=pages))
        self.add_item(_BackToHomeButton())

        plural = "hubs" if self.kind == "hub" else "subsystems"
        embed = discord.Embed(
            title=f"✏️ Help editor — {plural}",
            description=(
                f"Pick a {self.kind} to hide, rename, or re-describe. "
                "🙈 marks entries currently hidden from Help."
            ),
            color=ADMIN_COLOR,
        )
        embed.set_footer(text=_FOOTER)
        return embed


class _PageNavButton(discord.ui.Button):
    def __init__(self, *, delta: int, page: int, pages: int) -> None:
        super().__init__(
            label="◀ Prev" if delta < 0 else "Next ▶",
            style=discord.ButtonStyle.secondary,
            disabled=(page + delta) < 0 or (page + delta) >= pages,
            row=1,
        )
        self._delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EntityPickerView = self.view  # type: ignore[assignment]
        view.page += self._delta
        await interaction.response.edit_message(
            embed=await view.build_embed(),
            view=view,
        )


class _BackToHomeButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="◀ Back", style=discord.ButtonStyle.secondary, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EntityPickerView = self.view  # type: ignore[assignment]
        home = HelpEditorHomeView(interaction.user, view.guild_id)
        await interaction.response.edit_message(
            embed=await build_editor_home_embed(view.guild_id),
            view=home,
        )


# ---------------------------------------------------------------------------
# Reset-all confirm step
# ---------------------------------------------------------------------------


class _ResetAllConfirmView(_EditorViewBase):
    """Two-step destructive reset: nothing is written until Confirm."""

    @discord.ui.button(
        label="🗑 Yes, reset everything",
        style=discord.ButtonStyle.danger,
    )
    async def confirm_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        try:
            await reset_guild_overlay(self.guild_id, actor=interaction.user)
        except HelpOverlayMutationError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        home = HelpEditorHomeView(interaction.user, self.guild_id)
        await interaction.response.edit_message(
            embed=await build_editor_home_embed(self.guild_id),
            view=home,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        home = HelpEditorHomeView(interaction.user, self.guild_id)
        await interaction.response.edit_message(
            embed=await build_editor_home_embed(self.guild_id),
            view=home,
        )


# ---------------------------------------------------------------------------
# Editor home
# ---------------------------------------------------------------------------


class HelpEditorHomeView(_EditorViewBase):
    """Landing view: override counts + the three editing lanes."""

    @discord.ui.button(label="🏛 Hubs", style=discord.ButtonStyle.primary, row=0)
    async def hubs_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        picker = EntityPickerView(interaction.user, self.guild_id, "hub")
        await interaction.response.edit_message(
            embed=await picker.build_embed(),
            view=picker,
        )

    @discord.ui.button(label="🧩 Subsystems", style=discord.ButtonStyle.primary, row=0)
    async def subsystems_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        picker = EntityPickerView(interaction.user, self.guild_id, "subsystem")
        await interaction.response.edit_message(
            embed=await picker.build_embed(),
            view=picker,
        )

    @discord.ui.button(
        label="🏠 Home message",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def home_message_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        from views.help.home_builder import (
            HomeMessageBuilderView,
            build_builder_embed,
        )

        builder = await HomeMessageBuilderView.from_current(
            interaction.user,
            self.guild_id,
        )
        await interaction.response.edit_message(
            embed=build_builder_embed(builder),
            view=builder,
        )

    @discord.ui.button(label="🗑 Reset all…", style=discord.ButtonStyle.danger, row=1)
    async def reset_all_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        embed = discord.Embed(
            title="Reset ALL Help customizations?",
            description=(
                "Every hide, rename, re-description, and the custom Home "
                "message in this server will be removed and Help returns to "
                "its defaults. This cannot be undone (the audit log keeps "
                "the history)."
            ),
            color=discord.Color.red(),
        )
        await interaction.response.edit_message(
            embed=embed,
            view=_ResetAllConfirmView(interaction.user, self.guild_id),
        )


__all__ = [
    "EntityPickerView",
    "HelpEditorHomeView",
    "HelpEntityEditorView",
    "build_editor_home_embed",
    "build_entity_editor_embed",
]
