"""Descend / Ascend depth navigation folded into the Mine action (declutter PR2).

Option A declutter (owner-directed, 2026-06-15;
``docs/planning/mining-hub-redesign-2026-06-15.md``): Descend / Ascend moved off
the main hub into the Mine action (``MineView``), alongside the folded
depth-event Explore, as an interim until PR3's grid Mine. These tests pin:

- the main hub no longer carries ``mining:descend`` / ``mining:ascend``;
- ``MineView`` carries Descend / Ascend / Explore movement buttons (row 1);
- the Descend / Ascend callbacks route through ``mining_workflow`` and swap to
  the navigable results view.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.mining.main_panel import MiningHubView
from views.mining.mine_view import MineView, _MineResultsView


def _buttons(view: discord.ui.View) -> list[discord.ui.Button]:
    return [c for c in view.children if isinstance(c, discord.ui.Button)]


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


def test_main_hub_no_longer_carries_descend_ascend():
    view = MiningHubView()
    ids = {b.custom_id for b in _buttons(view)}
    assert "mining:descend" not in ids
    assert "mining:ascend" not in ids


def test_mine_view_carries_movement_and_explore_on_row_one():
    view = MineView(MagicMock(id=1), guild_id=2)
    labels = [b.label or "" for b in _buttons(view)]
    descend = _find_button(view, "Descend")
    ascend = _find_button(view, "Ascend")
    explore = _find_button(view, "Explore")
    assert descend.row == 1
    assert ascend.row == 1
    assert explore.row == 1
    # The three Mine-direction buttons stay on row 0.
    assert any("Mine Left" in lbl for lbl in labels)


@pytest.mark.asyncio
async def test_descend_button_routes_through_workflow_and_swaps_to_results():
    view = MineView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Descend")
    interaction = MagicMock()
    interaction.user.mention = "@user"
    interaction.message.id = 99
    interaction.followup.edit_message = AsyncMock()

    from services.mining_workflow import DescentResult

    with patch(
        "views.mining.mine_view.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "views.mining.mine_view.mining_workflow.descend",
        new_callable=AsyncMock,
        return_value=DescentResult(moved=True, depth=1),
    ):
        await btn.callback(interaction)

    interaction.followup.edit_message.assert_awaited_once()
    swapped = interaction.followup.edit_message.await_args.kwargs["view"]
    assert isinstance(swapped, _MineResultsView)


@pytest.mark.asyncio
async def test_explore_button_routes_through_workflow_and_swaps_to_results():
    view = MineView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Explore")
    interaction = MagicMock()
    interaction.user.mention = "@user"
    interaction.message.id = 99
    interaction.followup.edit_message = AsyncMock()

    from services.mining_workflow import ExploreActionResult
    from utils.mining.workshop import WearReport

    with patch(
        "views.mining.mine_view.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "views.mining.mine_view.mining_workflow.explore",
        new_callable=AsyncMock,
        return_value=ExploreActionResult(
            text="found a gem",
            item="diamond",
            amount=1,
            depth=0,
            wear=WearReport(),
        ),
    ):
        await btn.callback(interaction)

    interaction.followup.edit_message.assert_awaited_once()
    kwargs = interaction.followup.edit_message.await_args.kwargs
    assert isinstance(kwargs["view"], _MineResultsView)
    assert "found a gem" in (kwargs["embed"].description or "")
