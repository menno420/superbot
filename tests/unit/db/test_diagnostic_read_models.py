"""RS08 read models — the diagnostic aggregates extracted from the cogs.

The embed builders in ``cogs/diagnostic/`` used to own these queries
inline; they now live with their tables' owning ``utils/db`` modules
(``test_no_raw_sql_in_cogs.py`` fences the class). Mock-level pins:
shape + filter behaviour, not SQL text.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import anchors, migrations, sessions


def _pool_with_fetch(rows: list[dict]) -> MagicMock:
    fake = MagicMock()
    fake.fetch = AsyncMock(return_value=rows)
    return fake


@pytest.mark.asyncio
async def test_count_sessions_by_subsystem_all():
    rows = [{"subsystem": "setup", "n": 3}, {"subsystem": "mining", "n": 1}]
    fake = _pool_with_fetch(rows)
    with patch("utils.db.sessions.pool.get", return_value=fake):
        out = await sessions.count_sessions_by_subsystem()

    assert out == rows
    query = fake.fetch.await_args.args[0]
    assert "GROUP BY subsystem" in query and "WHERE" not in query


@pytest.mark.asyncio
async def test_count_sessions_by_subsystem_filtered():
    fake = _pool_with_fetch([{"subsystem": "setup", "n": 3}])
    with patch("utils.db.sessions.pool.get", return_value=fake):
        out = await sessions.count_sessions_by_subsystem("setup")

    assert out == [{"subsystem": "setup", "n": 3}]
    args = fake.fetch.await_args.args
    assert "WHERE subsystem = $1" in args[0] and args[1] == "setup"


@pytest.mark.asyncio
async def test_count_active_anchors_by_subsystem_excludes_stale():
    fake = _pool_with_fetch([{"subsystem": "economy", "n": 2}])
    with patch("utils.db.anchors.pool.get", return_value=fake):
        out = await anchors.count_active_anchors_by_subsystem()

    assert out == [{"subsystem": "economy", "n": 2}]
    assert "NOT is_stale" in fake.fetch.await_args.args[0]


@pytest.mark.asyncio
async def test_applied_migration_versions_returns_set():
    with patch(
        "utils.db.migrations.pool.fetchall",
        AsyncMock(return_value=[{"version": 1}, {"version": 52}]),
    ):
        assert await migrations.applied_migration_versions() == {1, 52}


@pytest.mark.asyncio
async def test_list_public_tables_returns_set():
    with patch(
        "utils.db.migrations.pool.fetchall",
        AsyncMock(return_value=[{"tablename": "xp"}, {"tablename": "economy"}]),
    ):
        assert await migrations.list_public_tables() == {"economy", "xp"}
