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
    from cogs import chain_cog

    fake_channel = SimpleNamespace(id=123, mention="#chain")
    monkeypatch.setattr(
        chain_cog, "_resolve_channel", lambda _interaction, _value: fake_channel
    )
    monkeypatch.setattr(
        chain_cog.db, "get_chain_channel", AsyncMock(return_value={"word_limit": 5})
    )
    set_limit = AsyncMock()
    monkeypatch.setattr(chain_cog.db, "set_chain_limit", set_limit)

    modal = chain_cog._ClearLimitModal(MagicMock())
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    await modal.on_submit(interaction)

    set_limit.assert_awaited_once_with(123, 0)


@pytest.mark.asyncio
async def test_clear_limit_modal_noops_when_no_limit(monkeypatch):
    from cogs import chain_cog

    fake_channel = SimpleNamespace(id=123, mention="#chain")
    monkeypatch.setattr(
        chain_cog, "_resolve_channel", lambda _interaction, _value: fake_channel
    )
    monkeypatch.setattr(
        chain_cog.db, "get_chain_channel", AsyncMock(return_value=None)
    )
    set_limit = AsyncMock()
    monkeypatch.setattr(chain_cog.db, "set_chain_limit", set_limit)

    modal = chain_cog._ClearLimitModal(MagicMock())
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    await modal.on_submit(interaction)

    set_limit.assert_not_awaited()
