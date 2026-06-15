"""PR5 — staff_approve_guild keeps strategies guild-local + audits."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_strategy_mutation as mut  # noqa: E402
from utils.db import btd6_strategies as db  # noqa: E402


def _staff_actor(actor_id: int = 12345) -> MagicMock:
    actor = MagicMock()
    actor.id = actor_id
    actor.guild_permissions.administrator = False
    actor.guild_permissions.manage_guild = True
    return actor


def _admin_actor(actor_id: int = 12345) -> MagicMock:
    actor = MagicMock()
    actor.id = actor_id
    actor.guild_permissions.administrator = True
    return actor


def _non_staff_actor(actor_id: int = 99) -> MagicMock:
    actor = MagicMock()
    actor.id = actor_id
    actor.guild_permissions.administrator = False
    actor.guild_permissions.manage_guild = False
    return actor


def _strategy_row(
    *,
    sid: int = 1,
    visibility: str = "guild",
    approval_status: str = "draft",
) -> dict:
    return {
        "id": sid,
        "title": "test",
        "summary": "s",
        "origin_guild_id": 100,
        "current_guild_id": 100,
        "visibility": visibility,
        "approval_status": approval_status,
        "version": 1,
    }


async def test_staff_approve_guild_writes_state_and_audit(monkeypatch):
    update_calls: list[dict] = []
    audit_calls: list[dict] = []

    async def _get(sid):
        return _strategy_row(sid=sid)

    async def _update(strategy_id, **kw):
        update_calls.append({"id": strategy_id, **kw})

    async def _audit(strategy_id, **kw):
        audit_calls.append({"id": strategy_id, **kw})

    monkeypatch.setattr(db, "get_strategy", _get)
    monkeypatch.setattr(db, "update_strategy_state", _update)
    monkeypatch.setattr(db, "record_strategy_audit", _audit)

    result = await mut.staff_approve_guild(
        7,
        staff_actor=_staff_actor(actor_id=42),
    )
    assert result.action == "staff_approved_guild"
    assert result.actor_kind == "staff"

    # State update must promote to approved at GUILD visibility (NOT
    # published) — that's the entire point of this mutation.
    assert update_calls[0]["approval_status"] == "approved"
    assert update_calls[0]["visibility"] == "guild"
    assert update_calls[0]["approved_by"] == "staff"
    assert update_calls[0]["approved_by_id"] == 42
    assert update_calls[0]["bump_version"] is True

    # Audit row recorded with the staff actor.
    assert audit_calls[0]["actor_kind"] == "staff"
    assert audit_calls[0]["actor_id"] == 42
    assert audit_calls[0]["action"] == "staff_approved_guild"


async def test_staff_approve_guild_admin_is_also_staff(monkeypatch):
    async def _get(sid):
        return _strategy_row(sid=sid)

    monkeypatch.setattr(db, "get_strategy", _get)
    monkeypatch.setattr(db, "update_strategy_state", AsyncMock())
    monkeypatch.setattr(db, "record_strategy_audit", AsyncMock())
    result = await mut.staff_approve_guild(
        7,
        staff_actor=_admin_actor(actor_id=99),
    )
    assert result.actor_kind == "staff"


async def test_staff_approve_guild_rejects_non_staff(monkeypatch):
    async def _get(sid):
        return _strategy_row(sid=sid)

    # The mutation must refuse before any DB write fires.
    explode = AsyncMock()
    monkeypatch.setattr(db, "get_strategy", _get)
    monkeypatch.setattr(db, "update_strategy_state", explode)
    monkeypatch.setattr(db, "record_strategy_audit", explode)
    with pytest.raises(mut.UnauthorizedStrategyMutationError):
        await mut.staff_approve_guild(7, staff_actor=_non_staff_actor())
    explode.assert_not_awaited()


async def test_staff_approve_guild_refuses_when_already_published(monkeypatch):
    async def _get(sid):
        return _strategy_row(
            sid=sid, visibility="published", approval_status="approved"
        )

    explode = AsyncMock()
    monkeypatch.setattr(db, "get_strategy", _get)
    monkeypatch.setattr(db, "update_strategy_state", explode)
    monkeypatch.setattr(db, "record_strategy_audit", explode)
    with pytest.raises(mut.InvalidStrategyValueError, match="already published"):
        await mut.staff_approve_guild(7, staff_actor=_staff_actor())
    explode.assert_not_awaited()


async def test_staff_approve_guild_refuses_when_strategy_missing(monkeypatch):
    async def _get(sid):
        return None

    explode = AsyncMock()
    monkeypatch.setattr(db, "get_strategy", _get)
    monkeypatch.setattr(db, "update_strategy_state", explode)
    monkeypatch.setattr(db, "record_strategy_audit", explode)
    with pytest.raises(mut.InvalidStrategyValueError, match="strategy 7 not found"):
        await mut.staff_approve_guild(7, staff_actor=_staff_actor())
    explode.assert_not_awaited()


def test_module_exports_staff_approve_guild():
    """The new mutation is in __all__ so callers can import without
    relying on internal attribute access."""
    assert "staff_approve_guild" in mut.__all__
