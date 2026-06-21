"""Tests for utils.db.role_menus — the role-menu data layer (migration 078).

Pins the two behaviours the higher layers rely on: ``create_menu`` returns the
DB-generated ``menu_id`` (via ``RETURNING``), and ``delete_for_guild`` reports
how many menus it removed (via ``RETURNING`` + count) so the guild-teardown
step can log it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.db import role_menus  # noqa: E402


@pytest.mark.asyncio
async def test_create_menu_returns_generated_id(monkeypatch):
    captured: dict[str, object] = {}

    async def _fetchone(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return {"menu_id": 7}

    monkeypatch.setattr(role_menus.pool, "fetchone", AsyncMock(side_effect=_fetchone))

    menu_id = await role_menus.create_menu(
        1,
        222,
        title="Pick",
        description=None,
        style="dropdown",
    )

    assert menu_id == 7
    assert "INSERT INTO role_menus" in captured["sql"]
    assert "RETURNING menu_id" in captured["sql"]
    # guild_id + channel_id lead the param tuple; style is carried through.
    assert captured["params"][0] == 1
    assert captured["params"][1] == 222
    assert "dropdown" in captured["params"]


@pytest.mark.asyncio
async def test_delete_for_guild_returns_count(monkeypatch):
    monkeypatch.setattr(
        role_menus.pool,
        "fetchall",
        AsyncMock(return_value=[{"menu_id": 1}, {"menu_id": 2}, {"menu_id": 3}]),
    )

    removed = await role_menus.delete_for_guild(1)

    assert removed == 3


@pytest.mark.asyncio
async def test_add_option_upserts(monkeypatch):
    captured: dict[str, str] = {}

    async def _execute(sql, params=()):
        captured["sql"] = sql

    monkeypatch.setattr(role_menus.pool, "execute", AsyncMock(side_effect=_execute))

    await role_menus.add_option(7, 42, emoji="🎮", label="Gamer", position=1)

    assert "INSERT INTO role_menu_options" in captured["sql"]
    assert "ON CONFLICT (menu_id, role_id)" in captured["sql"]


@pytest.mark.asyncio
async def test_get_options_orders_by_position(monkeypatch):
    captured: dict[str, str] = {}

    async def _fetchall(sql, params=()):
        captured["sql"] = sql
        return []

    monkeypatch.setattr(role_menus.pool, "fetchall", AsyncMock(side_effect=_fetchall))

    await role_menus.get_options(7)

    assert "ORDER BY position" in captured["sql"]
