"""Q-0059 Home-message embed builder (audit Phase 5, PR B).

Stage → **preview (mandatory)** → save: operators customize the Help Home
frame (title / body / color) with the exact embed shown before any write.
Staged-not-saved state lives on the view; **Save stays disabled until the
current draft has been previewed**, and any edit re-disables it. Saving is
one audited :func:`services.help_overlay_mutation.set_home_message` call;
"Reset to default" writes all-``None`` (row deleted — the default Home is
byte-identical by construction). Color is a select of named colors — no
free-form hex parsing in v1 (plan §4.3).

The preview composes through the same :func:`home_embed_frame` the live
Home render uses (preview-is-exact rule; mention suppression included).
"""

from __future__ import annotations

import logging

import discord

from services.help_overlay import (
    HomeMessage,
    get_guild_help_overlay,
    home_embed_frame,
)
from services.help_overlay_mutation import (
    HelpOverlayMutationError,
    set_home_message,
)
from utils.ui_constants import UTILITY_COLOR
from views.help.editor import _EditorViewBase

logger = logging.getLogger("bot.views.help.home_builder")

# Named colors only (v1) — value None = "default" (the Help utility color).
_NAMED_COLORS: tuple[tuple[str, int | None], ...] = (
    ("Default (blue)", None),
    ("Blurple", 0x5865F2),
    ("Green", 0x57F287),
    ("Yellow", 0xFEE75C),
    ("Orange", 0xE67E22),
    ("Red", 0xED4245),
    ("Fuchsia", 0xEB459E),
    ("White", 0xFFFFFE),
    ("Dark grey", 0x2C2F33),
)

_PREVIEW_REQUIRED_NOTE = "Preview the draft to enable Save."


def _staged_frame(view: HomeMessageBuilderView) -> tuple[str, str, int]:
    """The exact frame the staged draft renders (shared composer)."""
    staged = HomeMessage(
        title=view.staged_title,
        body=view.staged_body,
        color=view.staged_color,
    )
    return home_embed_frame(
        None if staged.is_noop else staged,
        default_color=UTILITY_COLOR.value,
    )


def build_builder_embed(view: HomeMessageBuilderView) -> discord.Embed:
    """The builder's own control embed (draft state + instructions)."""
    embed = discord.Embed(
        title="🏠 Home message builder",
        description=(
            "Customize the Help Home frame (title, body text, color). "
            "**Preview is mandatory** — Save unlocks after you've seen the "
            "exact embed. Reset returns the byte-identical default."
        ),
        color=UTILITY_COLOR,
    )
    embed.add_field(
        name="Draft title",
        value=(view.staged_title or "*(default)*")[:1024],
        inline=False,
    )
    embed.add_field(
        name="Draft body",
        value=(view.staged_body or "*(default)*")[:1024],
        inline=False,
    )
    color_label = next(
        (label for label, value in _NAMED_COLORS if value == view.staged_color),
        f"#{view.staged_color:06x}" if view.staged_color is not None else "Default",
    )
    embed.add_field(name="Draft color", value=color_label, inline=False)
    embed.set_footer(
        text=(
            "Previewed — Save is unlocked."
            if view.previewed
            else _PREVIEW_REQUIRED_NOTE
        ),
    )
    return embed


class _TitleModal(discord.ui.Modal, title="Home title"):  # type: ignore[call-arg]
    title_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Custom Home title (blank = default)",
        max_length=256,  # MAX_HOME_TITLE_LEN — the seam re-validates
        required=False,
    )

    def __init__(self, view: HomeMessageBuilderView):
        super().__init__()
        self.builder = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = self.title_input.value.strip()
        self.builder.stage(title=raw or None)
        await self.builder.rerender(interaction)


class _BodyModal(discord.ui.Modal, title="Home body"):  # type: ignore[call-arg]
    body_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Custom Home body (blank = default)",
        style=discord.TextStyle.paragraph,
        max_length=2000,  # MAX_HOME_BODY_LEN — the seam re-validates
        required=False,
    )

    def __init__(self, view: HomeMessageBuilderView):
        super().__init__()
        self.builder = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = self.body_input.value.strip()
        self.builder.stage(body=raw or None)
        await self.builder.rerender(interaction)


class _ColorSelect(discord.ui.Select):
    def __init__(self, current: int | None) -> None:
        super().__init__(
            placeholder="Pick an embed color…",
            options=[
                discord.SelectOption(
                    label=label,
                    value=str(value) if value is not None else "default",
                    default=(value == current),
                )
                for label, value in _NAMED_COLORS
            ],
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: HomeMessageBuilderView = self.view  # type: ignore[assignment]
        raw = self.values[0]
        view.stage(color=None if raw == "default" else int(raw))
        await view.rerender(interaction)


class HomeMessageBuilderView(_EditorViewBase):
    """The stage/preview/save builder — see the module docstring.

    Same authority shell as the rest of the editor stack (owner-locked
    ephemeral + admin re-check at every callback); items rebuild on every
    stage change so Save's disabled state always reflects the draft.
    """

    def __init__(self, author: discord.abc.User, guild_id: int) -> None:
        super().__init__(author, guild_id)
        self.staged_title: str | None = None
        self.staged_body: str | None = None
        self.staged_color: int | None = None
        self.previewed = False
        self._rebuild_items()

    # -- staging -----------------------------------------------------------

    @classmethod
    async def from_current(
        cls,
        author: discord.abc.User,
        guild_id: int,
    ) -> HomeMessageBuilderView:
        """Builder pre-staged with the guild's saved Home message."""
        view = cls(author, guild_id)
        overlay = await get_guild_help_overlay(guild_id)
        if overlay.home is not None:
            view.staged_title = overlay.home.title
            view.staged_body = overlay.home.body
            view.staged_color = overlay.home.color
        return view

    def stage(self, **changes) -> None:
        """Apply a draft change; any change invalidates the preview."""
        for key, value in changes.items():
            setattr(self, f"staged_{key}", value)
        self.previewed = False
        self._rebuild_items()

    # -- rendering -----------------------------------------------------------

    def _rebuild_items(self) -> None:
        self.clear_items()
        self.add_item(_EditTitleButton())
        self.add_item(_EditBodyButton())
        self.add_item(_ColorSelect(self.staged_color))
        self.add_item(_PreviewButton())
        self.add_item(_SaveButton(disabled=not self.previewed))
        self.add_item(_ResetButton())
        self.add_item(_BackButton())

    async def rerender(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            embed=build_builder_embed(self),
            view=self,
        )


class _EditTitleButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="✏️ Edit title…", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            _TitleModal(self.view),  # type: ignore[arg-type]
        )


class _EditBodyButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="📝 Edit body…", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            _BodyModal(self.view),  # type: ignore[arg-type]
        )


class _PreviewButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="👁 Preview", style=discord.ButtonStyle.secondary, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: HomeMessageBuilderView = self.view  # type: ignore[assignment]
        title, body, color = _staged_frame(view)
        preview = discord.Embed(
            title=title,
            description=body,
            color=discord.Color(color),
        )
        preview.add_field(
            name="📋 (categories)",
            value="The Help category list renders here, unchanged.",
            inline=False,
        )
        view.previewed = True
        view._rebuild_items()
        # Builder embed + the exact frame side by side, Save now unlocked.
        await interaction.response.edit_message(
            embeds=[build_builder_embed(view), preview],
            view=view,
        )


class _SaveButton(discord.ui.Button):
    def __init__(self, *, disabled: bool) -> None:
        super().__init__(
            label="💾 Save",
            style=discord.ButtonStyle.success,
            disabled=disabled,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: HomeMessageBuilderView = self.view  # type: ignore[assignment]
        if not view.previewed:  # defense in depth — the button is disabled too
            await interaction.response.send_message(
                _PREVIEW_REQUIRED_NOTE,
                ephemeral=True,
            )
            return
        try:
            await set_home_message(
                view.guild_id,
                actor=interaction.user,
                title=view.staged_title,
                body=view.staged_body,
                color=view.staged_color,
            )
        except HelpOverlayMutationError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        from views.help.editor import HelpEditorHomeView, build_editor_home_embed

        await interaction.response.edit_message(
            embed=await build_editor_home_embed(view.guild_id),
            view=HelpEditorHomeView(interaction.user, view.guild_id),
        )


class _ResetButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="♻️ Reset to default",
            style=discord.ButtonStyle.danger,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: HomeMessageBuilderView = self.view  # type: ignore[assignment]
        try:
            await set_home_message(
                view.guild_id,
                actor=interaction.user,
                title=None,
                body=None,
                color=None,
            )
        except HelpOverlayMutationError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        view.staged_title = view.staged_body = view.staged_color = None
        view.previewed = False
        view._rebuild_items()
        await interaction.response.edit_message(
            embed=build_builder_embed(view),
            view=view,
        )


class _BackButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="◀ Back", style=discord.ButtonStyle.secondary, row=3)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: HomeMessageBuilderView = self.view  # type: ignore[assignment]
        from views.help.editor import HelpEditorHomeView, build_editor_home_embed

        await interaction.response.edit_message(
            embed=await build_editor_home_embed(view.guild_id),
            view=HelpEditorHomeView(interaction.user, view.guild_id),
        )


__all__ = [
    "HomeMessageBuilderView",
    "build_builder_embed",
]
