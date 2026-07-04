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
async def test_create_menu_persists_card_columns(monkeypatch):
    """The banner-card columns (migration 085) flow into the INSERT params."""
    captured: dict[str, object] = {}

    async def _fetchone(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return {"menu_id": 9}

    monkeypatch.setattr(role_menus.pool, "fetchone", AsyncMock(side_effect=_fetchone))

    await role_menus.create_menu(
        1,
        2,
        title="Pick",
        description=None,
        card_template="banner",
        card_text="Choose below",
    )

    assert "card_template" in captured["sql"]
    assert "card_text" in captured["sql"]
    assert "banner" in captured["params"]
    assert "Choose below" in captured["params"]


@pytest.mark.asyncio
async def test_update_menu_persists_card_columns(monkeypatch):
    captured: dict[str, object] = {}

    async def _execute(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params

    monkeypatch.setattr(role_menus.pool, "execute", AsyncMock(side_effect=_execute))

    await role_menus.update_menu(
        9,
        title="Pick",
        description=None,
        style="dropdown",
        mode="normal",
        max_roles=0,
        theme="default",
        card_template="gradient",
        card_text=None,
    )

    assert "card_template=$8" in captured["sql"]
    assert "card_text=$9" in captured["sql"]
    assert "gradient" in captured["params"]


@pytest.mark.asyncio
async def test_create_menu_persists_show_counts(monkeypatch):
    """The sign-up-counter flag (migration 102) flows into the INSERT params."""
    captured: dict[str, object] = {}

    async def _fetchone(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return {"menu_id": 11}

    monkeypatch.setattr(role_menus.pool, "fetchone", AsyncMock(side_effect=_fetchone))

    await role_menus.create_menu(
        1,
        2,
        title="Pick",
        description=None,
        show_counts=True,
    )

    assert "show_counts" in captured["sql"]
    assert True in captured["params"]


@pytest.mark.asyncio
async def test_update_menu_persists_show_counts(monkeypatch):
    captured: dict[str, object] = {}

    async def _execute(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params

    monkeypatch.setattr(role_menus.pool, "execute", AsyncMock(side_effect=_execute))

    await role_menus.update_menu(
        9,
        title="Pick",
        description=None,
        style="dropdown",
        mode="normal",
        max_roles=0,
        theme="default",
        show_counts=True,
    )

    assert "show_counts=$10" in captured["sql"]
    assert True in captured["params"]


@pytest.mark.asyncio
async def test_add_option_upserts(monkeypatch):
    captured: dict[str, str] = {}

    async def _execute(sql, params=()):
        captured["sql"] = sql

    monkeypatch.setattr(role_menus.pool, "execute", AsyncMock(side_effect=_execute))

    await role_menus.add_option(7, 42, emoji="🎮", label="Gamer", position=1)

    assert "INSERT INTO role_menu_options" in captured["sql"]
    assert "ON CONFLICT (menu_id, role_id)" in captured["sql"]


# ---------------------------------------------------------------------------
# Pickup analytics (PR 5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_pickup_upserts_increment(monkeypatch):
    captured: dict[str, object] = {}

    async def _execute(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params

    monkeypatch.setattr(role_menus.pool, "execute", AsyncMock(side_effect=_execute))

    await role_menus.record_pickup(1, 42)

    assert "INSERT INTO role_menu_pickup_stats" in captured["sql"]
    assert "picked = role_menu_pickup_stats.picked + 1" in captured["sql"]
    assert captured["params"] == (1, 42)


@pytest.mark.asyncio
async def test_record_removal_upserts_increment(monkeypatch):
    captured: dict[str, str] = {}

    async def _execute(sql, params=()):
        captured["sql"] = sql

    monkeypatch.setattr(role_menus.pool, "execute", AsyncMock(side_effect=_execute))

    await role_menus.record_removal(1, 42)

    assert "removed = role_menu_pickup_stats.removed + 1" in captured["sql"]


@pytest.mark.asyncio
async def test_get_pickup_stats_orders_by_picked(monkeypatch):
    captured: dict[str, str] = {}

    async def _fetchall(sql, params=()):
        captured["sql"] = sql
        return [{"role_id": 42, "picked": 9, "removed": 1, "last_picked_at": None}]

    monkeypatch.setattr(role_menus.pool, "fetchall", AsyncMock(side_effect=_fetchall))

    rows = await role_menus.get_pickup_stats(1)

    assert rows[0]["picked"] == 9
    assert "ORDER BY picked DESC" in captured["sql"]


@pytest.mark.asyncio
async def test_delete_pickup_stats_returns_count(monkeypatch):
    monkeypatch.setattr(
        role_menus.pool,
        "fetchall",
        AsyncMock(return_value=[{"role_id": 1}, {"role_id": 2}]),
    )

    assert await role_menus.delete_pickup_stats_for_guild(1) == 2


@pytest.mark.asyncio
async def test_get_options_orders_by_position(monkeypatch):
    captured: dict[str, str] = {}

    async def _fetchall(sql, params=()):
        captured["sql"] = sql
        return []

    monkeypatch.setattr(role_menus.pool, "fetchall", AsyncMock(side_effect=_fetchall))

    await role_menus.get_options(7)

    assert "ORDER BY position" in captured["sql"]
