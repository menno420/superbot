"""In-place navigation helper for the AI admin panel page-stack.

The AI Platform panel is **one anchor message** (the persistent
:class:`views.ai.panel.AIPanelView`). Every chooser / scope-picker is a
*page* of that same message: a button callback ``edit_message``-es the
anchor to the next page instead of spawning a new ephemeral (the
"matches the rest of the bot" doctrine — V-02 navigation, settings hub,
mining hub). Ephemerals are reserved for confirmations / errors only.

This module provides the **Back affordance** every non-home page needs:
:func:`add_back_button` appends a secondary button whose callback
rebuilds the parent ``(embed, view)`` synchronously and ``edit_message``-es
the same anchor. The builder is a plain callable so a page can point Back
at the AI home, at its chooser, or at any intermediate page without a
router or a serialized stack.

Why a local helper and not ``views.navigation.attach_back_button``: that
helper defers then ``safe_edit``-s (an ``edit_original_response`` /
``edit``) — correct for the cross-cog hub chains it serves, but the AI
pages are a single synchronous ``edit_message`` swap with no async
parent rebuild, so a direct ``interaction.response.edit_message`` keeps
the page swap inside the 3-second ack window and reads as the same idiom
the consistency linter rewards (``edit_in_place``). The two coexist.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import discord

logger = logging.getLogger("bot.views.ai.nav")

# A page builder returns the ``(embed, view)`` pair for a page. It is
# synchronous: AI pages are built from already-loaded state (an embed
# builder + a fresh view), so no await is needed to render the parent.
PageBuilder = Callable[[], "tuple[discord.Embed, discord.ui.View]"]

# Discord's per-view component cap (a view may hold at most 25 items).
_MAX_COMPONENTS = 25


class _BackButton(discord.ui.Button):
    """A Back button that rebuilds a parent page in place on the anchor."""

    def __init__(self, *, label: str, builder: PageBuilder, row: int) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self._builder = builder

    async def callback(self, interaction: discord.Interaction) -> None:
        embed, view = self._builder()
        await interaction.response.edit_message(embed=embed, view=view)


def add_back_button(
    view: discord.ui.View,
    *,
    label: str,
    builder: PageBuilder,
    row: int = 4,
) -> bool:
    """Append a Back button to ``view`` that swaps the anchor to its parent.

    Args:
        view: the page view being rendered onto the anchor.
        label: button label (e.g. ``"↩ Back"`` / ``"↩ AI home"``).
        builder: zero-arg callable returning the parent ``(embed, view)``.
            Invoked at click time so the parent is always freshly built.
        row: Discord row index (default 4 — the bottom row).

    Returns ``True`` if the button was added, ``False`` if the view is
    already at Discord's 25-component cap (a WARNING is logged so the
    lost-nav case is visible). Mirrors
    :func:`views.navigation.attach_back_button`'s cap contract.
    """
    if len(view.children) >= _MAX_COMPONENTS:
        logger.warning(
            "ai._nav.add_back_button: %s already has %d children — %r button skipped.",
            type(view).__name__,
            len(view.children),
            label,
        )
        return False
    view.add_item(_BackButton(label=label, builder=builder, row=row))
    return True


def ai_home_page() -> tuple[discord.Embed, discord.ui.View]:
    """Build the AI Platform home page ``(embed, view)`` for a Back target."""
    from views.ai.panel import AIPanelView, build_ai_panel_embed

    return build_ai_panel_embed(), AIPanelView()


__all__ = ["PageBuilder", "add_back_button", "ai_home_page"]
