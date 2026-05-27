"""Shared helpers for game-panel sub-views (PR 7).

Evidence-driven extraction (plan §2.9.1) — only patterns that
genuinely repeat across the RPS / Blackjack / Deathmatch panels live
here. Helpers with one caller stay inlined.

Initial scope:

* :class:`BackToPanelButton` — a "↩ Back to <Game>" button that any
  sub-view can include to return to its parent game panel. Each game
  panel ships its own ``Game → sub-view`` chain; without this helper
  every panel re-implements the same edit_message + author capture
  callback.

Future migrations land here when the second/third caller appears:

* ``BetPresetView`` (RPS + Blackjack both have the 10/25/50/100 +
  Custom shape) — migrates after PR 5 (Blackjack panel) merges.
* ``OpponentSelectView`` (RPS + Blackjack + Deathmatch all have a
  UserSelect for PvP) — migrates after PRs 5 + 6 merge.
"""

from __future__ import annotations

from collections.abc import Callable

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from views.navigation import BackTarget, attach_back_target

ParentBuilder = Callable[
    [discord.Member | discord.User],
    discord.ui.View,
]
OverviewEmbedBuilder = Callable[[], discord.Embed]


class BackToPanelButton(discord.ui.Button):
    """A "◀ Back to <Game>" button for game-panel sub-views.

    On click, edits the message back to ``overview_builder()`` + a
    fresh ``panel_builder(author)`` instance. Author is read off the
    parent view (``self.view._author``) when available, falling back
    to ``interaction.user`` if the parent view is unavailable.

    This is the only inter-game-panel pattern that genuinely repeats
    today (three call-sites per game's set of sub-views). Other
    shared shapes (bet preset, opponent select) stay inlined until
    a second caller materializes.
    """

    def __init__(
        self,
        *,
        label: str,
        custom_id: str,
        panel_builder: ParentBuilder,
        overview_builder: OverviewEmbedBuilder,
        row: int = 4,
        grandparent: BackTarget | None = None,
    ) -> None:
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=custom_id,
            row=row,
        )
        self._panel_builder = panel_builder
        self._overview_builder = overview_builder
        self._grandparent = grandparent

    async def callback(self, interaction: discord.Interaction) -> None:
        # Canonical "component defer then edit clicked message" pattern:
        # safe_defer is idempotent and bails cleanly on token expiry, and
        # safe_edit routes through followup.edit_message(message_id=
        # interaction.message.id) once deferred. Without this, a raw
        # response.edit_message after token expiry surfaces "interaction
        # failed" to the user.
        if not await safe_defer(interaction):
            return
        parent_view = self.view
        author = getattr(parent_view, "_author", interaction.user)
        new_view = self._panel_builder(author)
        if self._grandparent is not None:
            attach_back_target(new_view, self._grandparent)
        await safe_edit(
            interaction,
            embed=self._overview_builder(),
            view=new_view,
        )


__all__ = [
    "BackToPanelButton",
    "OverviewEmbedBuilder",
    "ParentBuilder",
]
