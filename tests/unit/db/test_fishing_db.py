"""fishing_catch_log CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import fishing


@pytest.mark.asyncio
async def test_record_catch_upserts_count_only():
    with patch(
        "utils.db.games.fishing.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await fishing.record_catch(99, 1, "trout")
    query, params = mock_exec.await_args.args
    flat = " ".join(query.split())
    assert "INSERT INTO fishing_catch_log (user_id, guild_id, species, count)" in flat
    assert "ON CONFLICT (user_id, guild_id, species) DO UPDATE" in flat
    assert "count = fishing_catch_log.count + 1" in flat
    # No coin/value column is touched (v1 has no coins — Q-0175).
    assert "total_value" not in flat
    assert "best_weight" not in flat
    assert params == (99, 1, "trout")


@pytest.mark.asyncio
async def test_top_fishers_filters_to_known_species():
    known = ["minnow", "trout", "shark"]
    with patch(
        "utils.db.games.fishing.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"user_id": 7, "caught": 12, "species": 3}],
    ) as mock_fetch:
        out = await fishing.top_fishers(1, known, limit=5)
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    # The current-catalog allow-list keeps legacy rows out of the leaderboard.
    assert "species = ANY($2::text[])" in flat
    assert params == (1, known, 5)
    assert out == [(7, 12, 3)]


@pytest.mark.asyncio
async def test_top_fishers_empty_allow_list_short_circuits():
    with patch(
        "utils.db.games.fishing.pool.fetchall",
        new_callable=AsyncMock,
    ) as mock_fetch:
        out = await fishing.top_fishers(1, [])
    assert out == []
    mock_fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_fishing_log_returns_species_to_count():
    with patch(
        "utils.db.games.fishing.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"species": "trout", "count": 4}, {"species": "bass", "count": 1}],
    ):
        log = await fishing.get_fishing_log(99, 1)
    assert log == {"trout": 4, "bass": 1}
