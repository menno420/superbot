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
    """The Mine / Harvest / Explore / Inventory / Stats action buttons remain —
    the no-op Overview is removed, and (Option A declutter, 2026-06-15) Build /
    Recipes / Forge / Market moved into the Workshop sub-hub.
    """
    view = MiningHubView()
    ids = [getattr(c, "custom_id", None) for c in view.children]
    expected = {
        "mining:mine",
        "mining:harvest",
        "mining:explore",
        "mining:inventory",
        "mining:stats",
        "mining:workshop",
    }
    for expected_id in expected:
        assert expected_id in ids, f"Missing action button {expected_id!r}; got {ids}"


def test_mining_hub_view_button_count_after_declutter():
    """Twelve buttons after the Option A declutter (2026-06-15): the Workshop
    sub-hub absorbed Build/Craft/Recipes (consolidated) + Forge + Market, so the
    four scattered Build/Recipes/Forge/Market buttons left the main hub. Pinned
    so the panel can't quietly re-bloat. (Character/Skills/Vault move next.)
    """
    view = MiningHubView()
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 12
