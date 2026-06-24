"""Blackjack PvP settle-once contract.

``_resolve_pvp`` is reachable from both players' finish callbacks and the
instant-blackjack path. The ``SettleOnceMixin`` claim on ``_PvPState`` must make
a second resolution a no-op — no duplicate result embed, no redundant (idempotent)
wager settle. Part of the cross-game terminal contract
(``docs/planning/production-readiness/games-production-readiness-map-2026-06-12.md``).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


@pytest.mark.asyncio
async def test_resolve_pvp_settles_once_no_double_payout_or_post():
    from services.blackjack_state import _PvPState
    from views.blackjack.pvp_view import _resolve_pvp

    state = _PvPState(p1=100, p2=200, guild_id=111, bet=50, channel_id=333)
    state.results = {100: 20, 200: 18}  # p1 wins
    channel = MagicMock()
    channel.send = AsyncMock()

    with (
        patch(
            "views.blackjack.pvp_view._clear_pvp_match",
            new_callable=AsyncMock,
        ) as mock_clear,
        patch(
            "views.blackjack.pvp_view.game_wager_workflow.settle_pvp",
            new_callable=AsyncMock,
        ) as mock_settle,
        patch(
            "views.blackjack.pvp_view.game_wager_workflow.refund_pvp",
            new_callable=AsyncMock,
        ),
    ):
        await _resolve_pvp(state, channel)
        assert state.is_settled is True
        # A racing duplicate resolution must do nothing.
        await _resolve_pvp(state, channel)

    mock_settle.assert_awaited_once()
    channel.send.assert_awaited_once()
    mock_clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_pvp_tie_refunds_once():
    from services.blackjack_state import _PvPState
    from views.blackjack.pvp_view import _resolve_pvp

    state = _PvPState(p1=100, p2=200, guild_id=111, bet=50, channel_id=333)
    state.results = {100: 19, 200: 19}  # tie → refund
    channel = MagicMock()
    channel.send = AsyncMock()

    with (
        patch(
            "views.blackjack.pvp_view._clear_pvp_match",
            new_callable=AsyncMock,
        ),
        patch(
            "views.blackjack.pvp_view.game_wager_workflow.settle_pvp",
            new_callable=AsyncMock,
        ) as mock_settle,
        patch(
            "views.blackjack.pvp_view.game_wager_workflow.refund_pvp",
            new_callable=AsyncMock,
        ) as mock_refund,
    ):
        await _resolve_pvp(state, channel)
        await _resolve_pvp(state, channel)

    mock_refund.assert_awaited_once()
    mock_settle.assert_not_called()
    channel.send.assert_awaited_once()
