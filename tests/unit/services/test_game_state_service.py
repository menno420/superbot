"""Tests for services.game_state_service (P2 PR-13)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import game_state_service


@pytest.mark.asyncio
async def test_save_upserts_jsonb_payload():
    state = {"hand": [1, 5, 7], "phase": "deal"}
    with patch(
        "services.game_state_service.pool.execute",
        new_callable=AsyncMock,
    ) as execute:
        await game_state_service.save(
            guild_id=1, user_id=2, channel_id=3,
            subsystem="blackjack",
            state=state,
        )
    execute.assert_awaited_once()
    args = execute.await_args.args
    # SQL begins with INSERT INTO game_state
    assert args[0].startswith("INSERT INTO game_state")
    # The payload is JSON-encoded and matches.
    params = args[1]
    assert params[0] == 1 and params[1] == 2 and params[2] == 3
    assert params[3] == "blackjack"
    assert json.loads(params[4]) == state
    # PR G0: version is the 6th param, defaults to 1.
    assert params[5] == 1


@pytest.mark.asyncio
async def test_save_writes_explicit_version():
    """PR G0: cogs can pass version=N to track payload-schema generation."""
    with patch(
        "services.game_state_service.pool.execute",
        new_callable=AsyncMock,
    ) as execute:
        await game_state_service.save(
            guild_id=1, user_id=2, channel_id=3,
            subsystem="blackjack",
            state={"hand": []},
            version=3,
        )
    execute.assert_awaited_once()
    params = execute.await_args.args[1]
    assert params[5] == 3


@pytest.mark.asyncio
async def test_load_returns_decoded_dict():
    with patch(
        "services.game_state_service.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"state": '{"hand": [1, 2]}'},
    ):
        result = await game_state_service.load(
            guild_id=1, user_id=2, channel_id=3,
            subsystem="blackjack",
        )
    assert result == {"hand": [1, 2]}


@pytest.mark.asyncio
async def test_load_accepts_pre_decoded_jsonb():
    """asyncpg may decode JSONB to dict before we see it; handle both shapes."""
    with patch(
        "services.game_state_service.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"state": {"hand": [1, 2]}},
    ):
        result = await game_state_service.load(
            guild_id=1, user_id=2, channel_id=3,
            subsystem="blackjack",
        )
    assert result == {"hand": [1, 2]}


@pytest.mark.asyncio
async def test_load_returns_none_when_missing():
    with patch(
        "services.game_state_service.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await game_state_service.load(
            guild_id=1, user_id=2, channel_id=3,
            subsystem="blackjack",
        )
    assert result is None


@pytest.mark.asyncio
async def test_clear_deletes_by_key():
    with patch(
        "services.game_state_service.pool.execute",
        new_callable=AsyncMock,
    ) as execute:
        await game_state_service.clear(
            guild_id=1, user_id=2, channel_id=3,
            subsystem="blackjack",
        )
    execute.assert_awaited_once()
    assert execute.await_args.args[0].startswith("DELETE FROM game_state")


@pytest.mark.asyncio
async def test_list_active_for_subsystem_returns_decoded_rows():
    rows = [
        {
            "guild_id": 1,
            "user_id": 100,
            "channel_id": 200,
            "state": '{"hand": [1, 2]}',
            "version": 1,
            "updated_at": "2025-01-01",
        },
        {
            "guild_id": 1,
            "user_id": 101,
            "channel_id": 201,
            "state": {"hand": [3, 4]},
            "version": 2,
            "updated_at": "2025-01-02",
        },
    ]
    fake_pool = MagicMock()
    fake_pool.fetch = AsyncMock(return_value=rows)
    with patch(
        "services.game_state_service.pool.get",
        return_value=fake_pool,
    ):
        result = await game_state_service.list_active_for_subsystem("blackjack")

    assert len(result) == 2
    assert result[0]["state"] == {"hand": [1, 2]}
    assert result[0]["version"] == 1
    assert result[1]["state"] == {"hand": [3, 4]}
    assert result[1]["version"] == 2
    assert result[0]["guild_id"] == 1


# ---------------------------------------------------------------------------
# PR G0 — GC helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_stale_returns_rows_with_id_and_version():
    """``list_stale`` returns synthetic ``id`` for precise per-row delete."""
    rows = [
        {
            "id": 42,
            "guild_id": 1,
            "user_id": 100,
            "channel_id": 200,
            "subsystem": "blackjack_solo",
            "state": '{"bet": 50, "hand": []}',
            "version": 1,
            "updated_at": "2025-01-01",
        },
    ]
    fake_pool = MagicMock()
    fake_pool.fetch = AsyncMock(return_value=rows)
    with patch(
        "services.game_state_service.pool.get",
        return_value=fake_pool,
    ):
        result = await game_state_service.list_stale()
    assert len(result) == 1
    assert result[0]["id"] == 42
    assert result[0]["subsystem"] == "blackjack_solo"
    assert result[0]["state"] == {"bet": 50, "hand": []}
    assert result[0]["version"] == 1


@pytest.mark.asyncio
async def test_list_stale_query_uses_cutoff_hours():
    fake_pool = MagicMock()
    fake_pool.fetch = AsyncMock(return_value=[])
    with patch(
        "services.game_state_service.pool.get",
        return_value=fake_pool,
    ):
        await game_state_service.list_stale(cutoff_hours=12)
    args = fake_pool.fetch.await_args.args
    # cutoff_hours is the only parameter.
    assert 12 in args


@pytest.mark.asyncio
async def test_clear_by_id_deletes_one_row():
    with patch(
        "services.game_state_service.pool.execute",
        new_callable=AsyncMock,
    ) as execute:
        await game_state_service.clear_by_id(42)
    execute.assert_awaited_once()
    query, params = execute.await_args.args
    assert "DELETE FROM game_state WHERE id=$1" in query
    assert params == (42,)


@pytest.mark.asyncio
async def test_list_active_for_subsystem_filters_by_guild():
    fake_pool = MagicMock()
    fake_pool.fetch = AsyncMock(return_value=[])
    with patch(
        "services.game_state_service.pool.get",
        return_value=fake_pool,
    ):
        await game_state_service.list_active_for_subsystem(
            "blackjack",
            guild_id=42,
        )
    # Verify guild_id is in the parameter list.
    args = fake_pool.fetch.await_args.args
    assert 42 in args
