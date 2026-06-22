"""fishing_bait CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import fishing_bait


@pytest.mark.asyncio
async def test_get_active_bait_defaults_to_none_when_no_row():
    with patch(
        "utils.db.games.fishing_bait.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        key, charges = await fishing_bait.get_active_bait(99, 1)
    assert (key, charges) == ("", 0)  # absent row → no bait


@pytest.mark.asyncio
async def test_get_active_bait_reads_the_stored_loadout():
    with patch(
        "utils.db.games.fishing_bait.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"bait_key": "worm", "charges": 7},
    ):
        key, charges = await fishing_bait.get_active_bait(99, 1)
    assert (key, charges) == ("worm", 7)


@pytest.mark.asyncio
async def test_set_active_bait_upserts_key_and_charges():
    with patch(
        "utils.db.games.fishing_bait.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await fishing_bait.set_active_bait(99, 1, "lure", 10)
    query, params = mock_exec.await_args.args
    flat = " ".join(query.split())
    assert "INSERT INTO fishing_bait (user_id, guild_id, bait_key, charges)" in flat
    assert "ON CONFLICT (user_id, guild_id) DO UPDATE SET" in flat
    assert params == (99, 1, "lure", 10)


@pytest.mark.asyncio
async def test_clear_active_bait_writes_the_empty_loadout():
    with patch(
        "utils.db.games.fishing_bait.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await fishing_bait.clear_active_bait(99, 1)
    _query, params = mock_exec.await_args.args
    assert params == (99, 1, "", 0)  # back to bait-less
