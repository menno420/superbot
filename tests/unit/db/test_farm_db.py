"""chicken_farm CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import farm


@pytest.mark.asyncio
async def test_top_farmers_orders_by_flock_then_coop():
    with patch(
        "utils.db.games.farm.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[
            {"user_id": 7, "chickens": 12, "coop_level": 3},
            {"user_id": 9, "chickens": 1, "coop_level": 0},
        ],
    ) as mock_fetch:
        out = await farm.top_farmers(1, limit=5)
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    # Flock size first, coop level as the tie-break.
    assert "ORDER BY chickens DESC, coop_level DESC" in flat
    # Empty (0-hen) farms never appear on the board.
    assert "chickens > 0" in flat
    assert params == (1, 5)
    assert out == [(7, 12, 3), (9, 1, 0)]


@pytest.mark.asyncio
async def test_top_farmers_default_limit_is_ten():
    with patch(
        "utils.db.games.farm.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_fetch:
        out = await farm.top_farmers(42)
    _, params = mock_fetch.await_args.args
    assert params == (42, 10)
    assert out == []
