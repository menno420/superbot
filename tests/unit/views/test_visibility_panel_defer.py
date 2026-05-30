"""Regression: visibility sub-panel must defer before the DB round-trip.

``_VisibilitySubView.configure_btn`` resolves the selection, then loads
subsystem-visibility rows from the DB (an ``await`` that can exceed the
3 s interaction-token window across several channels).  It must
``safe_defer`` before that load, or the follow-up ``safe_edit`` races the
token.  These tests pin the defer-before-load ordering.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest


def _make_view():
    from views.channels.visibility_panel import _VisibilitySubView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    ctx.guild.text_channels = []
    return _VisibilitySubView(ctx, manager_message=None)


def _make_interaction():
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild_id = 99
    interaction.response = MagicMock()
    return interaction


async def _click(view, label: str, interaction) -> None:
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == label
    )
    btn._view = view
    await btn.callback(interaction)


@pytest.mark.asyncio
async def test_configure_defers_before_db_load():
    """Configure Selected must defer before hitting the DB."""
    from views.channels.visibility_panel import _SubsystemToggleView

    call_order: list[str] = []

    async def _defer(*_a, **_k):
        call_order.append("defer")
        return True

    async def _load(self, *_a, **_k):  # noqa: ANN001
        call_order.append("load")

    view = _make_view()
    view.selected_channel_ids = [123]
    view._option_names = {123: "#x"}
    interaction = _make_interaction()

    with (
        patch(
            "views.channels.visibility_panel.safe_defer",
            AsyncMock(side_effect=_defer),
        ),
        patch.object(_SubsystemToggleView, "load", _load),
        patch("views.channels.visibility_panel.safe_edit", AsyncMock()),
    ):
        await _click(view, "Configure Selected", interaction)

    assert call_order == ["defer", "load"]


@pytest.mark.asyncio
async def test_configure_requires_a_selection():
    """With nothing selected, Configure must prompt and not hit the DB."""
    view = _make_view()
    view.selected_channel_ids = []
    interaction = _make_interaction()
    interaction.response.send_message = AsyncMock()
    await _click(view, "Configure Selected", interaction)
    interaction.response.send_message.assert_awaited_once()
