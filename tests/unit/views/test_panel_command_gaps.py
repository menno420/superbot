"""Tests for the idea-box command->panel gap closures (Ideas-Lab section 4.1):

* RPS tournament "Create Matchup" button (exposes ``!rpsmatchup``).
* Chain "Clear Limit" button + modal (exposes ``!chain removelimit``).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest


def _button_labels(view) -> list[str]:
    return [
        c.label or "" for c in view.children if isinstance(c, discord.ui.Button)
    ]


# ---------------------------------------------------------------------------
# RPS — Create Matchup button
# ---------------------------------------------------------------------------


def test_rps_tournament_subview_shows_matchup_button_for_admin_when_active():
    from views.games.rps_panel import _RpsTournamentSubView

    view = _RpsTournamentSubView(
        MagicMock(),
        is_admin=True,
        registration_active=False,
        tournament_active=True,
    )
    assert any("Matchup" in lbl for lbl in _button_labels(view))


def test_rps_tournament_subview_hides_matchup_for_non_admin():
    from views.games.rps_panel import _RpsTournamentSubView

    view = _RpsTournamentSubView(
        MagicMock(),
        is_admin=False,
        registration_active=False,
        tournament_active=True,
    )
    assert not any("Matchup" in lbl for lbl in _button_labels(view))


# ---------------------------------------------------------------------------
# Chain — Clear Limit button + modal
# ---------------------------------------------------------------------------


def test_chain_menu_view_has_clear_limit_button():
    from cogs.chain_cog import _ChainMenuView

    view = _ChainMenuView(MagicMock(), MagicMock())
    assert any("Clear Limit" in lbl for lbl in _button_labels(view))


@pytest.mark.asyncio
async def test_clear_limit_modal_clears_existing_limit(monkeypatch):
    """The modal routes through chain_service (RS07); the write still
    lands as set_chain_limit(channel, 0) at the DB seam.
    """
    from cogs import chain_cog
    from services import chain_service

    fake_channel = SimpleNamespace(id=123, mention="#chain")
    monkeypatch.setattr(
        chain_cog, "_resolve_channel", lambda _interaction, _value: fake_channel,
    )
    monkeypatch.setattr(
        chain_service.db,
        "get_chain_channel",
        AsyncMock(return_value={"word_limit": 5}),
    )
    set_limit = AsyncMock()
    monkeypatch.setattr(chain_service.db, "set_chain_limit", set_limit)
    monkeypatch.setattr(
        chain_service, "emit_audit_action", AsyncMock(return_value=True),
    )

    modal = chain_cog._ClearLimitModal(MagicMock())
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    await modal.on_submit(interaction)

    set_limit.assert_awaited_once_with(123, 0)


@pytest.mark.asyncio
async def test_clear_limit_modal_noops_when_no_limit(monkeypatch):
    from cogs import chain_cog
    from services import chain_service

    fake_channel = SimpleNamespace(id=123, mention="#chain")
    monkeypatch.setattr(
        chain_cog, "_resolve_channel", lambda _interaction, _value: fake_channel,
    )
    monkeypatch.setattr(
        chain_service.db, "get_chain_channel", AsyncMock(return_value=None),
    )
    set_limit = AsyncMock()
    monkeypatch.setattr(chain_service.db, "set_chain_limit", set_limit)

    modal = chain_cog._ClearLimitModal(MagicMock())
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    await modal.on_submit(interaction)

    set_limit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Panel authority guards (pre-merge hardening)
# ---------------------------------------------------------------------------


def _interaction(*, user_id: int = 7, admin: bool = True):
    interaction = MagicMock()
    interaction.user.id = user_id
    interaction.user.guild_permissions.administrator = admin
    interaction.response.send_message = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_chain_menu_blocks_non_admin_interaction():
    from cogs.chain_cog import _ChainMenuView

    ctx = MagicMock()
    ctx.author.id = 7
    view = _ChainMenuView(ctx, MagicMock())
    interaction = _interaction(user_id=7, admin=False)  # invoker, but not admin
    assert await view.interaction_check(interaction) is False
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_chain_menu_allows_admin_interaction():
    from cogs.chain_cog import _ChainMenuView

    ctx = MagicMock()
    ctx.author.id = 7
    view = _ChainMenuView(ctx, MagicMock())
    interaction = _interaction(user_id=7, admin=True)
    assert await view.interaction_check(interaction) is True


@pytest.mark.asyncio
async def test_rps_matchup_button_denies_non_admin():
    from views.games.rps_panel import _RpsTournamentMatchupButton

    btn = _RpsTournamentMatchupButton()
    interaction = _interaction(admin=False)
    await btn.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    args, _ = interaction.response.send_message.call_args
    assert "admin-only" in args[0]


@pytest.mark.asyncio
async def test_rps_matchup_select_denies_non_admin_before_dispatch(monkeypatch):
    from views.games import rps_panel

    resolve_spy = MagicMock()
    monkeypatch.setattr(rps_panel, "_resolve_rps_cog", resolve_spy)
    sel = rps_panel._RpsMatchupSelect()
    interaction = _interaction(admin=False)
    await sel.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    resolve_spy.assert_not_called()  # bailed before resolving the cog / dispatch
