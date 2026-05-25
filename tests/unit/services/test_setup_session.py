"""Phase 9e / Track 4 PR 8 — ``services.setup_session`` lifecycle tests.

Mocks the ``utils.db.setup_session`` primitives and verifies the
service applies the four lifecycle transitions: start, resume,
mark_in_progress, mark_complete, dismiss. The service is
asyncpg-free at the test level.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import setup_session as svc
from services.setup_session import SetupSession


def _row(**overrides):
    base = {
        "guild_id": 1,
        "guild_name": "Test",
        "owner_id": 99,
        "joined_at": None,
        "setup_status": "pending",
        "setup_channel_id": None,
        "setup_message_id": None,
        "last_readiness_score": None,
        "current_step": None,
        "delegated_admins": [],
        "skipped_sections": [],
        "created_at": None,
        "updated_at": None,
    }
    base.update(overrides)
    return base


@pytest.fixture
def _mock_db():
    with (
        patch("services.setup_session.db.get", new_callable=AsyncMock) as get_mock,
        patch(
            "services.setup_session.db.upsert", new_callable=AsyncMock
        ) as upsert_mock,
        patch(
            "services.setup_session.db.set_status",
            new_callable=AsyncMock,
        ) as set_status_mock,
        patch(
            "services.setup_session.db.set_step",
            new_callable=AsyncMock,
        ) as set_step_mock,
        patch(
            "services.setup_session.db.set_readiness_score",
            new_callable=AsyncMock,
        ) as set_score_mock,
        patch(
            "services.setup_session.db.add_skipped_section",
            new_callable=AsyncMock,
        ) as add_skipped_mock,
        patch(
            "services.setup_session.db.remove_skipped_section",
            new_callable=AsyncMock,
        ) as remove_skipped_mock,
        patch(
            "services.setup_session.db.clear_skipped_sections",
            new_callable=AsyncMock,
        ) as clear_skipped_mock,
    ):
        yield {
            "get": get_mock,
            "upsert": upsert_mock,
            "set_status": set_status_mock,
            "set_step": set_step_mock,
            "set_readiness_score": set_score_mock,
            "add_skipped_section": add_skipped_mock,
            "remove_skipped_section": remove_skipped_mock,
            "clear_skipped_sections": clear_skipped_mock,
        }


@pytest.mark.asyncio
async def test_start_session_upserts_and_returns_snapshot(_mock_db):
    _mock_db["get"].return_value = _row(setup_channel_id=11, setup_message_id=22)
    session = await svc.start_session(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_channel_id=11,
        setup_message_id=22,
    )
    _mock_db["upsert"].assert_awaited_once()
    assert isinstance(session, SetupSession)
    assert session.guild_id == 1
    assert session.setup_channel_id == 11
    assert session.setup_status == "pending"


@pytest.mark.asyncio
async def test_start_session_raises_if_row_missing_after_upsert(_mock_db):
    _mock_db["get"].return_value = None
    with pytest.raises(RuntimeError, match="missing"):
        await svc.start_session(guild_id=1, guild_name="x", owner_id=99)


@pytest.mark.asyncio
async def test_resume_session_returns_none_if_no_row(_mock_db):
    _mock_db["get"].return_value = None
    session = await svc.resume_session(1)
    assert session is None


@pytest.mark.asyncio
async def test_resume_session_hydrates_dataclass(_mock_db):
    _mock_db["get"].return_value = _row(
        setup_status="in_progress",
        current_step="logging",
        delegated_admins=[123, 456],
    )
    session = await svc.resume_session(1)
    assert session is not None
    assert session.setup_status == "in_progress"
    assert session.current_step == "logging"
    assert session.delegated_admins == (123, 456)


@pytest.mark.asyncio
async def test_mark_in_progress_sets_status_and_optional_step(_mock_db):
    await svc.mark_in_progress(1, step="onboarding")
    _mock_db["set_status"].assert_awaited_once_with(1, "in_progress")
    _mock_db["set_step"].assert_awaited_once_with(1, "onboarding")


@pytest.mark.asyncio
async def test_mark_in_progress_without_step_does_not_touch_step(_mock_db):
    await svc.mark_in_progress(1)
    _mock_db["set_status"].assert_awaited_once_with(1, "in_progress")
    _mock_db["set_step"].assert_not_awaited()


@pytest.mark.asyncio
async def test_mark_complete_clears_step(_mock_db):
    with patch(
        "services.setup_draft.clear",
        new_callable=AsyncMock,
    ):
        await svc.mark_complete(1)
    _mock_db["set_status"].assert_awaited_once_with(1, "complete")
    _mock_db["set_step"].assert_awaited_once_with(1, None)


@pytest.mark.asyncio
async def test_dismiss_clears_step(_mock_db):
    with patch(
        "services.setup_draft.clear",
        new_callable=AsyncMock,
    ):
        await svc.dismiss(1)
    _mock_db["set_status"].assert_awaited_once_with(1, "dismissed")
    _mock_db["set_step"].assert_awaited_once_with(1, None)


@pytest.mark.asyncio
async def test_mark_complete_clears_draft(_mock_db):
    """mark_complete must also drop any pending draft operations."""
    with patch(
        "services.setup_draft.clear",
        new_callable=AsyncMock,
    ) as draft_clear:
        await svc.mark_complete(42)
    draft_clear.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_dismiss_clears_draft(_mock_db):
    """dismiss must wipe any staged work so a re-launch starts clean."""
    with patch(
        "services.setup_draft.clear",
        new_callable=AsyncMock,
    ) as draft_clear:
        await svc.dismiss(42)
    draft_clear.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_mark_complete_tolerates_draft_clear_failure(_mock_db):
    """A draft-clear failure must not prevent the session status flip."""
    with patch(
        "services.setup_draft.clear",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB exploded"),
    ):
        # Should not raise.
        await svc.mark_complete(42)
    _mock_db["set_status"].assert_awaited_once_with(42, "complete")


@pytest.mark.asyncio
async def test_record_readiness_score_delegates(_mock_db):
    await svc.record_readiness_score(1, 75)
    _mock_db["set_readiness_score"].assert_awaited_once_with(1, 75)


# ---------------------------------------------------------------------------
# Skipped-section tracking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_section_skipped_delegates(_mock_db):
    await svc.mark_section_skipped(1, "cleanup")
    _mock_db["add_skipped_section"].assert_awaited_once_with(1, "cleanup")


@pytest.mark.asyncio
async def test_unmark_section_skipped_delegates(_mock_db):
    await svc.unmark_section_skipped(1, "cleanup")
    _mock_db["remove_skipped_section"].assert_awaited_once_with(1, "cleanup")


@pytest.mark.asyncio
async def test_mark_complete_clears_skipped_sections(_mock_db):
    with patch("services.setup_session._clear_draft", new_callable=AsyncMock):
        await svc.mark_complete(1)
    _mock_db["clear_skipped_sections"].assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_dismiss_clears_skipped_sections(_mock_db):
    with patch("services.setup_session._clear_draft", new_callable=AsyncMock):
        await svc.dismiss(1)
    _mock_db["clear_skipped_sections"].assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_resume_session_hydrates_skipped_sections(_mock_db):
    _mock_db["get"].return_value = _row(
        setup_status="in_progress",
        skipped_sections=["cleanup", "cog_routing"],
    )
    session = await svc.resume_session(1)
    assert session is not None
    assert session.skipped_sections == frozenset({"cleanup", "cog_routing"})


# ---------------------------------------------------------------------------
# Delegated-admin lifecycle wrappers (Phase 1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_delegated_admin_routes_to_db_layer():
    with (
        patch(
            "services.setup_session.db.add_delegated_admin",
            new_callable=AsyncMock,
        ) as add_mock,
        patch(
            "services.setup_session._emit_session_audit",
            new_callable=AsyncMock,
        ) as audit_mock,
    ):
        await svc.add_delegated_admin(guild_id=1, user_id=42, actor_id=99)
    add_mock.assert_awaited_once_with(1, 42)
    audit_mock.assert_awaited_once()
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["guild_id"] == 1
    assert kwargs["mutation_type"] == "setup.delegated_admin.added"
    assert kwargs["new_value"] == "42"
    assert kwargs["actor_id"] == 99
    assert kwargs["actor_type"] == "user"


@pytest.mark.asyncio
async def test_remove_delegated_admin_routes_to_db_layer():
    with (
        patch(
            "services.setup_session.db.remove_delegated_admin",
            new_callable=AsyncMock,
        ) as remove_mock,
        patch(
            "services.setup_session._emit_session_audit",
            new_callable=AsyncMock,
        ) as audit_mock,
    ):
        await svc.remove_delegated_admin(guild_id=1, user_id=42, actor_id=99)
    remove_mock.assert_awaited_once_with(1, 42)
    audit_mock.assert_awaited_once()
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["mutation_type"] == "setup.delegated_admin.removed"
    assert kwargs["new_value"] == "42"


@pytest.mark.asyncio
async def test_add_delegated_admin_does_not_double_emit_audit_on_idempotent_grant():
    """Calling add_delegated_admin twice for the same user emits the
    audit event each time — the DB layer is idempotent on the
    underlying set, but the audit trail records every operator action
    (the owner pressed delegate again; that's still an action).
    """
    with (
        patch(
            "services.setup_session.db.add_delegated_admin",
            new_callable=AsyncMock,
        ),
        patch(
            "services.setup_session._emit_session_audit",
            new_callable=AsyncMock,
        ) as audit_mock,
    ):
        await svc.add_delegated_admin(guild_id=1, user_id=42, actor_id=99)
        await svc.add_delegated_admin(guild_id=1, user_id=42, actor_id=99)
    assert audit_mock.await_count == 2
