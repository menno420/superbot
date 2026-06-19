"""Prev/next embed paginator (S4.4.5 extraction + stabilization).

The diagnostic command-list view uses this when reached either via the
``!list_commands_detailed`` text command (no parent view) or via the
"📋 Commands" button on the diagnostics hub (with a parent view to
return to).

When ``parent_view`` is supplied, an extra "↩ Back" button is added
on a separate row.  Clicking it edits the panel in place back to the
parent — matching the canonical sub-panel return pattern used by the
rest of the codebase.
"""

from __future__ import annotations

import discord

from views.base import BaseView


class _PaginatorView(BaseView):
    """Simple prev/next paginator for multi-page embeds.

    Optional ``parent_view`` enables a "↩ Back" button that returns
    the user to the parent panel (in-place edit, no new message).
    """

    def __init__(
        self,
        pages: list[discord.Embed],
        author: discord.Member | discord.User,
        *,
        parent_view: discord.ui.View | None = None,
    ):
        super().__init__(author, timeout=120)
        self.pages = pages
        self.index = 0
        self._parent_view = parent_view
        self._update_buttons()
        if parent_view is not None:
            self._add_back_button()

    def _update_buttons(self):
        self.prev_btn.disabled = self.index == 0
        self.next_btn.disabled = self.index == len(self.pages) - 1

    def _add_back_button(self) -> None:
        """Append a "↩ Back" button that restores the parent view in place."""
        back_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="↩ Back",
            style=discord.ButtonStyle.secondary,
            row=1,
        )

        async def _back_callback(interaction: discord.Interaction) -> None:
            parent = self._parent_view
            if parent is None:
                # Defensive — _add_back_button is only called when parent_view is set.
                return
            # Restore parent embed.  Import locally to avoid a cycle
            # (paginator is imported by hub_panel which is imported by views.diagnostic).
            from services.diagnostic_helpers import build_hub_overview_embed

            await interaction.response.edit_message(
                embed=build_hub_overview_embed(),
                view=parent,
            )

        back_btn.callback = _back_callback  # type: ignore[method-assign]
        self.add_item(back_btn)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, row=0)
    async def prev_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.index -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, row=0)
    async def next_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.index += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)
