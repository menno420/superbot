"""Simple prev/next embed paginator (S4.4.5 extraction).

Extracted from ``cogs/diagnostic_cog.py`` unchanged.  Future stage C2
(audit §5.2 item 4) will lift this shape into a shared
``views/paginated.py PaginatedView`` base class consumed by both
``HelpPanelView`` (cogs/help_cog.py) and this paginator.  Until then,
the diagnostic paginator stays here.
"""

from __future__ import annotations

import discord

from views.base import BaseView


class _PaginatorView(BaseView):
    """Simple prev/next paginator for multi-page embeds."""

    def __init__(
        self,
        pages: list[discord.Embed],
        author: discord.Member | discord.User,
    ):
        super().__init__(author, timeout=120)
        self.pages = pages
        self.index = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.index == 0
        self.next_btn.disabled = self.index == len(self.pages) - 1

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.index -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.index += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)
