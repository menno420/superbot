"""creature_collection_log CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import creatures


@pytest.mark.asyncio
async def test_record_creature_catch_upserts_count_only():
    with patch(
        "utils.db.games.creatures.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await creatures.record_creature_catch(99, 1, "Cindling")
    query, params = mock_exec.await_args.args
    flat = " ".join(query.split())
    assert (
        "INSERT INTO creature_collection_log (user_id, guild_id, creature, count)"
        in flat
    )
    assert "ON CONFLICT (user_id, guild_id, creature) DO UPDATE" in flat
    assert "count = creature_collection_log.count + 1" in flat
    assert params == (99, 1, "Cindling")


@pytest.mark.asyncio
async def test_top_collectors_filters_to_known_creatures():
    known = ["Cindling", "Rippling", "Magmaul"]
    with patch(
        "utils.db.games.creatures.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"user_id": 7, "caught": 12, "creatures": 3}],
    ) as mock_fetch:
        out = await creatures.top_collectors(1, known, limit=5)
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    assert "creature = ANY($2::text[])" in flat
    assert params == (1, known, 5)
    assert out == [(7, 12, 3)]


@pytest.mark.asyncio
async def test_top_collectors_empty_allow_list_short_circuits():
    with patch(
        "utils.db.games.creatures.pool.fetchall",
        new_callable=AsyncMock,
    ) as mock_fetch:
        out = await creatures.top_collectors(1, [])
    assert out == []
    mock_fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_creature_collection_returns_creature_to_count():
    with patch(
        "utils.db.games.creatures.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[
            {"creature": "Cindling", "count": 4},
            {"creature": "Rippling", "count": 1},
        ],
    ):
        log = await creatures.get_creature_collection(99, 1)
    assert log == {"Cindling": 4, "Rippling": 1}
