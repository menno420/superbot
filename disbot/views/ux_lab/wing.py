"""Shared exhibit browser for UX Lab wings.

One small base view: a wing holds an ordered list of registered pattern ids
and renders one exhibit at a time — exhibit content on rows 0–3, a fixed
navigation row (Prev / counter / Next / Home) on row 4, and the pattern's
spec card appended as the last embed. Navigation edits the message in place
(the V-02 doctrine the lab itself demonstrates).

This is intentionally *not* a new view framework: it extends the canonical
:class:`views.base.HubView`, holds only in-memory state, and is private to
``views/ux_lab/``.
"""

from __future__ import annotations

import logging
from typing import Any, TypeAlias

import discord

from utils.ux_patterns import get_spec
from utils.ux_patterns.builders import spec_card
from views.base import HubView
from views.navigation import ParentBuilder, transition_to

logger = logging.getLogger("bot.views.ux_lab")

# Row indices: exhibits may use rows 0–3; row 4 belongs to wing navigation.
NAV_ROW = 4
MAX_EXHIBIT_ROW = 3

ExhibitRender: TypeAlias = tuple[
    list[discord.Embed],
    list["discord.ui.Item[discord.ui.View]"],
]


class ExhibitWingView(HubView):
    """Browse a wing's exhibits one page at a time, editing in place.

    Subclasses define :meth:`_exhibit_ids` (ordered pattern ids) and
    :meth:`_render_exhibit` (embeds + interactive items for one exhibit).
    Per-exhibit demo state lives in ``self.state`` and is cleared on
    navigation so every exhibit starts fresh.
    """

    WING_TITLE = "Wing"
    WING_EMOJI = "🧪"

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        home_builder: ParentBuilder,
    ) -> None:
        super().__init__(author)
        self._home_builder = home_builder
        self._index = 0
        # Scratch space for the *current* exhibit's demo state (toggle
        # values, wizard step, …). Cleared on Prev/Next.
        self.state: dict[str, Any] = {}

    # -- subclass contract --------------------------------------------------

    def _exhibit_ids(self) -> tuple[str, ...]:
        raise NotImplementedError

    def _render_exhibit(self, pattern_id: str) -> ExhibitRender:
        raise NotImplementedError

    # -- rendering ----------------------------------------------------------

    @property
    def current_pattern_id(self) -> str:
        ids = self._exhibit_ids()
        return ids[self._index % len(ids)]

    def build(self) -> tuple[list[discord.Embed], ExhibitWingView]:
        """Return ``(embeds, self)`` for the current exhibit, items rebuilt."""
        pattern_id = self.current_pattern_id
        embeds, items = self._render_exhibit(pattern_id)
        embeds = [*embeds, spec_card(get_spec(pattern_id))]
        self.clear_items()
        for item in items:
            self.add_item(item)
        self._add_nav_row()
        return embeds, self

    def _add_nav_row(self) -> None:
        ids = self._exhibit_ids()
        prev_btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            emoji="◀",
            style=discord.ButtonStyle.secondary,
            row=NAV_ROW,
            custom_id="uxlab:wing:prev",
        )
        counter: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label=f"{(self._index % len(ids)) + 1}/{len(ids)} · {self.WING_TITLE}",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=NAV_ROW,
            custom_id="uxlab:wing:counter",
        )
        next_btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            emoji="▶",
            style=discord.ButtonStyle.secondary,
            row=NAV_ROW,
            custom_id="uxlab:wing:next",
        )
        home_btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label="UX Lab",
            emoji="🏠",
            style=discord.ButtonStyle.secondary,
            row=NAV_ROW,
            custom_id="uxlab:wing:home",
        )

        async def _prev(interaction: discord.Interaction) -> None:
            self._index = (self._index - 1) % len(self._exhibit_ids())
            self.state.clear()
            await self.rerender(interaction)

        async def _next(interaction: discord.Interaction) -> None:
            self._index = (self._index + 1) % len(self._exhibit_ids())
            self.state.clear()
            await self.rerender(interaction)

        async def _home(interaction: discord.Interaction) -> None:
            await transition_to(interaction, builder=self._home_builder)

        prev_btn.callback = _prev  # type: ignore[method-assign]
        next_btn.callback = _next  # type: ignore[method-assign]
        home_btn.callback = _home  # type: ignore[method-assign]
        self.add_item(prev_btn)
        self.add_item(counter)
        self.add_item(next_btn)
        self.add_item(home_btn)

    async def rerender(self, interaction: discord.Interaction) -> None:
        """Re-render the current exhibit into the same message."""
        embeds, _ = self.build()
        if interaction.response.is_done():
            await interaction.edit_original_response(embeds=embeds, view=self)
        else:
            await interaction.response.edit_message(embeds=embeds, view=self)

    # -- small helpers shared by wings ---------------------------------------

    @staticmethod
    async def ack(interaction: discord.Interaction, text: str) -> None:
        """The minimum visible reaction: an ephemeral acknowledgement."""
        await interaction.response.send_message(text, ephemeral=True)

    @staticmethod
    def demo_button(
        label: str,
        *,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        emoji: str | None = None,
        row: int = 0,
        disabled: bool = False,
        custom_id: str | None = None,
    ) -> discord.ui.Button[discord.ui.View]:
        """A plain button; caller assigns ``.callback`` (closure style)."""
        return discord.ui.Button(
            label=label,
            style=style,
            emoji=emoji,
            row=row,
            disabled=disabled,
            custom_id=custom_id,
        )
