"""fishing_rod CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import fishing_rod


@pytest.mark.asyncio
async def test_get_rod_tier_defaults_to_zero_when_no_row():
    with patch(
        "utils.db.games.fishing_rod.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        tier = await fishing_rod.get_rod_tier(99, 1)
    assert tier == 0  # absent row → starter rod


@pytest.mark.asyncio
async def test_get_rod_tier_reads_the_stored_tier():
    with patch(
        "utils.db.games.fishing_rod.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"tier": 3},
    ):
        tier = await fishing_rod.get_rod_tier(99, 1)
    assert tier == 3


@pytest.mark.asyncio
async def test_set_rod_tier_upserts_the_tier():
    with patch(
        "utils.db.games.fishing_rod.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await fishing_rod.set_rod_tier(99, 1, 2)
    query, params = mock_exec.await_args.args
    flat = " ".join(query.split())
    assert "INSERT INTO fishing_rod (user_id, guild_id, tier)" in flat
    assert "ON CONFLICT (user_id, guild_id) DO UPDATE SET tier = $3" in flat
    assert params == (99, 1, 2)
