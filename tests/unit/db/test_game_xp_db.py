"""game_xp + depth-record CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import game_xp, mining_player_state

_TODAY = datetime.date(2026, 6, 10)


@pytest.mark.asyncio
async def test_add_game_xp_single_upsert_with_day_rollover():
    with patch(
        "utils.db.games.game_xp.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"xp": 42},
    ) as mock_fetch:
        total = await game_xp.add_game_xp(1, 99, "mining", 5, day=_TODAY)
    assert total == 42
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    assert "ON CONFLICT (user_id, guild_id, game) DO UPDATE" in flat
    assert "xp = game_xp.xp + $4" in flat
    # Day rollover: same day accumulates, a new day restarts at the amount.
    assert "CASE WHEN game_xp.day = $5 THEN game_xp.day_xp + $4 ELSE $4 END" in flat
    assert "RETURNING xp" in flat
    assert params == (1, 99, "mining", 5, _TODAY)


@pytest.mark.asyncio
async def test_get_total_xp_sums_across_games():
    with patch(
        "utils.db.games.game_xp.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"total": 17},
    ) as mock_fetch:
        total = await game_xp.get_total_xp(1, 99)
    assert total == 17
    query, _ = mock_fetch.await_args.args
    assert "COALESCE(SUM(xp), 0)" in query


@pytest.mark.asyncio
async def test_top_total_xp_groups_by_user():
    with patch(
        "utils.db.games.game_xp.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"user_id": 1, "total": 30}, {"user_id": 2, "total": 10}],
    ) as mock_fetch:
        rows = await game_xp.top_total_xp(99)
    assert rows == [(1, 30), (2, 10)]
    query, params = mock_fetch.await_args.args
    assert "GROUP BY user_id ORDER BY total DESC" in " ".join(query.split())
    assert params == (99, 10)


@pytest.mark.asyncio
async def test_record_depth_conditional_upsert_decides_and_writes_together():
    with patch(
        "utils.db.games.mining_player_state.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"max_depth": 2},
    ) as mock_fetch:
        assert await mining_player_state.record_depth("1", 99, 2) is True
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    assert "WHERE mining_player_state.max_depth < $3" in flat
    assert "RETURNING max_depth" in flat
    assert params == ("1", 99, 2)


@pytest.mark.asyncio
async def test_record_depth_returns_false_when_record_stands():
    with patch(
        "utils.db.games.mining_player_state.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await mining_player_state.record_depth("1", 99, 1) is False
