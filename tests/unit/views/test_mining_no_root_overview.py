"""Regression test for PR #1 — Mining root has no no-op Overview.

Before PR #1, ``MiningHubView`` shipped a root-level ``↩ Overview``
button at row 2 whose callback redrew the same view with its own
``build_embed()`` — a pure no-op when the hub is already on its root
state. This violated the architecture rule that root panels must not
show no-op Overview controls.

This test pins the post-PR-#1 contract: the root MiningHubView has
no button with ``custom_id="mining:overview"``. Mining child / result
screens (e.g. ``_MineResultsView`` in ``views.mining.mine_view``) may
still expose their own "↩ Mining Menu" return path — those are
parent-navigation buttons, not no-op self-refreshes.
"""

from __future__ import annotations

import discord

from views.mining.main_panel import MiningHubView


def test_mining_hub_view_has_no_root_overview_button():
    view = MiningHubView()
    ids = [getattr(c, "custom_id", None) for c in view.children]
    assert "mining:overview" not in ids, (
        f"MiningHubView must not ship a no-op root Overview button. Got: {ids}"
    )


def test_mining_hub_view_action_buttons_still_present():
    """The Mine / Harvest / Explore / Inventory / Stats / Build action
    buttons remain — only the no-op Overview is removed.
    """
    view = MiningHubView()
    ids = [getattr(c, "custom_id", None) for c in view.children]
    expected = {
        "mining:mine",
        "mining:harvest",
        "mining:explore",
        "mining:inventory",
        "mining:stats",
        "mining:build",
    }
    for expected_id in expected:
        assert expected_id in ids, f"Missing action button {expected_id!r}; got {ids}"


def test_mining_hub_view_button_count_after_overview_removal():
    """Sixteen action buttons, no Overview: the six core actions (Mine /
    Harvest / Explore / Inventory / Stats / Build), Workshop, the two
    depth-navigation buttons (Descend / Ascend), Market, Vault, Gear, Skills,
    Forge, Recipes, and Character. The count is pinned so an accidental no-op
    control can't creep back in.
    """
    view = MiningHubView()
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 16
