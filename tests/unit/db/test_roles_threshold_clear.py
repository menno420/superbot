"""Field-specific role-threshold clears (server-management PR5).

Pins the non-destructive contract that replaces the full-row
``remove_role_threshold`` for the time/XP removal surfaces: clearing one tier
must touch only its own columns and may delete the row **only** when no
automation field remains.  The previous full-row DELETE wiped both tiers (see
``role_cog.unsetrole`` / ``time_roles_panel`` comments); these must not.
"""

from __future__ import annotations

import pytest

from utils.db import roles


@pytest.fixture
def captured(monkeypatch):
    calls: list[tuple[str, tuple]] = []

    async def fake_execute(sql, params):
        calls.append((sql, params))

    monkeypatch.setattr(roles.pool, "execute", fake_execute)
    return calls


@pytest.mark.asyncio
async def test_clear_time_touches_only_days_then_guards_delete_on_no_xp(captured):
    await roles.clear_role_time_threshold(7, "Veteran")
    assert len(captured) == 2
    update_sql, update_params = captured[0]
    delete_sql, delete_params = captured[1]

    # 1) UPDATE clears ONLY days_required — never the XP columns.
    assert "UPDATE role_thresholds SET days_required=0" in update_sql
    assert "level_required" not in update_sql
    assert "xp_auto_assign" not in update_sql
    assert update_params == (7, "Veteran")

    # 2) DELETE removes the row only when no XP config remains.
    assert "DELETE FROM role_thresholds" in delete_sql
    assert "days_required=0" in delete_sql
    assert "level_required IS NULL" in delete_sql
    assert delete_params == (7, "Veteran")


@pytest.mark.asyncio
async def test_clear_xp_touches_only_xp_then_guards_delete_on_no_time(captured):
    await roles.clear_role_xp_threshold(7, "Veteran")
    assert len(captured) == 2
    update_sql, update_params = captured[0]
    delete_sql, delete_params = captured[1]

    # 1) UPDATE clears ONLY the XP columns — never days_required.
    set_clause = update_sql.split("WHERE")[0]
    assert "level_required=NULL" in update_sql
    assert "xp_auto_assign=FALSE" in update_sql
    assert "days_required" not in set_clause
    assert update_params == (7, "Veteran")

    # 2) DELETE removes the row only when no time tier remains.
    assert "DELETE FROM role_thresholds" in delete_sql
    assert "days_required=0" in delete_sql
    assert "level_required IS NULL" in delete_sql
    assert delete_params == (7, "Veteran")
