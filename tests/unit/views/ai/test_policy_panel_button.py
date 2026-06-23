"""PR4A — main AI panel gains a Policy button that opens the chooser."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from views.ai import panel  # noqa: E402


def _admin_panel_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.guild_id = 999
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


def test_panel_advertises_policy_button():
    view = panel.AIPanelView()
    custom_ids = [
        item.custom_id
        for item in view.children
        if isinstance(item, discord.ui.Button)
    ]
    assert "ai:policy" in custom_ids


def test_policy_button_is_on_the_second_row_next_to_settings():
    """``Settings`` and ``Policy`` are both success-style entry points
    that open separate ephemeral surfaces; keep them on the same row
    so the panel layout stays predictable.
    """
    view = panel.AIPanelView()
    by_id = {
        item.custom_id: item
        for item in view.children
        if isinstance(item, discord.ui.Button)
    }
    settings_btn = by_id["ai:settings"]
    policy_btn = by_id["ai:policy"]
    assert settings_btn.row == policy_btn.row
    assert policy_btn.style == discord.ButtonStyle.success


async def test_router_handler_dispatches_policy_action_in_place():
    """When the View's callback path is bypassed (e.g. after a process
    restart, where the in-memory view is gone), the router handler
    must still serve the policy action by swapping the anchor message to
    the chooser page in place (AI nav plan PR 2) — the persistent anchor
    message survives a restart, so navigation stays in place.
    """
    interaction = _admin_panel_interaction()
    await panel.handle_ai_interaction(
        interaction,
        "policy",
        session=None,
        request_id="req-test",
    )
    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.call_args
    assert kwargs.get("embed") is not None
    assert kwargs.get("view") is not None
    from views.ai.policy.chooser import PolicyChooserView

    assert isinstance(kwargs["view"], PolicyChooserView)
    # In-place navigation: no new ephemeral message is spawned.
    interaction.response.send_message.assert_not_awaited()


async def test_router_handler_rejects_non_admin_for_policy():
    interaction = _admin_panel_interaction()
    interaction.user.guild_permissions.administrator = False
    await panel.handle_ai_interaction(
        interaction,
        "policy",
        session=None,
        request_id="req-test",
    )
    # Permission denial reply, NOT a chooser view.
    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "Administrator" in args[0]
    # No view attached when permission denied.
    assert kwargs.get("view") is None or kwargs.get("view") is False


async def test_router_short_circuits_when_view_already_responded():
    """If the View's @discord.ui.button callback already sent the
    chooser, the router must bail without sending a second response.
    """
    interaction = _admin_panel_interaction()
    interaction.response.is_done.return_value = True
    await panel.handle_ai_interaction(
        interaction,
        "policy",
        session=None,
        request_id="req-test",
    )
    interaction.response.send_message.assert_not_awaited()
    interaction.response.edit_message.assert_not_awaited()
