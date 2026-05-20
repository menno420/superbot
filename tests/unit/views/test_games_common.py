"""PR 7 — shared game-panel helpers + deeper Back navigation.

Tests for ``views.games.common.BackToPanelButton`` and the
sub-view → main-panel Back chain it powers in the RPS panel. Other
game panels (Blackjack PR 5, Deathmatch PR 6) will migrate to use
the shared helper in a follow-up once their PRs merge.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.games.common import BackToPanelButton
from views.games.rps_panel import (
    RPSPanelView,
    _RpsBetPresetView,
    _RpsChallengeSelectView,
    build_rps_overview_embed,
)


def _author(id_: int = 1) -> SimpleNamespace:
    return SimpleNamespace(id=id_, display_name="tester", mention=f"<@{id_}>")


def _stub_interaction(user: SimpleNamespace) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = user
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.message = MagicMock(id=444)
    return interaction


# ---------------------------------------------------------------------------
# BackToPanelButton helper
# ---------------------------------------------------------------------------


def test_back_button_renders_with_label_and_custom_id():
    btn = BackToPanelButton(
        label="◀ Back to RPS",
        custom_id="rps_panel:back",
        panel_builder=lambda author: RPSPanelView(author),
        overview_builder=build_rps_overview_embed,
    )
    assert btn.label == "◀ Back to RPS"
    assert btn.custom_id == "rps_panel:back"
    assert btn.row == 4
    assert btn.style is discord.ButtonStyle.secondary


@pytest.mark.asyncio
async def test_back_button_callback_returns_panel_and_overview_embed():
    author = _author(42)
    parent_view = _RpsBetPresetView(author)  # type: ignore[arg-type]
    btn = next(
        c
        for c in parent_view.children
        if isinstance(c, BackToPanelButton)
    )
    interaction = _stub_interaction(author)
    await btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    # Embed = overview
    embed = kwargs["embed"]
    assert isinstance(embed, discord.Embed)
    assert "Rock Paper Scissors" in (embed.title or "")
    # View = a fresh main RPS panel
    new_view = kwargs["view"]
    assert isinstance(new_view, RPSPanelView)
    # Author preserved across the back nav (invoker-restriction stays
    # bound to the original opener).
    assert new_view._author is author


@pytest.mark.asyncio
async def test_back_button_falls_back_to_interaction_user_if_no_parent_author():
    """When the helper is attached to a bare view without ``_author``,
    the click should not crash — author falls back to
    ``interaction.user`` so the rebuilt panel still has a valid
    invoker.
    """
    btn = BackToPanelButton(
        label="◀ Back to RPS",
        custom_id="rps_panel:back",
        panel_builder=lambda author: RPSPanelView(author),
        overview_builder=build_rps_overview_embed,
    )
    bare = discord.ui.View()
    bare.add_item(btn)
    interaction = _stub_interaction(_author(99))
    await btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    new_view = kwargs["view"]
    assert isinstance(new_view, RPSPanelView)
    assert new_view._author.id == 99


# ---------------------------------------------------------------------------
# Chain-back: RPS sub-views all wire BackToPanelButton via the helper
# ---------------------------------------------------------------------------


def test_rps_bet_preset_view_includes_back_to_panel_button():
    view = _RpsBetPresetView(_author())  # type: ignore[arg-type]
    backs = [c for c in view.children if isinstance(c, BackToPanelButton)]
    assert len(backs) == 1
    assert backs[0].custom_id == "rps_panel:back"


def test_rps_challenge_select_view_includes_back_to_panel_button():
    view = _RpsChallengeSelectView(_author())  # type: ignore[arg-type]
    backs = [c for c in view.children if isinstance(c, BackToPanelButton)]
    assert len(backs) == 1


@pytest.mark.asyncio
async def test_rps_tournament_subview_includes_back_to_panel_button():
    """Tournament sub-view is constructed via ``btn_tournament`` rather
    than directly, so cover it via the panel's button callback path.
    """
    from views.games.rps_panel import _RpsTournamentSubView

    sub = _RpsTournamentSubView(
        _author(),  # type: ignore[arg-type]
        is_admin=False,
        registration_active=False,
        tournament_active=False,
    )
    backs = [c for c in sub.children if isinstance(c, BackToPanelButton)]
    assert len(backs) == 1


# ---------------------------------------------------------------------------
# Blackjack + Deathmatch migrations (follow-up to PR 7)
# ---------------------------------------------------------------------------


def test_blackjack_bet_preset_view_includes_shared_back_button():
    """Follow-up to PR 7: Blackjack now uses the shared
    ``BackToPanelButton`` helper instead of its local
    ``_BlackjackBackToPanelButton`` class.
    """
    from views.games.blackjack_panel import _BlackjackBetPresetView

    view = _BlackjackBetPresetView(_author())  # type: ignore[arg-type]
    backs = [c for c in view.children if isinstance(c, BackToPanelButton)]
    assert len(backs) == 1
    assert backs[0].custom_id == "blackjack_panel:back"


def test_blackjack_challenge_select_view_includes_shared_back_button():
    from views.games.blackjack_panel import _BlackjackChallengeSelectView

    view = _BlackjackChallengeSelectView(_author())  # type: ignore[arg-type]
    backs = [c for c in view.children if isinstance(c, BackToPanelButton)]
    assert len(backs) == 1


def test_blackjack_tournament_subview_includes_shared_back_button():
    from views.games.blackjack_panel import _BlackjackTournamentSubView

    sub = _BlackjackTournamentSubView(
        _author(),  # type: ignore[arg-type]
        is_admin=False,
        has_active=False,
    )
    backs = [c for c in sub.children if isinstance(c, BackToPanelButton)]
    assert len(backs) == 1


def test_deathmatch_challenge_select_view_includes_shared_back_button():
    from views.games.deathmatch_panel import _DeathmatchChallengeSelectView

    view = _DeathmatchChallengeSelectView(_author())  # type: ignore[arg-type]
    backs = [c for c in view.children if isinstance(c, BackToPanelButton)]
    assert len(backs) == 1
    assert backs[0].custom_id == "deathmatch_panel:back"


@pytest.mark.asyncio
async def test_blackjack_back_button_returns_blackjack_panel():
    """The Blackjack back button must rebuild ``BlackjackPanelView``
    on click — pin the helper wiring across the migration.
    """
    from views.games.blackjack_panel import (
        BlackjackPanelView,
        _BlackjackBetPresetView,
    )

    author = _author(42)
    parent = _BlackjackBetPresetView(author)  # type: ignore[arg-type]
    btn = next(c for c in parent.children if isinstance(c, BackToPanelButton))
    interaction = _stub_interaction(author)
    await btn.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs["view"], BlackjackPanelView)


@pytest.mark.asyncio
async def test_deathmatch_back_button_returns_deathmatch_panel():
    from views.games.deathmatch_panel import (
        DeathmatchPanelView,
        _DeathmatchChallengeSelectView,
    )

    author = _author(42)
    parent = _DeathmatchChallengeSelectView(author)  # type: ignore[arg-type]
    btn = next(c for c in parent.children if isinstance(c, BackToPanelButton))
    interaction = _stub_interaction(author)
    await btn.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs["view"], DeathmatchPanelView)
