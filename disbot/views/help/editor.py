"""Help overlay editor — the operator UI over the audited #659 seam (PR A).

Audit Phase 5 / `docs/planning/help-overlay-editor-ui-plan-2026-06-10.md` §4.2:
hide / rename / re-describe hubs and subsystems per guild, with per-field and
full reset. **Display-only by decision Q-0055** — execution is never touched,
and the editor copy says so wherever something is hidden. Every write goes
through :mod:`services.help_overlay_mutation` (admin gate + catalogue-key
validation + cache invalidation + audit events); this module renders and
routes, it never writes.

Q-0058 everywhere: operator surfaces show the custom label *and* the default
*and* the stable key together, so a renamed entity stays unambiguous.

Authority follows the staff-hub pattern (`views/server_management/access_map`):
``public=True`` (the panel lives on the shared hub message) with an
**administrator floor re-checked live on every interaction** — opening the
panel never authorises later clicks. The mutation service re-checks again at
write time (defense in depth).

Entity choice happens in selects, text entry in modals — a Discord modal
cannot contain a select (journal rule), and a button callback that opens a
modal must not defer first.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import help_overlay_mutation
from services.help_catalogue import build_help_catalogue
from services.help_overlay import (
    MAX_DESCRIPTION_LEN,
    MAX_DISPLAY_NAME_LEN,
    get_guild_help_overlay,
)
from utils.ui_constants import ADMIN_COLOR
from views.base import BaseView, interaction_is_admin

logger = logging.getLogger("bot.views.help.editor")

_PAGE_SIZE = 25

# Q-0055 copy — shown beside every hidden entity.
_HIDDEN_NOTE = "hidden from Help but still executable"


# ---------------------------------------------------------------------------
# Catalogue/overlay composition helpers (read-only)
# ---------------------------------------------------------------------------


def _entity_defaults(kind: str, key: str) -> tuple[str, str]:
    """``(default_display_name, default_description)`` from the catalogue."""
    catalogue = build_help_catalogue()
    if kind == "hub":
        row = catalogue.hub(key)
        if row is None:
            return key, ""
        return row.entry.display_name, row.entry.purpose
    sub = catalogue.subsystem(key)
    if sub is None:
        return key, ""
    return sub.display_name, sub.description


def _entity_keys(kind: str) -> tuple[str, ...]:
    """Stable-ordered catalogue keys for one entity kind."""
    catalogue = build_help_catalogue()
    rows = catalogue.hubs if kind == "hub" else catalogue.subsystems
    return tuple(r.key for r in rows)


async def _entity_state(
    guild_id: int,
    kind: str,
    key: str,
) -> tuple[str, str, bool, str | None, str | None]:
    """``(default_name, default_desc, hidden, custom_name, custom_desc)``."""
    default_name, default_desc = _entity_defaults(kind, key)
    overlay = await get_guild_help_overlay(guild_id)
    row = overlay.get(kind, key)
    if row is None:
        return default_name, default_desc, False, None, None
    return (
        default_name,
        default_desc,
        bool(row.display_hidden),
        row.display_name,
        row.description,
    )


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


async def build_editor_home_embed(guild_id: int) -> discord.Embed:
    """The editor overview: current override counts + how the lanes relate."""
    overlay = await get_guild_help_overlay(guild_id)
    hidden = sum(1 for r in overlay.rows if r.display_hidden)
    renamed = sum(1 for r in overlay.rows if r.display_name is not None)
    redescribed = sum(1 for r in overlay.rows if r.description is not None)
    embed = discord.Embed(
        title="✏️ Help editor",
        description=(
            "Per-guild Help **presentation** — hide, rename, or re-describe "
            "hubs and subsystems in Help surfaces only. Hiding is "
            "**display-only**: a hidden command stays executable, and "
            "execution access is never changed here (Q-0055)."
        ),
        color=ADMIN_COLOR,
    )
    embed.add_field(
        name="Current overrides",
        value=(
            f"🙈 hidden: **{hidden}** · ✏️ renamed: **{renamed}** · "
            f"📝 re-described: **{redescribed}**"
            + ("" if overlay.rows else "  *(none — Help renders the defaults)*")
        ),
        inline=False,
    )
    embed.add_field(
        name="Verify",
        value=(
            "Changes are live in Help immediately — check them with "
            "**👁 Help Preview** (it also reports orphaned overrides)."
        ),
        inline=False,
    )
    embed.set_footer(text="Administrator only · writes are audited")
    return embed


async def build_entity_embed(guild_id: int, kind: str, key: str) -> discord.Embed:
    """One entity's edit card — custom + default + stable key (Q-0058)."""
    default_name, default_desc, hidden, custom_name, custom_desc = await _entity_state(
        guild_id,
        kind,
        key,
    )
    shown_name = custom_name or default_name
    title = f"✏️ {shown_name}"
    if hidden:
        title = f"🙈 {shown_name}"
    embed = discord.Embed(title=title, color=ADMIN_COLOR)
    embed.add_field(
        name="Identity",
        value=(
            f"kind: `{kind}` · stable key: `{key}`\n"
            f"default name: **{default_name}**"
            + (f"\ncustom name: **{custom_name}**" if custom_name else "")
        ),
        inline=False,
    )
    embed.add_field(
        name="Description",
        value=(
            (f"custom: {custom_desc}\n" if custom_desc else "")
            + f"default: {default_desc or '*none*'}"
        )[:1024],
        inline=False,
    )
    embed.add_field(
        name="Visibility",
        value=(f"🙈 **Hidden** — {_HIDDEN_NOTE}." if hidden else "👁 Shown (default)."),
        inline=False,
    )
    embed.set_footer(text="Display-only · live in Help on save · audited")
    return embed


# ---------------------------------------------------------------------------
# Shared admin-gated shell
# ---------------------------------------------------------------------------


class _HelpAdminView(BaseView):
    """Authority-gated, not ownership-gated — the staff-hub subpanel pattern."""

    def __init__(self, author: discord.abc.User) -> None:
        super().__init__(author, public=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction_is_admin(interaction):
            return True
        await interaction.response.send_message(
            "❌ You need **Administrator** permission to edit Help.",
            ephemeral=True,
        )
        return False


def _mutation_error_text(exc: Exception) -> str:
    return f"❌ {exc}" if str(exc) else "❌ That edit was rejected."


# ---------------------------------------------------------------------------
# Home view
# ---------------------------------------------------------------------------


class HelpEditorHomeView(_HelpAdminView):
    """Entry panel: pick an entity kind, or reset the whole guild overlay."""

    @discord.ui.button(
        label="📂 Hubs",
        style=discord.ButtonStyle.secondary,
        custom_id="help_editor:hubs",
        row=0,
    )
    async def hubs_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await _open_picker(interaction, kind="hub", page=0)

    @discord.ui.button(
        label="🧩 Subsystems",
        style=discord.ButtonStyle.secondary,
        custom_id="help_editor:subsystems",
        row=0,
    )
    async def subsystems_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await _open_picker(interaction, kind="subsystem", page=0)

    @discord.ui.button(
        label="♻️ Reset all…",
        style=discord.ButtonStyle.danger,
        custom_id="help_editor:reset_all",
        row=1,
    )
    async def reset_all_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        embed = discord.Embed(
            title="♻️ Reset ALL Help overrides?",
            description=(
                "Every hide / rename / re-description in this guild is "
                "removed and Help returns to the defaults. This cannot be "
                "undone (the audit log keeps the history)."
            ),
            color=discord.Color.red(),
        )
        view = _ResetAllConfirmView(interaction.user)
        _carry_back_button(self, view)
        await safe_edit(interaction, embed=embed, view=view)


class _ResetAllConfirmView(_HelpAdminView):
    @discord.ui.button(
        label="⚠️ Yes, reset everything",
        style=discord.ButtonStyle.danger,
        custom_id="help_editor:reset_all_confirm",
        row=0,
    )
    async def confirm_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        if interaction.guild is None:  # guild-only panel; narrows typing
            return
        try:
            await help_overlay_mutation.reset_guild_overlay(
                interaction.guild.id,
                actor=interaction.user,
            )
        except help_overlay_mutation.HelpOverlayMutationError as exc:
            await interaction.followup.send(
                _mutation_error_text(exc),
                ephemeral=True,
            )
            return
        await _back_to_home(interaction, self)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="help_editor:reset_all_cancel",
        row=0,
    )
    async def cancel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        await _back_to_home(interaction, self)


# ---------------------------------------------------------------------------
# Entity picker (paginated)
# ---------------------------------------------------------------------------


class _EntitySelect(discord.ui.Select):
    def __init__(
        self,
        kind: str,
        keys: tuple[str, ...],
        labels: dict[str, tuple[str, str, bool]],
        page: int,
    ) -> None:
        pages = max(1, -(-len(keys) // _PAGE_SIZE))
        window = keys[page * _PAGE_SIZE : (page + 1) * _PAGE_SIZE]
        options = []
        for key in window:
            shown, default_name, hidden = labels[key]
            label = f"{'🙈 ' if hidden else ''}{shown}"[:100]
            # Q-0058: the default + stable key ride along when renamed.
            description = (f"{default_name} · {key}" if shown != default_name else key)[
                :100
            ]
            options.append(
                discord.SelectOption(label=label, value=key, description=description),
            )
        placeholder = f"Edit a {kind}…"
        if pages > 1:
            placeholder += f" (page {page + 1}/{pages})"
        super().__init__(
            placeholder=placeholder,
            options=options
            or [discord.SelectOption(label="(none registered)", value="_none")],
        )
        self._kind = kind

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.values[0] == "_none":
            await interaction.response.send_message(
                "Nothing to edit for this kind.",
                ephemeral=True,
            )
            return
        await _open_entity(interaction, kind=self._kind, key=self.values[0])


class _PickerPageButton(discord.ui.Button):
    def __init__(self, *, kind: str, delta: int, page: int, pages: int) -> None:
        prev = delta < 0
        super().__init__(
            label="◀ Prev" if prev else "More ▶",
            style=discord.ButtonStyle.secondary,
            custom_id=f"help_editor:page_{'prev' if prev else 'next'}",
            disabled=(page + delta) < 0 or (page + delta) >= pages,
            row=1,
        )
        self._kind = kind
        self._target = page + delta

    async def callback(self, interaction: discord.Interaction) -> None:
        await _open_picker(interaction, kind=self._kind, page=self._target)


class EntityPickerView(_HelpAdminView):
    """Choose which hub/subsystem to edit (25 per page, never truncated)."""

    def __init__(
        self,
        author: discord.abc.User,
        *,
        kind: str,
        keys: tuple[str, ...],
        labels: dict[str, tuple[str, str, bool]],
        page: int,
    ) -> None:
        super().__init__(author)
        self.add_item(_EntitySelect(kind, keys, labels, page))
        pages = max(1, -(-len(keys) // _PAGE_SIZE))
        if pages > 1:
            self.add_item(
                _PickerPageButton(kind=kind, delta=-1, page=page, pages=pages),
            )
            self.add_item(_PickerPageButton(kind=kind, delta=1, page=page, pages=pages))
        self.add_item(_BackToEditorHomeButton(row=2))


# ---------------------------------------------------------------------------
# Entity editor
# ---------------------------------------------------------------------------


class EntityEditorView(_HelpAdminView):
    """One entity's actions — every button is exactly one audited write."""

    def __init__(
        self,
        author: discord.abc.User,
        *,
        kind: str,
        key: str,
        hidden: bool,
    ) -> None:
        super().__init__(author)
        self.kind = kind
        self.key = key
        toggle = _HideToggleButton(hidden=hidden)
        self.add_item(toggle)
        self.add_item(_RenameButton())
        self.add_item(_RedescribeButton())
        self.add_item(_ResetFieldButton(field="display_name", label="↩ Reset name"))
        self.add_item(
            _ResetFieldButton(field="description", label="↩ Reset description"),
        )
        self.add_item(_ResetEntityButton())
        self.add_item(_BackToPickerButton(kind=kind, row=3))
        self.add_item(_BackToEditorHomeButton(row=3))


class _HideToggleButton(discord.ui.Button):
    def __init__(self, *, hidden: bool) -> None:
        super().__init__(
            label="👁 Unhide" if hidden else "🙈 Hide from Help",
            style=(
                discord.ButtonStyle.success if hidden else discord.ButtonStyle.danger
            ),
            custom_id="help_editor:hide_toggle",
            row=0,
        )
        self._currently_hidden = hidden

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EntityEditorView = self.view  # type: ignore[assignment]
        await _apply_field_edit(
            interaction,
            view,
            display_hidden=(None if self._currently_hidden else True),
        )


class _RenameButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="✏️ Rename…",
            style=discord.ButtonStyle.primary,
            custom_id="help_editor:rename",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EntityEditorView = self.view  # type: ignore[assignment]
        # No defer before a modal — send_modal must be the first response.
        await interaction.response.send_modal(
            _TextFieldModal(view, field="display_name"),
        )


class _RedescribeButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="📝 Re-describe…",
            style=discord.ButtonStyle.primary,
            custom_id="help_editor:redescribe",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EntityEditorView = self.view  # type: ignore[assignment]
        await interaction.response.send_modal(
            _TextFieldModal(view, field="description"),
        )


class _ResetFieldButton(discord.ui.Button):
    def __init__(self, *, field: str, label: str) -> None:
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"help_editor:reset_{field}",
            row=2,
        )
        self._field = field

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EntityEditorView = self.view  # type: ignore[assignment]
        await _apply_field_edit(interaction, view, **{self._field: None})


class _ResetEntityButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="♻️ Reset entity",
            style=discord.ButtonStyle.secondary,
            custom_id="help_editor:reset_entity",
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EntityEditorView = self.view  # type: ignore[assignment]
        await _apply_field_edit(
            interaction,
            view,
            display_hidden=None,
            display_name=None,
            description=None,
        )


class _TextFieldModal(discord.ui.Modal):
    """Rename / re-describe input. One bounded text field, service-validated."""

    def __init__(self, view: EntityEditorView, *, field: str) -> None:
        rename = field == "display_name"
        super().__init__(
            title="Rename in Help" if rename else "Re-describe in Help",
        )
        self._editor_view = view
        self._field = field
        self.value_input: discord.ui.TextInput = discord.ui.TextInput(
            label="Display name" if rename else "Description",
            style=(discord.TextStyle.short if rename else discord.TextStyle.paragraph),
            required=True,
            max_length=(MAX_DISPLAY_NAME_LEN if rename else MAX_DESCRIPTION_LEN),
            placeholder="Shown in Help surfaces only (stable key never changes)",
        )
        self.add_item(self.value_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await _apply_field_edit(
            interaction,
            self._editor_view,
            **{self._field: str(self.value_input.value).strip()},
        )


# ---------------------------------------------------------------------------
# Navigation + the one write path
# ---------------------------------------------------------------------------


class _BackToEditorHomeButton(discord.ui.Button):
    def __init__(self, *, row: int) -> None:
        super().__init__(
            label="✏️ Editor home",
            style=discord.ButtonStyle.secondary,
            custom_id="help_editor:home",
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        await _back_to_home(interaction, self.view)


class _BackToPickerButton(discord.ui.Button):
    def __init__(self, *, kind: str, row: int) -> None:
        super().__init__(
            label="◀ Back",
            style=discord.ButtonStyle.secondary,
            custom_id="help_editor:back_to_picker",
            row=row,
        )
        self._kind = kind

    async def callback(self, interaction: discord.Interaction) -> None:
        await _open_picker(interaction, kind=self._kind, page=0)


def _carry_back_button(old: discord.ui.View | None, new: discord.ui.View) -> None:
    """Carry the staff hub's attached Back across an in-place re-render."""
    if old is None:
        return
    for item in old.children:
        if getattr(item, "custom_id", None) == "server_management:back":
            new.add_item(item)
            return


async def _back_to_home(
    interaction: discord.Interaction,
    old_view: discord.ui.View | None,
) -> None:
    if interaction.guild is None:  # guild-only panel; narrows typing
        return
    embed = await build_editor_home_embed(interaction.guild.id)
    view = HelpEditorHomeView(interaction.user)
    _carry_back_button(old_view, view)
    if not any(
        getattr(i, "custom_id", None) == "server_management:back" for i in view.children
    ):
        # Re-attach fresh — navigation must never strand the operator
        # without the way back to the staff hub (its child panel by
        # design, Q-0032). Lazy import: no module-level views→views cycle.
        from views.server_management.hub import _attach_back_to_hub

        _attach_back_to_hub(view)
    await safe_edit(interaction, embed=embed, view=view)


async def _open_picker(
    interaction: discord.Interaction,
    *,
    kind: str,
    page: int,
) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "The editor is only available inside a server.",
            ephemeral=True,
        )
        return
    if not await safe_defer(interaction):
        return
    keys = _entity_keys(kind)
    overlay = await get_guild_help_overlay(interaction.guild.id)
    labels: dict[str, tuple[str, str, bool]] = {}
    for key in keys:
        default_name, _ = _entity_defaults(kind, key)
        row = overlay.get(kind, key)
        shown = (row.display_name if row and row.display_name else default_name) or key
        labels[key] = (shown, default_name, bool(row and row.display_hidden))
    embed = discord.Embed(
        title=f"✏️ Help editor — {kind}s",
        description=(
            f"Pick a {kind} to hide, rename, or re-describe. 🙈 marks "
            f"entries currently hidden ({_HIDDEN_NOTE})."
        ),
        color=ADMIN_COLOR,
    )
    view = EntityPickerView(
        interaction.user,
        kind=kind,
        keys=keys,
        labels=labels,
        page=page,
    )
    await safe_edit(interaction, embed=embed, view=view)


async def _open_entity(
    interaction: discord.Interaction,
    *,
    kind: str,
    key: str,
) -> None:
    if not await safe_defer(interaction):
        return
    if interaction.guild is None:  # guild-only panel; narrows typing
        return
    embed = await build_entity_embed(interaction.guild.id, kind, key)
    _, _, hidden, _, _ = await _entity_state(interaction.guild.id, kind, key)
    view = EntityEditorView(interaction.user, kind=kind, key=key, hidden=hidden)
    await safe_edit(interaction, embed=embed, view=view)


async def _apply_field_edit(
    interaction: discord.Interaction,
    view: EntityEditorView,
    **fields: object,
) -> None:
    """The single write path: one button/modal action = one audited call."""
    if interaction.guild is None:
        await interaction.response.send_message(
            "The editor is only available inside a server.",
            ephemeral=True,
        )
        return
    if not await safe_defer(interaction):
        return
    try:
        await help_overlay_mutation.set_overlay_fields(
            interaction.guild.id,
            view.kind,
            view.key,
            actor=interaction.user,
            **fields,  # type: ignore[arg-type]
        )
    except help_overlay_mutation.HelpOverlayMutationError as exc:
        await interaction.followup.send(_mutation_error_text(exc), ephemeral=True)
        return
    await _open_entity_refresh(interaction, view.kind, view.key)


async def _open_entity_refresh(
    interaction: discord.Interaction,
    kind: str,
    key: str,
) -> None:
    if interaction.guild is None:  # guild-only panel; narrows typing
        return
    embed = await build_entity_embed(interaction.guild.id, kind, key)
    _, _, hidden, _, _ = await _entity_state(interaction.guild.id, kind, key)
    view = EntityEditorView(interaction.user, kind=kind, key=key, hidden=hidden)
    await safe_edit(interaction, embed=embed, view=view)


__all__ = [
    "EntityEditorView",
    "EntityPickerView",
    "HelpEditorHomeView",
    "build_editor_home_embed",
    "build_entity_embed",
]
