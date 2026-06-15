"""Regression tests for PR #1 — Economy → Work result navigation.

Before PR #1, after a successful job selection ``_JobSelect.callback``
disabled every child on ``_WorkSubView`` (including its ``↩ Back``
button) and then re-rendered the message with that disabled view —
the user landed on a dead-end result screen.

These tests pin the post-PR-#1 contract:

* On work completion the message is re-rendered with a fresh
  ``_WorkResultView`` (not the disabled-children ``_WorkSubView``).
* ``_WorkResultView`` carries a single ``↩ Back to Economy`` button
  with ``custom_id="economy:back"``, enabled, on row 0.
* The Back button returns to a fresh ``EconomyPanelView`` (not the
  stopped sub-view).
* Pre-completion cooldown and "not your menu" responses stay
  ephemeral.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.economy.work_panel import _JobSelect, _WorkResultView, _WorkSubView


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    author.display_name = "tester"
    author.display_avatar = MagicMock(url="https://example/avatar.png")
    author.mention = f"<@{id_}>"
    return author


# ---------------------------------------------------------------------------
# _JobSelect.callback swaps to a fresh _WorkResultView, not a disabled sub-view
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_job_select_replaces_subview_with_fresh_result_view():
    """After a successful work transaction the response view must be a
    fresh ``_WorkResultView`` — not the dropdown sub-view with every
    child disabled. This pins the dead-end fix from Bug #2.

    The callback defers immediately (handler does 4 DB ops + 2 service
    calls before the final edit), so the response edit lands via
    ``followup.edit_message`` rather than the inline
    ``response.edit_message``.
    """
    # ``janitor`` is a real job in cogs.economy._helpers.JOBS so the
    # _WorkSubView constructor (which looks up each available job in
    # the real dict to build the dropdown labels) succeeds. The
    # callback path then reads through patched DB / service helpers,
    # so the real-vs-patched JOBS distinction does not affect the
    # post-completion view swap that this test pins.
    sub_view = _WorkSubView(MagicMock(id=1), guild_id=2, available=["janitor"])
    select = next(c for c in sub_view.children if isinstance(c, _JobSelect))
    select._values = ["janitor"]  # type: ignore[attr-defined]

    interaction = MagicMock()
    interaction.user = _author(id_=1)
    interaction.guild_id = 2
    interaction.message = MagicMock()
    interaction.message.id = 1234
    # safe_defer: is_done() == False on first check → defer is called.
    # safe_edit: is_done() == True on the next check → followup path.
    interaction.response.is_done = MagicMock(side_effect=[False, True])
    interaction.response.defer = AsyncMock()
    interaction.followup.edit_message = AsyncMock()
    interaction.client = MagicMock()

    eco_row = {"last_worked": 0}

    xp_result = MagicMock()
    xp_result.new_level = 1
    xp_result.leveled_up = False

    with (
        patch(
            "views.economy.work_panel.db.ensure_and_get_economy",
            new_callable=AsyncMock,
            return_value=eco_row,
        ),
        patch(
            "views.economy.work_panel.check_cooldown",
            return_value=(False, 0),
        ),
        patch(
            "views.economy.work_panel.db.get_job_times",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "views.economy.work_panel._job_pay",
            return_value=100,
        ),
        patch(
            "views.economy.work_panel.db.increment_job",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "views.economy.work_panel.economy_service.credit",
            new_callable=AsyncMock,
            return_value=500,
        ),
        patch(
            "views.economy.work_panel.xp_service.award",
            new_callable=AsyncMock,
            return_value=xp_result,
        ),
        patch(
            "views.economy.work_panel.db.set_last_worked",
            new_callable=AsyncMock,
        ),
        patch(
            "views.economy.work_panel.post_log_embed",
            new_callable=AsyncMock,
        ),
    ):
        await select.callback(interaction)

    interaction.response.defer.assert_awaited_once()
    interaction.followup.edit_message.assert_awaited_once()
    kwargs = interaction.followup.edit_message.await_args.kwargs
    rendered_view = kwargs["view"]
    assert isinstance(
        rendered_view,
        _WorkResultView,
    ), f"Expected _WorkResultView after job completion, got {type(rendered_view).__name__}"
    assert kwargs["message_id"] == 1234


# ---------------------------------------------------------------------------
# _WorkResultView shape — Back button enabled with the canonical custom_id
# ---------------------------------------------------------------------------


def test_work_result_view_has_one_enabled_back_button():
    view = _WorkResultView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 1
    btn = buttons[0]
    assert btn.custom_id == "economy:back"
    assert btn.disabled is False
    assert btn.row == 0
    assert btn.label is not None and "Back to Economy" in btn.label


@pytest.mark.asyncio
async def test_work_result_view_rejects_other_user_ephemerally():
    """The result view is invoker-restricted; other users must get an
    ephemeral, not a panel edit.
    """
    view = _WorkResultView(_author(id_=1))
    other = MagicMock()
    other.id = 99
    interaction = MagicMock()
    interaction.user = other
    interaction.response.send_message = AsyncMock()

    allowed = await view.interaction_check(interaction)
    assert allowed is False
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# Back button rebuilds the EconomyPanelView
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_work_result_back_button_returns_to_economy_panel():
    """Clicking Back returns to a fresh ``EconomyPanelView`` with the
    economy overview embed.

    The back button is constructed via
    ``views.navigation.attach_back_button``, which calls the
    parent-builder closure and then routes the edit through
    ``response.edit_message`` (when the interaction is not yet
    deferred) or ``edit_original_response`` (when deferred). This
    test pins the not-yet-deferred path.
    """
    from views.economy.main_panel import EconomyPanelView

    view = _WorkResultView(_author(id_=1))
    btn = next(c for c in view.children if isinstance(c, discord.ui.Button))

    interaction = MagicMock()
    interaction.user = _author(id_=1)
    interaction.guild_id = 2
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    with patch(
        "views.economy.work_panel._build_economy_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="Economy"),
    ):
        await btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert isinstance(kwargs["view"], EconomyPanelView)


# ---------------------------------------------------------------------------
# #2 regression — the Work path propagates the hub back chain (no lost back)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_work_subview_back_re_attaches_grandparent_chain():
    """Opened with a back_target (e.g. back-to-Help from !economymenu), the
    Work sub-view's ↩ Back rebuilds Economy with the grandparent re-attached —
    the back button is no longer dropped mid-navigation.
    """
    from views.economy.main_panel import EconomyPanelView
    from views.navigation import BackTarget

    async def _grandparent_builder(_interaction):  # pragma: no cover - not invoked
        return discord.Embed(title="Help"), EconomyPanelView()

    grandparent = BackTarget(
        builder=_grandparent_builder,
        label="↩ Back to Help",
        custom_id="help:back",
    )
    sub = _WorkSubView(
        MagicMock(id=1),
        guild_id=2,
        available=["janitor"],
        back_target=grandparent,
    )
    # stored for further-down propagation (e.g. the result view)
    assert sub._back_target is grandparent
    back_btn = next(
        c
        for c in sub.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "economy:work:back"
    )

    interaction = MagicMock()
    interaction.user = _author(id_=1)
    interaction.guild_id = 2
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    with patch(
        "views.economy.work_panel._build_economy_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="Economy"),
    ):
        await back_btn.callback(interaction)

    rebuilt = interaction.response.edit_message.await_args.kwargs["view"]
    assert isinstance(rebuilt, EconomyPanelView)
    # chain_back re-attached the grandparent's back button + target on Economy:
    assert getattr(rebuilt, "_back_target", None) is grandparent
    assert any(
        isinstance(c, discord.ui.Button) and c.custom_id == "help:back"
        for c in rebuilt.children
    )
