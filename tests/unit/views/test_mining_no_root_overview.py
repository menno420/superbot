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
    """The six Option A top-level actions remain (declutter PR2, 2026-06-19):
    Mine · Harvest · Explore (open-world sub-hub) · Character (sub-hub) · Gear ·
    Workshop (sub-hub). Inventory / Stats / Skills / Vault / Home moved into the
    Character sub-hub; Descend / Ascend + the old mining-explore folded into the
    Mine action.
    """
    view = MiningHubView()
    ids = [getattr(c, "custom_id", None) for c in view.children]
    expected = {
        "mining:mine",
        "mining:harvest",
        "mining:explore_hub",
        "mining:character",
        "mining:gear",
        "mining:workshop",
    }
    for expected_id in expected:
        assert expected_id in ids, f"Missing action button {expected_id!r}; got {ids}"


def test_mining_hub_view_is_exactly_the_six_option_a_actions():
    """The Option A declutter (PR2, 2026-06-19): the main hub is exactly six
    buttons. Everything else moved into the Character / Explore / Workshop
    sub-hubs or the Mine action. Pinned so the panel can't quietly re-bloat.
    """
    view = MiningHubView()
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    ids = {getattr(c, "custom_id", None) for c in buttons}
    assert ids == {
        "mining:mine",
        "mining:harvest",
        "mining:explore_hub",
        "mining:character",
        "mining:gear",
        "mining:workshop",
    }
    assert len(buttons) == 6
    # The moved/folded actions are gone from the persistent main panel.
    for gone in (
        "mining:inventory",
        "mining:stats",
        "mining:skills",
        "mining:vault",
        "mining:home",
        "mining:descend",
        "mining:ascend",
        "mining:explore",  # old depth-event explore (now in the Mine action)
    ):
        assert gone not in ids, f"{gone!r} should have moved off the main hub"
