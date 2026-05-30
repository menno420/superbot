"""Regression tests for subsystem-visibility panel interaction ACK safety.

Pre-fix two callbacks in `views/channels/visibility_panel.py` did I/O
before any ACK:

* `_ChannelSelectForVisibility.callback` — `sub.load(guild_id)` (DB
  read of `subsystem_visibility`) before `interaction.response.edit_message`.
* `_SubsystemToggleView._make_toggle_callback` — full audited
  `governance_service.set_subsystem_visibility` write before any
  response.

The fix wraps each in `safe_defer`. The toggle callback's error
branch was previously gated by `if not interaction.response.is_done()`
(which becomes always-False after defer, silently swallowing
errors); it now routes through `safe_followup(ephemeral=True)`.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 1
    interaction.guild = MagicMock()
    interaction.guild_id = 99
    interaction.client = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.message = MagicMock()
    interaction.message.id = 4242
    return interaction


# ---------------------------------------------------------------------------
# _ChannelSelectForVisibility
# ---------------------------------------------------------------------------


async def test_channel_select_unknown_channel_uses_immediate_response():
    from views.channels.visibility_panel import _ChannelSelectForVisibility

    select = MagicMock()
    select.values = ["12345"]
    select.view = MagicMock()
    interaction = _interaction()

    with (
        patch("views.channels.visibility_panel.resources") as mock_res,
        patch("views.channels.visibility_panel.safe_defer") as defer,
    ):
        mock_res.resolve_channel = MagicMock(return_value=None)
        await _ChannelSelectForVisibility.callback(select, interaction)

    interaction.response.send_message.assert_awaited_once()
    defer.assert_not_called()


async def test_channel_select_happy_path_defers_before_subview_load():
    from views.channels.visibility_panel import _ChannelSelectForVisibility

    select = MagicMock()
    select.values = ["12345"]
    select.view = MagicMock()
    select.view.ctx = MagicMock()
    select.view.manager_message = MagicMock()
    interaction = _interaction()

    order: list[str] = []

    async def _defer(_inter, **_kw):
        order.append("defer")
        return True

    async def _load(*_a, **_kw):
        order.append("load")

    async def _edit(*_a, **_kw):
        order.append("safe_edit")
        return True

    with (
        patch("views.channels.visibility_panel.resources") as mock_res,
        patch(
            "views.channels.visibility_panel.safe_defer",
            AsyncMock(side_effect=_defer),
        ),
        patch(
            "views.channels.visibility_panel.safe_edit",
            AsyncMock(side_effect=_edit),
        ),
        patch("views.channels.visibility_panel._SubsystemToggleView") as mock_sub_cls,
    ):
        mock_res.resolve_channel = MagicMock(return_value=MagicMock())
        sub_instance = MagicMock()
        sub_instance.load = AsyncMock(side_effect=_load)
        sub_instance.build_embed = MagicMock(return_value=MagicMock())
        mock_sub_cls.return_value = sub_instance
        await _ChannelSelectForVisibility.callback(select, interaction)

    assert order == ["defer", "load", "safe_edit"], order
    interaction.response.edit_message.assert_not_called()


# ---------------------------------------------------------------------------
# _SubsystemToggleView._make_toggle_callback
# ---------------------------------------------------------------------------


def _build_toggle_view():
    """Construct a `_SubsystemToggleView` with the minimum state needed."""
    from views.channels.visibility_panel import _SubsystemToggleView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    channel = MagicMock()
    channel.id = 555
    channel.name = "test-channel"
    view = _SubsystemToggleView(ctx, channel=channel, manager_message=None)
    return view


async def test_toggle_callback_happy_path_defers_before_governance_call():
    view = _build_toggle_view()
    view._visibility = {"economy": None}
    interaction = _interaction()

    order: list[str] = []

    async def _defer(_inter, **_kw):
        order.append("defer")
        return True

    async def _set(*_a, **_kw):
        order.append("governance.set")

    async def _edit(*_a, **_kw):
        order.append("safe_edit")
        return True

    with (
        patch(
            "views.channels.visibility_panel.safe_defer",
            AsyncMock(side_effect=_defer),
        ),
        patch(
            "views.channels.visibility_panel.safe_edit",
            AsyncMock(side_effect=_edit),
        ),
        patch("views.channels.visibility_panel.governance_service") as mock_gov,
        patch("views.channels.visibility_panel.GovernanceContext") as mock_gctx,
    ):
        mock_gctx.from_interaction = MagicMock(return_value=MagicMock())
        mock_gov.set_subsystem_visibility = AsyncMock(side_effect=_set)
        callback = view._make_toggle_callback("economy")
        await callback(interaction)

    assert order == ["defer", "governance.set", "safe_edit"], order
    assert view._visibility["economy"] is True
    interaction.response.edit_message.assert_not_called()


async def test_toggle_callback_error_path_uses_safe_followup():
    """After defer, error branch must use safe_followup — not the old
    response.is_done() guard, which becomes always-False post-defer."""
    view = _build_toggle_view()
    view._visibility = {"economy": None}
    interaction = _interaction()

    safe_followup_mock = AsyncMock()

    with (
        patch(
            "views.channels.visibility_panel.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch(
            "views.channels.visibility_panel.safe_followup",
            safe_followup_mock,
        ),
        patch("views.channels.visibility_panel.governance_service") as mock_gov,
        patch("views.channels.visibility_panel.GovernanceContext") as mock_gctx,
    ):
        mock_gctx.from_interaction = MagicMock(return_value=MagicMock())
        mock_gov.set_subsystem_visibility = AsyncMock(
            side_effect=RuntimeError("pipeline crashed")
        )
        callback = view._make_toggle_callback("economy")
        await callback(interaction)

    safe_followup_mock.assert_awaited_once()
    args, kwargs = safe_followup_mock.await_args
    assert "Could not update" in args[1]
    assert kwargs.get("ephemeral") is True
    # State must not be mutated on failure.
    assert view._visibility["economy"] is None
    interaction.response.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# Navigation dead-end fix (audit §9.3): the toggle grid must keep a Back button
# ---------------------------------------------------------------------------


def test_toggle_view_rebuild_keeps_a_back_button():
    """`_rebuild_buttons` wipes all children every refresh; it must
    re-attach the Back nav so the grid is not a dead-end."""
    view = _build_toggle_view()
    view._visibility = {}
    view._rebuild_buttons()

    back_buttons = [
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "channels:visibility:toggle:back"
    ]
    assert len(back_buttons) == 1, "toggle grid lost its Back button (dead-end)"


def test_toggle_view_back_button_survives_repeated_rebuilds():
    """Toggling cycles call `_rebuild_buttons` repeatedly — the Back
    button must not duplicate or vanish across refreshes."""
    view = _build_toggle_view()
    view._visibility = {}
    view._rebuild_buttons()
    view._rebuild_buttons()
    view._rebuild_buttons()

    back_buttons = [
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "channels:visibility:toggle:back"
    ]
    assert len(back_buttons) == 1
