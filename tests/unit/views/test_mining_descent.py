"""The mining hub exposes Descend/Ascend depth navigation (persistent buttons)."""

from __future__ import annotations

import inspect

import discord

from views.mining.main_panel import MiningHubView


def _buttons(view: discord.ui.View) -> list[discord.ui.Button]:
    return [c for c in view.children if isinstance(c, discord.ui.Button)]


def test_hub_has_descend_and_ascend_buttons_on_their_own_row():
    view = MiningHubView()
    by_id = {b.custom_id: b for b in _buttons(view)}
    assert "mining:descend" in by_id
    assert "mining:ascend" in by_id
    # Both live on their own row (row 2), below the six existing actions.
    assert by_id["mining:descend"].row == 2
    assert by_id["mining:ascend"].row == 2


def test_descent_buttons_guard_dm_invocations():
    # Like every DB-touching hub button, descend/ascend must refuse DMs before
    # reading state (mirrors test_mining_cog_dm_guard's contract).
    src = inspect.getsource(MiningHubView)
    for btn in ("descend_btn", "ascend_btn"):
        assert f"async def {btn}(" in src, f"{btn} missing from the hub"
    # Two new guards on top of the five pre-existing DB-touching buttons.
    assert src.count("interaction.guild_id is None") >= 7
