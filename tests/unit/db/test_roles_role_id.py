"""Role-id groundwork for ``role_thresholds`` (server-management PR6, migration 056).

Pins the additive id-groundwork: migration 056 adds nullable ``role_id`` /
``display_name``; the setters persist them (``COALESCE``-preserved on conflict)
and stay backward-compatible for legacy name-only callers; the getters select
them so readers can resolve id-first.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from utils.db import roles

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "056_role_threshold_role_id.sql"
)


def test_migration_056_adds_nullable_role_id_columns():
    sql = _MIGRATION.read_text()
    assert "ALTER TABLE role_thresholds" in sql
    assert "ADD COLUMN IF NOT EXISTS role_id BIGINT" in sql
    assert "ADD COLUMN IF NOT EXISTS display_name TEXT" in sql
    # additive-only: the executable statement must not drop anything.
    statement = sql.split("Forward-only")[-1]
    assert "DROP" not in statement


@pytest.fixture
def exec_calls(monkeypatch):
    calls: list[tuple[str, tuple]] = []

    async def fake_execute(sql, params):
        calls.append((sql, params))

    monkeypatch.setattr(roles.pool, "execute", fake_execute)
    return calls


@pytest.fixture
def fetch_calls(monkeypatch):
    calls: list[tuple[str, tuple]] = []

    async def fake_fetchall(sql, params):
        calls.append((sql, params))
        return []

    monkeypatch.setattr(roles.pool, "fetchall", fake_fetchall)
    return calls


@pytest.mark.asyncio
async def test_set_role_threshold_persists_role_id_and_display_name(exec_calls):
    await roles.set_role_threshold(7, "Veteran", 30, role_id=123, display_name="Veteran")
    sql, params = exec_calls[0]
    assert "role_id" in sql and "display_name" in sql
    # captured id is preserved on conflict, never wiped by a later update.
    assert "COALESCE(EXCLUDED.role_id" in sql
    assert params == (7, "Veteran", 30, 123, "Veteran")


@pytest.mark.asyncio
async def test_set_role_threshold_backward_compatible_without_ids(exec_calls):
    await roles.set_role_threshold(7, "Veteran", 30)
    _, params = exec_calls[0]
    assert params == (7, "Veteran", 30, None, None)


@pytest.mark.asyncio
async def test_set_role_xp_threshold_persists_ids_and_coalesces(exec_calls):
    await roles.set_role_xp_threshold(
        7, "Veteran", 5, True, role_id=123, display_name="Veteran"
    )
    sql, params = exec_calls[0]
    assert "role_id" in sql and "COALESCE(EXCLUDED.role_id" in sql
    assert params == (7, "Veteran", 5, True, 123, "Veteran")


@pytest.mark.asyncio
async def test_set_role_xp_threshold_backward_compatible_without_ids(exec_calls):
    await roles.set_role_xp_threshold(7, "Veteran", 5, True)
    _, params = exec_calls[0]
    assert params == (7, "Veteran", 5, True, None, None)


@pytest.mark.asyncio
async def test_getters_select_role_id_and_display_name(fetch_calls):
    await roles.get_role_thresholds(7)
    await roles.get_xp_threshold_roles(7)
    assert fetch_calls, "expected fetchall to be called"
    for sql, _ in fetch_calls:
        assert "role_id" in sql and "display_name" in sql
