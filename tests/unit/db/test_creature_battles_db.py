"""creature_battle_record CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import creature_battles


@pytest.mark.asyncio
async def test_record_battle_outcome_bumps_winner_then_loser():
    with patch(
        "utils.db.games.creature_battles.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await creature_battles.record_battle_outcome(7, 9, 1)
    assert mock_exec.await_count == 2
    (q1, p1), _ = mock_exec.await_args_list[0]
    (q2, p2), _ = mock_exec.await_args_list[1]
    flat = " ".join(q1.split())
    assert (
        "INSERT INTO creature_battle_record (user_id, guild_id, wins, losses)" in flat
    )
    assert "ON CONFLICT (user_id, guild_id) DO UPDATE" in flat
    assert "wins = creature_battle_record.wins + $3" in flat
    # Winner gets the (1, 0) delta, loser the (0, 1) delta.
    assert p1 == (7, 1, 1, 0)
    assert p2 == (9, 1, 0, 1)


@pytest.mark.asyncio
async def test_get_battle_record_returns_zero_zero_when_absent():
    with patch(
        "utils.db.games.creature_battles.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await creature_battles.get_battle_record(7, 1) == (0, 0)


@pytest.mark.asyncio
async def test_get_battle_record_returns_wins_losses():
    with patch(
        "utils.db.games.creature_battles.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"wins": 5, "losses": 2},
    ):
        assert await creature_battles.get_battle_record(7, 1) == (5, 2)


@pytest.mark.asyncio
async def test_top_battlers_orders_by_wins_and_filters_winless():
    with patch(
        "utils.db.games.creature_battles.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"user_id": 7, "wins": 9, "losses": 2}],
    ) as mock_fetch:
        out = await creature_battles.top_battlers(1, limit=5)
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    assert "wins > 0" in flat
    assert "ORDER BY wins DESC, losses ASC, user_id ASC" in flat
    assert params == (1, 5)
    assert out == [(7, 9, 2)]
