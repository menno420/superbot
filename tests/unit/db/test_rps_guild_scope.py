"""PR R1 — rps CRUD must scope every write by guild_id.

Regression tests for the same multi-tenancy bug pattern as the mining
fix:

  * ``rps_update_stat`` previously defaulted ``guild_id=0`` and the
    single production caller never passed it, so every guild's stats
    merged at PK (user_id, 0).
  * Both ``rps_update_stat`` and ``rps_get_leaderboard`` now require
    ``guild_id``; passing it positionally is checked here so future
    refactors that drop the argument can't slip past the type system.

Additionally, the f-string column interpolation pattern is gone — the
three-arm ``match`` produces three distinct prepared statements with
no dynamic identifier interpolation.
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import rps


@pytest.mark.asyncio
async def test_rps_update_stat_writes_with_guild_id_win():
    with patch(
        "utils.db.games.rps.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await rps.rps_update_stat(12345, 999, "win")
    mock_exec.assert_awaited_once()
    query, params = mock_exec.await_args.args
    assert "wins=wins+1" in query
    assert "guild_id=$2" in query.replace(" ", "")
    assert params == (12345, 999)


@pytest.mark.asyncio
async def test_rps_update_stat_writes_with_guild_id_loss():
    with patch(
        "utils.db.games.rps.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await rps.rps_update_stat(12345, 999, "loss")
    mock_exec.assert_awaited_once()
    query, params = mock_exec.await_args.args
    assert "losses=losses+1" in query
    assert params == (12345, 999)


@pytest.mark.asyncio
async def test_rps_update_stat_writes_with_guild_id_tie():
    with patch(
        "utils.db.games.rps.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await rps.rps_update_stat(12345, 999, "tie")
    mock_exec.assert_awaited_once()
    query, params = mock_exec.await_args.args
    assert "ties=ties+1" in query
    assert params == (12345, 999)


@pytest.mark.asyncio
async def test_rps_update_stat_invalid_result_is_noop():
    """Unknown ``result`` values are silently dropped — no SQL emitted.

    Callers normalise the input upstream (resolve_match etc.); the CRUD
    function's defensive default prevents an upstream bug from
    triggering a SQL injection class regression.
    """
    with patch(
        "utils.db.games.rps.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await rps.rps_update_stat(12345, 999, "totally-not-a-result")
    mock_exec.assert_not_called()


@pytest.mark.asyncio
async def test_rps_update_stat_two_guilds_two_writes():
    """Two writes for the same user but different guilds must hit
    different rows (different params).
    """
    with patch(
        "utils.db.games.rps.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await rps.rps_update_stat(12345, 111, "win")
        await rps.rps_update_stat(12345, 222, "win")
    assert mock_exec.await_count == 2
    params_seen = {call.args[1] for call in mock_exec.await_args_list}
    assert (12345, 111) in params_seen
    assert (12345, 222) in params_seen


@pytest.mark.asyncio
async def test_rps_get_leaderboard_scopes_by_guild_id():
    with patch(
        "utils.db.games.rps.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_fetch:
        await rps.rps_get_leaderboard(7777)
    mock_fetch.assert_awaited_once()
    query, params = mock_fetch.await_args.args
    assert "guild_id=$1" in query.replace(" ", "")
    assert params == (7777,)


@pytest.mark.asyncio
async def test_rps_ensure_player_writes_with_guild_id():
    with patch(
        "utils.db.games.rps.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await rps.rps_ensure_player(42, 999, "Alice")
    mock_exec.assert_awaited_once()
    _query, params = mock_exec.await_args.args
    assert params == (42, 999, "Alice")


def test_rps_update_stat_signature_requires_guild_id():
    """``guild_id`` must NOT have a default value any more.

    Tomorrow's maintainer might add ``= 0`` back to ease typing.  This
    test makes that mistake visible at CI time.
    """
    sig = inspect.signature(rps.rps_update_stat)
    guild = sig.parameters["guild_id"]
    assert guild.default is inspect.Parameter.empty, (
        "rps_update_stat.guild_id must be required (no default).  "
        "Defaulting to 0 collapses every guild's stats at PK (user, 0)."
    )


def test_rps_get_leaderboard_signature_requires_guild_id():
    sig = inspect.signature(rps.rps_get_leaderboard)
    guild = sig.parameters["guild_id"]
    assert guild.default is inspect.Parameter.empty, (
        "rps_get_leaderboard.guild_id must be required (no default)."
    )


def test_rps_ensure_player_signature_requires_guild_id():
    sig = inspect.signature(rps.rps_ensure_player)
    guild = sig.parameters["guild_id"]
    assert guild.default is inspect.Parameter.empty, (
        "rps_ensure_player.guild_id must be required (no default)."
    )


def test_rps_source_has_no_fstring_sql_identifier():
    """The previous ``f"… SET {col}=… "`` pattern is forbidden.

    Whitelist-protected today, structurally unsafe; the AST regression
    test in PR R2 covers the whole codebase.  This narrower check
    catches the specific file the audit flagged.
    """
    import re

    src = inspect.getsource(rps)
    # Match an f-string with a ``{identifier}`` placeholder inside what
    # looks like an SQL statement.  The match arms in the new shape use
    # plain triple-quoted strings, not f-strings.
    pattern = re.compile(r'f"[^"]*\b(SET|FROM|INTO|JOIN)\b[^"]*\{', re.IGNORECASE)
    assert not pattern.search(src), (
        "rps.py contains an f-string with a braced identifier inside a "
        "SQL keyword context.  Replace with explicit match arms or "
        "parameterised queries."
    )
