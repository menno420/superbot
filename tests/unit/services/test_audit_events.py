"""Phase 9c.2 — shared ``audit.action_recorded`` publisher.

Pins the 11-field payload contract that
:mod:`services.server_logging`'s ``_on_audit_action`` subscriber relies
on, and pins the failure-safe behaviour (a raising event bus must not
propagate; pipelines have already committed their DB state).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services.audit_events import EVT_AUDIT_ACTION_RECORDED, emit_audit_action

PAYLOAD_FIELDS = (
    "mutation_id",
    "subsystem",
    "mutation_type",
    "target",
    "scope",
    "guild_id",
    "prev_value",
    "new_value",
    "actor_id",
    "actor_type",
    "occurred_at",
)


def _sample_kwargs():
    return dict(
        mutation_id="00000000-0000-4000-8000-000000000001",
        subsystem="logging",
        mutation_type="set_flag_state",
        target="flag:bindings.primary",
        scope="global",
        guild_id=None,
        prev_value="off",
        new_value="canary",
        actor_id=99,
        actor_type="platform_owner",
        occurred_at=datetime(2026, 5, 20, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_emit_audit_action_emits_under_canonical_topic():
    with patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit:
        ok = await emit_audit_action(**_sample_kwargs())
    assert ok is True
    mock_emit.assert_awaited_once()
    topic = mock_emit.await_args.args[0]
    assert topic == EVT_AUDIT_ACTION_RECORDED == "audit.action_recorded"


@pytest.mark.asyncio
async def test_emit_audit_action_payload_has_all_eleven_fields():
    with patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit:
        await emit_audit_action(**_sample_kwargs())
    payload = mock_emit.await_args.kwargs
    for field in PAYLOAD_FIELDS:
        assert field in payload, f"missing {field}"
    assert set(payload.keys()) == set(
        PAYLOAD_FIELDS
    ), f"unexpected extra fields: {set(payload.keys()) - set(PAYLOAD_FIELDS)}"


@pytest.mark.asyncio
async def test_emit_audit_action_payload_values_match_inputs():
    kwargs = _sample_kwargs()
    with patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit:
        await emit_audit_action(**kwargs)
    payload = mock_emit.await_args.kwargs
    assert payload["mutation_id"] == kwargs["mutation_id"]
    assert payload["subsystem"] == kwargs["subsystem"]
    assert payload["mutation_type"] == kwargs["mutation_type"]
    assert payload["target"] == kwargs["target"]
    assert payload["scope"] == kwargs["scope"]
    assert payload["guild_id"] == kwargs["guild_id"]
    assert payload["prev_value"] == kwargs["prev_value"]
    assert payload["new_value"] == kwargs["new_value"]
    assert payload["actor_id"] == kwargs["actor_id"]
    assert payload["actor_type"] == kwargs["actor_type"]
    # datetime is serialised via .isoformat() so the wire format stays
    # JSON-friendly.
    assert payload["occurred_at"] == kwargs["occurred_at"].isoformat()


@pytest.mark.asyncio
async def test_emit_audit_action_accepts_none_for_optional_fields():
    kwargs = _sample_kwargs()
    kwargs.update(
        guild_id=None,
        prev_value=None,
        new_value=None,
        actor_id=None,
    )
    with patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit:
        ok = await emit_audit_action(**kwargs)
    assert ok is True
    payload = mock_emit.await_args.kwargs
    assert payload["guild_id"] is None
    assert payload["prev_value"] is None
    assert payload["new_value"] is None
    assert payload["actor_id"] is None


@pytest.mark.asyncio
async def test_emit_audit_action_swallows_bus_exceptions(caplog):
    with patch(
        "core.events.bus.emit",
        new_callable=AsyncMock,
        side_effect=RuntimeError("bus down"),
    ):
        with caplog.at_level("ERROR", logger="bot.services.audit_events"):
            ok = await emit_audit_action(**_sample_kwargs())
    assert ok is False
    # The exception is logged with exc_info so the traceback is
    # captured by caplog records.
    assert any(
        "audit.action_recorded emission failed" in record.getMessage()
        for record in caplog.records
    )


def test_audit_events_module_has_no_db_imports():
    """Pin: the shared publisher must not pull in DB code.

    Pipelines own DB writes; this helper exists strictly to push the
    canonical companion event onto the bus.
    """
    import services.audit_events as mod

    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    # The module's only runtime dependency outside stdlib is
    # ``core.events.bus``, which is imported lazily inside the
    # function. A top-level ``import utils.db`` / ``from utils.db``
    # would mean the helper has acquired hidden DB coupling.
    assert "utils.db" not in text
    assert "asyncpg" not in text


def test_audit_events_module_has_no_discord_imports():
    """Pin: the helper must be pure (no discord coupling)."""
    import services.audit_events as mod

    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    assert "import discord" not in text
    assert "from discord" not in text
