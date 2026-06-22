"""fishing_energy CRUD — SQL-shape pins (mock-pool idiom)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import fishing_energy


@pytest.mark.asyncio
async def test_get_fishing_energy_defaults_to_a_full_bar_when_no_row():
    with patch(
        "utils.db.games.fishing_energy.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        cur, ts = await fishing_energy.get_fishing_energy(99, 1)
    assert (cur, ts) == (20, 0)  # full bar @ epoch → settles to full


@pytest.mark.asyncio
async def test_get_fishing_energy_reads_the_stored_row():
    with patch(
        "utils.db.games.fishing_energy.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"energy": 7, "energy_updated_at": 12345},
    ):
        cur, ts = await fishing_energy.get_fishing_energy(99, 1)
    assert (cur, ts) == (7, 12345)


@pytest.mark.asyncio
async def test_set_fishing_energy_upserts_value_and_timestamp():
    with patch(
        "utils.db.games.fishing_energy.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await fishing_energy.set_fishing_energy(99, 1, 6, 999)
    query, params = mock_exec.await_args.args
    flat = " ".join(query.split())
    assert "INSERT INTO fishing_energy (user_id, guild_id, energy, energy_updated_at)" in flat
    assert "ON CONFLICT (user_id, guild_id) DO UPDATE" in flat
    assert params == (99, 1, 6, 999)
