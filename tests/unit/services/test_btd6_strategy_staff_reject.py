"""Blocker PR-1 — staff_reject mirrors reject() writes + adds guards.

These tests pin the new ``staff_reject`` chokepoint:

* It mirrors the historical ``reject`` write semantics
  (``approval_status='rejected'``, ``bump_version=True``,
  ``current_guild_id=None``; matching audit row).
* It enforces ``_is_staff`` permissions at the service layer
  (independent of the view's ``interaction_check``).
* It refuses missing strategies before any DB write.
"""

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


async def test_staff_reject_writes_state_and_audit(monkeypatch):
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

    result = await mut.staff_reject(7, staff_actor=_staff_actor(actor_id=42))
    assert result.action == "rejected"
    assert result.actor_kind == "staff"

    # Mirror the existing reject() write contract exactly.
    assert update_calls[0]["approval_status"] == "rejected"
    assert update_calls[0]["bump_version"] is True
    assert update_calls[0]["current_guild_id"] is None

    assert audit_calls[0]["actor_kind"] == "staff"
    assert audit_calls[0]["actor_id"] == 42
    assert audit_calls[0]["action"] == "rejected"


async def test_staff_reject_admin_is_also_staff(monkeypatch):
    async def _get(sid):
        return _strategy_row(sid=sid)

    monkeypatch.setattr(db, "get_strategy", _get)
    monkeypatch.setattr(db, "update_strategy_state", AsyncMock())
    monkeypatch.setattr(db, "record_strategy_audit", AsyncMock())

    result = await mut.staff_reject(7, staff_actor=_admin_actor(actor_id=99))
    assert result.actor_kind == "staff"
    assert result.action == "rejected"


async def test_staff_reject_rejects_non_staff(monkeypatch):
    """Service-layer authorization pin — independent of any view check."""

    async def _get(sid):
        return _strategy_row(sid=sid)

    explode = AsyncMock()
    monkeypatch.setattr(db, "get_strategy", _get)
    monkeypatch.setattr(db, "update_strategy_state", explode)
    monkeypatch.setattr(db, "record_strategy_audit", explode)

    with pytest.raises(mut.UnauthorizedStrategyMutationError):
        await mut.staff_reject(7, staff_actor=_non_staff_actor())
    explode.assert_not_awaited()


async def test_staff_reject_refuses_when_strategy_missing(monkeypatch):
    async def _get(sid):
        return None

    explode = AsyncMock()
    monkeypatch.setattr(db, "get_strategy", _get)
    monkeypatch.setattr(db, "update_strategy_state", explode)
    monkeypatch.setattr(db, "record_strategy_audit", explode)

    with pytest.raises(mut.InvalidStrategyValueError, match="strategy 7 not found"):
        await mut.staff_reject(7, staff_actor=_staff_actor())
    explode.assert_not_awaited()


def test_module_exports_staff_reject():
    """The new mutation is in __all__ so callers can import without
    relying on internal attribute access."""
    assert "staff_reject" in mut.__all__


async def test_staff_reject_matches_reject_state_writes(monkeypatch):
    """Both reject() and staff_reject() must converge on identical
    ``update_strategy_state`` kwargs — protects against silent drift
    if either path is later edited."""

    async def _get(sid):
        return _strategy_row(sid=sid)

    monkeypatch.setattr(db, "get_strategy", _get)

    staff_calls: list[dict] = []
    reject_calls: list[dict] = []

    async def _update_staff(strategy_id, **kw):
        staff_calls.append({"id": strategy_id, **kw})

    async def _audit_noop(*_a, **_kw):
        return None

    monkeypatch.setattr(db, "update_strategy_state", _update_staff)
    monkeypatch.setattr(db, "record_strategy_audit", _audit_noop)

    await mut.staff_reject(7, staff_actor=_staff_actor(actor_id=42))

    async def _update_reject(strategy_id, **kw):
        reject_calls.append({"id": strategy_id, **kw})

    monkeypatch.setattr(db, "update_strategy_state", _update_reject)
    await mut.reject(7, actor=_staff_actor(actor_id=42), actor_kind="staff")

    assert staff_calls and reject_calls
    assert staff_calls[0] == reject_calls[0]
