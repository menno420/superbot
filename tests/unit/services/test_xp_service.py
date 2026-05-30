"""Tests for services.xp_service (S4)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.events_catalogue import KNOWN_EVENTS
from services import xp_service
from services.xp_service import EVT_LEVEL_UP, EVT_XP_AWARDED, EVT_XP_RESET


def test_events_are_catalogued():
    assert EVT_XP_AWARDED in KNOWN_EVENTS
    assert EVT_LEVEL_UP in KNOWN_EVENTS
    assert EVT_XP_RESET in KNOWN_EVENTS


@pytest.mark.asyncio
async def test_award_emits_xp_awarded_without_level_up():
    with (
        patch(
            "services.xp_service.db.add_xp",
            new_callable=AsyncMock,
            return_value=(150, 2, False),  # no level change
        ),
        patch(
            "services.xp_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        result = await xp_service.award(
            guild_id=1,
            user_id=2,
            amount=15,
            source="message",
        )
        assert result.new_xp == 150
        assert result.new_level == 2
        assert result.leveled_up is False
        # Exactly one emit — xp.awarded; no xp.level_up.
        assert emit.await_count == 1
        emit.assert_awaited_with(
            EVT_XP_AWARDED,
            guild_id=1,
            user_id=2,
            delta=15,
            new_xp=150,
            new_level=2,
            source="message",
        )


@pytest.mark.asyncio
async def test_award_emits_level_up_on_boundary():
    with (
        patch(
            "services.xp_service.db.add_xp",
            new_callable=AsyncMock,
            return_value=(200, 3, True),
        ),
        patch(
            "services.xp_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        result = await xp_service.award(
            guild_id=1,
            user_id=2,
            amount=50,
            source="work:carpenter",
        )
        assert result.leveled_up is True
        # Both events fire, in order (xp.awarded then xp.level_up).
        assert emit.await_count == 2
        assert emit.await_args_list[0].args[0] == EVT_XP_AWARDED
        assert emit.await_args_list[1].args[0] == EVT_LEVEL_UP
        # level_up payload carries the new level + source attribution
        level_up_call = emit.await_args_list[1]
        assert level_up_call.kwargs["new_level"] == 3
        assert level_up_call.kwargs["source"] == "work:carpenter"


@pytest.mark.asyncio
async def test_non_positive_amount_rejected():
    with pytest.raises(ValueError, match="positive"):
        await xp_service.award(guild_id=1, user_id=2, amount=0, source="x")
    with pytest.raises(ValueError, match="positive"):
        await xp_service.award(guild_id=1, user_id=2, amount=-5, source="x")


@pytest.mark.asyncio
async def test_reset_deletes_row_and_emits_event():
    with (
        patch(
            "services.xp_service.db.delete_xp",
            new_callable=AsyncMock,
        ) as delete_xp,
        patch(
            "services.xp_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
        patch(
            "services.xp_service.emit_audit_action",
            new_callable=AsyncMock,
        ),
    ):
        await xp_service.reset(
            guild_id=42,
            user_id=7,
            source="admin:resetxp",
            actor_id=99,
        )

    delete_xp.assert_awaited_once_with(7, 42)
    emit.assert_awaited_once_with(
        EVT_XP_RESET,
        guild_id=42,
        user_id=7,
        actor_id=99,
        source="admin:resetxp",
    )


@pytest.mark.asyncio
async def test_reset_actor_defaults_to_none():
    """actor_id is optional — non-admin reset paths shouldn't need to lie."""
    with (
        patch("services.xp_service.db.delete_xp", new_callable=AsyncMock),
        patch("services.xp_service.bus.emit", new_callable=AsyncMock) as emit,
        patch("services.xp_service.emit_audit_action", new_callable=AsyncMock),
    ):
        await xp_service.reset(guild_id=1, user_id=2, source="system:purge")

    assert emit.await_args.kwargs["actor_id"] is None


@pytest.mark.asyncio
async def test_reset_emits_audit_action_for_server_logging():
    """An XP wipe must reach the shared ``audit.action_recorded`` stream
    (audit P1-1) so server logging is no longer blind to it.
    """
    with (
        patch("services.xp_service.db.delete_xp", new_callable=AsyncMock),
        patch("services.xp_service.bus.emit", new_callable=AsyncMock),
        patch(
            "services.xp_service.emit_audit_action",
            new_callable=AsyncMock,
        ) as audit,
    ):
        await xp_service.reset(
            guild_id=42,
            user_id=7,
            source="admin:resetxp",
            actor_id=99,
            actor_type="admin",
        )

    audit.assert_awaited_once()
    kwargs = audit.await_args.kwargs
    assert kwargs["subsystem"] == "xp"
    assert kwargs["mutation_type"] == "reset_xp"
    assert kwargs["target"] == "member:7"
    assert kwargs["scope"] == "guild"
    assert kwargs["guild_id"] == 42
    assert kwargs["actor_id"] == 99
    assert kwargs["actor_type"] == "admin"
    assert kwargs["new_value"] is None
