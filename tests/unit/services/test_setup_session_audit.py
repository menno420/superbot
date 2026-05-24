"""Pins audit.action_recorded emission for setup session lifecycle transitions.

Covers:
* start_session emits "setup.session.started" with actor_id=owner_id.
* mark_complete emits "setup.session.completed" with actor_type="system".
* dismiss emits "setup.session.dismissed" with actor_type="system".
* Audit emission failure never propagates — the DB transition completes normally.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db_row(guild_id: int = 1111, status: str = "pending") -> dict:
    return {
        "guild_id": guild_id,
        "guild_name": "Test Guild",
        "owner_id": 9999,
        "setup_status": status,
        "setup_channel_id": None,
        "setup_message_id": None,
        "last_readiness_score": None,
        "current_step": None,
        "delegated_admins": [],
        "skipped_sections": [],
        "depth": None,
    }


# ---------------------------------------------------------------------------
# start_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_session_emits_audit():
    row = _make_db_row()
    with (
        patch("utils.db.setup_session.upsert", new_callable=AsyncMock),
        patch("utils.db.setup_session.get", new_callable=AsyncMock, return_value=row),
        patch(
            "services.audit_events.emit_audit_action", new_callable=AsyncMock
        ) as mock_emit,
    ):
        from services.setup_session import start_session

        await start_session(
            guild_id=1111,
            guild_name="Test Guild",
            owner_id=9999,
        )

    mock_emit.assert_awaited_once()
    kwargs = mock_emit.await_args.kwargs
    assert kwargs["mutation_type"] == "setup.session.started"
    assert kwargs["subsystem"] == "setup"
    assert kwargs["guild_id"] == 1111
    assert kwargs["new_value"] == "pending"
    assert kwargs["actor_id"] == 9999
    assert kwargs["actor_type"] == "user"
    assert kwargs["target"] == "setup_session:1111"
    assert kwargs["scope"] == "guild"


# ---------------------------------------------------------------------------
# mark_complete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_complete_emits_audit():
    with (
        patch("utils.db.setup_session.set_status", new_callable=AsyncMock),
        patch("utils.db.setup_session.set_step", new_callable=AsyncMock),
        patch(
            "utils.db.setup_session.clear_skipped_sections", new_callable=AsyncMock
        ),
        patch("services.setup_draft.clear", new_callable=AsyncMock),
        patch(
            "services.audit_events.emit_audit_action", new_callable=AsyncMock
        ) as mock_emit,
    ):
        from services.setup_session import mark_complete

        await mark_complete(guild_id=2222)

    mock_emit.assert_awaited_once()
    kwargs = mock_emit.await_args.kwargs
    assert kwargs["mutation_type"] == "setup.session.completed"
    assert kwargs["guild_id"] == 2222
    assert kwargs["new_value"] == "complete"
    assert kwargs["actor_id"] is None
    assert kwargs["actor_type"] == "system"


# ---------------------------------------------------------------------------
# dismiss
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dismiss_emits_audit():
    with (
        patch("utils.db.setup_session.set_status", new_callable=AsyncMock),
        patch("utils.db.setup_session.set_step", new_callable=AsyncMock),
        patch(
            "utils.db.setup_session.clear_skipped_sections", new_callable=AsyncMock
        ),
        patch("services.setup_draft.clear", new_callable=AsyncMock),
        patch(
            "services.audit_events.emit_audit_action", new_callable=AsyncMock
        ) as mock_emit,
    ):
        from services.setup_session import dismiss

        await dismiss(guild_id=3333)

    mock_emit.assert_awaited_once()
    kwargs = mock_emit.await_args.kwargs
    assert kwargs["mutation_type"] == "setup.session.dismissed"
    assert kwargs["guild_id"] == 3333
    assert kwargs["new_value"] == "dismissed"
    assert kwargs["actor_id"] is None
    assert kwargs["actor_type"] == "system"


# ---------------------------------------------------------------------------
# Failure isolation — audit failure must never propagate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_session_audit_failure_does_not_raise():
    row = _make_db_row()
    with (
        patch("utils.db.setup_session.upsert", new_callable=AsyncMock),
        patch("utils.db.setup_session.get", new_callable=AsyncMock, return_value=row),
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
            side_effect=RuntimeError("bus down"),
        ),
    ):
        from services.setup_session import start_session

        session = await start_session(
            guild_id=1111,
            guild_name="Test Guild",
            owner_id=9999,
        )

    assert session is not None
    assert session.guild_id == 1111


@pytest.mark.asyncio
async def test_mark_complete_audit_failure_does_not_raise():
    with (
        patch("utils.db.setup_session.set_status", new_callable=AsyncMock),
        patch("utils.db.setup_session.set_step", new_callable=AsyncMock),
        patch(
            "utils.db.setup_session.clear_skipped_sections", new_callable=AsyncMock
        ),
        patch("services.setup_draft.clear", new_callable=AsyncMock),
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
            side_effect=RuntimeError("bus down"),
        ),
    ):
        from services.setup_session import mark_complete

        await mark_complete(guild_id=2222)  # must not raise


@pytest.mark.asyncio
async def test_dismiss_audit_failure_does_not_raise():
    with (
        patch("utils.db.setup_session.set_status", new_callable=AsyncMock),
        patch("utils.db.setup_session.set_step", new_callable=AsyncMock),
        patch(
            "utils.db.setup_session.clear_skipped_sections", new_callable=AsyncMock
        ),
        patch("services.setup_draft.clear", new_callable=AsyncMock),
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
            side_effect=RuntimeError("bus down"),
        ),
    ):
        from services.setup_session import dismiss

        await dismiss(guild_id=3333)  # must not raise


# ---------------------------------------------------------------------------
# Audit payload contract — occurred_at is a datetime (not a string or None)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_session_audit_occurred_at_is_datetime():
    from datetime import datetime

    row = _make_db_row()
    with (
        patch("utils.db.setup_session.upsert", new_callable=AsyncMock),
        patch("utils.db.setup_session.get", new_callable=AsyncMock, return_value=row),
        patch(
            "services.audit_events.emit_audit_action", new_callable=AsyncMock
        ) as mock_emit,
    ):
        from services.setup_session import start_session

        await start_session(guild_id=1111, guild_name="G", owner_id=9999)

    kwargs = mock_emit.await_args.kwargs
    assert isinstance(kwargs["occurred_at"], datetime)
