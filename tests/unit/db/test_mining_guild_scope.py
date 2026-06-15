"""PR M3 — mining CRUD must scope every read/write by guild_id.

Closes the multi-tenancy data leak identified in the audit:

  * Migration 002 added ``guild_id BIGINT NOT NULL DEFAULT 0`` to
    ``mining_inventory`` but the CRUD ignored it.
  * Migration 005 fixed deathmatch_stats and rps_players to a composite
    PK ``(user_id, guild_id)``; mining_inventory was missed.
  * Migration 017 (PR M2) widened the PK to
    ``(user_id, guild_id, item_name)``; this test pack covers the
    CRUD signatures that depend on it.

What's verified:
  * Every read and write carries (user_id, guild_id) parameters.
  * ``set_mining_inventory`` only deletes the calling guild's rows.
  * ``get_all_mining_totals`` filters on guild_id.
  * Function signatures require guild_id (no defaults).
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db.games import mining


@pytest.mark.asyncio
async def test_get_mining_inventory_filters_by_guild_id():
    with patch(
        "utils.db.games.mining.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_fetch:
        result = await mining.get_mining_inventory("12345", 999)
    assert result == {}
    mock_fetch.assert_awaited_once()
    query, params = mock_fetch.await_args.args
    assert "guild_id=$2" in query.replace(" ", "")
    assert params == ("12345", 999)


@pytest.mark.asyncio
async def test_update_mining_item_writes_with_guild_id_in_pk_conflict():
    """The ON CONFLICT target must include guild_id so concurrent writes
    from two guilds for the same user+item do NOT collide.
    """
    with patch(
        "utils.db.games.mining.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mining.update_mining_item("12345", 999, "iron", 5)
    mock_exec.assert_awaited_once()
    query, params = mock_exec.await_args.args
    assert "(user_id, guild_id, item_name)" in query
    assert params == ("12345", 999, "iron", 5)


@pytest.mark.asyncio
async def test_update_mining_item_two_guilds_two_rows():
    """Mining the same item from two different guilds must not merge
    into a single row.  Verified by checking that both writes pass
    distinct guild_id values in their params.
    """
    with patch(
        "utils.db.games.mining.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mining.update_mining_item("12345", 111, "iron", 5)
        await mining.update_mining_item("12345", 222, "iron", 3)
    assert mock_exec.await_count == 2
    seen = {call.args[1] for call in mock_exec.await_args_list}
    # Different guilds → different params tuples.
    assert {("12345", 111, "iron", 5), ("12345", 222, "iron", 3)} == seen


@pytest.mark.asyncio
async def test_set_mining_inventory_scopes_delete_to_guild():
    """``set_mining_inventory`` is the admin reset path.  The previous
    unscoped DELETE swept every guild's inventory for the target user;
    now it must only touch the calling guild's rows.
    """
    # Build a connection mock matching the asyncpg acquire-pattern:
    # pool.get() returns a Pool stub whose acquire() returns an async
    # context manager yielding a Connection-like object.
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.executemany = AsyncMock()
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)
    pool_stub = MagicMock(acquire=MagicMock(return_value=acquire_cm))

    with patch("utils.db.games.mining.pool.get", return_value=pool_stub):
        await mining.set_mining_inventory("12345", 999, {"iron": 3})

    # DELETE must scope to (user_id, guild_id) — not just user_id.
    conn.execute.assert_awaited_once()
    delete_sql, *args = conn.execute.await_args.args
    assert "user_id=$1 AND guild_id=$2" in delete_sql.replace("  ", " ")
    assert args == ["12345", 999]

    # executemany payload must carry guild_id in every row.
    conn.executemany.assert_awaited_once()
    _insert_sql, payload = conn.executemany.await_args.args
    assert all(
        row[1] == 999 for row in payload
    ), f"set_mining_inventory must include guild_id in every row; got {payload!r}"


@pytest.mark.asyncio
async def test_set_mining_inventory_empty_dict_only_deletes():
    """Passing an empty dict is the documented "reset" shape — only the
    DELETE runs, no INSERTs.  Ensures the previous behaviour is
    preserved post-scope-tightening.
    """
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.executemany = AsyncMock()
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)
    pool_stub = MagicMock(acquire=MagicMock(return_value=acquire_cm))

    with patch("utils.db.games.mining.pool.get", return_value=pool_stub):
        await mining.set_mining_inventory("12345", 999, {})

    conn.execute.assert_awaited_once()
    conn.executemany.assert_not_called()


@pytest.mark.asyncio
async def test_get_all_mining_totals_filters_by_guild_id():
    with patch(
        "utils.db.games.mining.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_fetch:
        result = await mining.get_all_mining_totals(777)
    assert result == []
    query, params = mock_fetch.await_args.args
    assert "guild_id=$1" in query.replace(" ", "")
    assert params == (777,)


def test_get_mining_inventory_signature_requires_guild_id():
    sig = inspect.signature(mining.get_mining_inventory)
    param = sig.parameters["guild_id"]
    assert (
        param.default is inspect.Parameter.empty
    ), "get_mining_inventory.guild_id must be required (no default)."


def test_update_mining_item_signature_requires_guild_id():
    sig = inspect.signature(mining.update_mining_item)
    param = sig.parameters["guild_id"]
    assert param.default is inspect.Parameter.empty


def test_set_mining_inventory_signature_requires_guild_id():
    sig = inspect.signature(mining.set_mining_inventory)
    param = sig.parameters["guild_id"]
    assert param.default is inspect.Parameter.empty


def test_get_all_mining_totals_signature_requires_guild_id():
    sig = inspect.signature(mining.get_all_mining_totals)
    param = sig.parameters["guild_id"]
    assert param.default is inspect.Parameter.empty, (
        "get_all_mining_totals.guild_id must be required (no default).  "
        "Without it, the leaderboard query sums across every guild."
    )
