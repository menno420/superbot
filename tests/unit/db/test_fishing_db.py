"""fishing_catch_log CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import fishing


@pytest.mark.asyncio
async def test_record_catch_upserts_count_and_tracks_best_weight():
    with patch(
        "utils.db.games.fishing.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"prev_best": 1.2},
    ) as mock_fetch:
        prev = await fishing.record_catch(99, 1, "trout", 3.4)
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    assert (
        "INSERT INTO fishing_catch_log (user_id, guild_id, species, count, best_weight)"
        in flat
    )
    assert "ON CONFLICT (user_id, guild_id, species) DO UPDATE" in flat
    assert "count = fishing_catch_log.count + 1" in flat
    # best_weight only ever grows (GREATEST against the incoming catch).
    assert (
        "best_weight = GREATEST(fishing_catch_log.best_weight, EXCLUDED.best_weight)"
        in flat
    )
    # The prior best is captured (CTE) and returned so the caller can detect a PB.
    assert "WITH prev AS" in flat
    assert "RETURNING (SELECT best_weight FROM prev) AS prev_best" in flat
    # No coin/value column is touched (v1 has no coins — Q-0175).
    assert "total_value" not in flat
    assert params == (99, 1, "trout", 3.4)
    assert prev == 1.2


@pytest.mark.asyncio
async def test_record_catch_first_catch_returns_none():
    with patch(
        "utils.db.games.fishing.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"prev_best": None},
    ):
        prev = await fishing.record_catch(99, 1, "trout", 0.5)
    assert prev is None


@pytest.mark.asyncio
async def test_top_trophies_orders_by_weight_and_filters_known_species():
    known = ["minnow", "trout", "shark"]
    with patch(
        "utils.db.games.fishing.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"user_id": 7, "species": "shark", "best_weight": 12.5}],
    ) as mock_fetch:
        out = await fishing.top_trophies(1, known, limit=5)
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    assert "ORDER BY best_weight DESC" in flat
    assert "species = ANY($2::text[])" in flat  # current-catalog allow-list
    assert "best_weight > 0" in flat  # pre-trophy-era rows excluded
    assert params == (1, known, 5)
    assert out == [(7, "shark", 12.5)]


@pytest.mark.asyncio
async def test_top_trophies_empty_allow_list_short_circuits():
    with patch(
        "utils.db.games.fishing.pool.fetchall",
        new_callable=AsyncMock,
    ) as mock_fetch:
        out = await fishing.top_trophies(1, [])
    assert out == []
    mock_fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_fishing_records_returns_species_to_best_weight():
    with patch(
        "utils.db.games.fishing.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[
            {"species": "trout", "best_weight": 3.4},
            {"species": "bass", "best_weight": 1.1},
        ],
    ) as mock_fetch:
        records = await fishing.get_fishing_records(99, 1)
    query, _ = mock_fetch.await_args.args
    flat = " ".join(query.split())
    # Only species with a recorded best appear (post-migration legacy rows = 0).
    assert "best_weight > 0" in flat
    assert records == {"trout": 3.4, "bass": 1.1}


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
        return_value=[
            {"species": "trout", "count": 4},
            {"species": "bass", "count": 1},
        ],
    ):
        log = await fishing.get_fishing_log(99, 1)
    assert log == {"trout": 4, "bass": 1}
