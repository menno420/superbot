"""Phase 2c PR-9 — ParticipationMutationPipeline 7-step contract.

Mocks the DB primitives + the event bus so the pipeline can be
exercised end-to-end without a real DB.  Covers:

* Input validation per entrypoint (invalid state, invalid visibility,
  invalid preference value, non-bool enabled).
* Authority: actor_type allow-list; 'user' requires actor_id ==
  user_id; 'moderator' / 'admin' require non-None actor_id; 'system'
  may have None.
* DB write happens in step 4; cache invalidation (step 5) happens
  inline AFTER successful write; event (step 6) emits AFTER cache.
* Event subscriber failure logged + swallowed; result.event_emitted
  reflects it without rolling back the DB write.
* DB failure → no cache invalidation, no event emission, exception
  propagates.
* Rollback semantics — flipping back writes a NEW audit row.
* Each catalogued event name is registered in KNOWN_EVENTS.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services.participation_mutation import (
    EVT_PARTICIPATION_CHANGED,
    EVT_SUBSCRIPTION_CHANGED,
    EVT_USER_PREFERENCE_CHANGED,
    EVT_USER_VISIBILITY_CHANGED,
    InvalidParticipationStateError,
    InvalidPreferenceValueError,
    InvalidVisibilityStateError,
    ParticipationMutationError,
    ParticipationMutationPipeline,
    UnauthorizedParticipationMutationError,
)


@pytest.fixture
def pipeline():
    return ParticipationMutationPipeline()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_participation_rejects_invalid_state(pipeline):
    with pytest.raises(InvalidParticipationStateError):
        await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="maybe",
            actor_id=1,
        )


@pytest.mark.asyncio
async def test_set_visibility_rejects_invalid_state(pipeline):
    with pytest.raises(InvalidVisibilityStateError):
        await pipeline.set_visibility(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            visibility="indeterminate",
            actor_id=1,
        )


@pytest.mark.asyncio
async def test_set_subscription_rejects_non_bool_enabled(pipeline):
    with pytest.raises(ParticipationMutationError):
        await pipeline.set_subscription(
            user_id=1,
            guild_id=2,
            subsystem="economy",
            topic="daily",
            enabled="yes",  # type: ignore[arg-type]
            actor_id=1,
        )


@pytest.mark.asyncio
async def test_set_preference_rejects_none_value(pipeline):
    with pytest.raises(InvalidPreferenceValueError):
        await pipeline.set_preference(
            user_id=1,
            guild_id=2,
            key="digest_freq",
            value=None,
            actor_id=1,
        )


@pytest.mark.asyncio
async def test_set_preference_rejects_non_serialisable_value(pipeline):
    """A truly non-serialisable value (circular reference) is rejected.

    ``json.dumps`` with ``default=str`` tolerates almost any object,
    but a circular structure still raises ``ValueError`` (max recursion).
    The pipeline catches that as :class:`InvalidPreferenceValueError`.
    """
    cyclic: dict = {}
    cyclic["self"] = cyclic
    with pytest.raises(InvalidPreferenceValueError):
        await pipeline.set_preference(
            user_id=1,
            guild_id=2,
            key="weird",
            value=cyclic,
            actor_id=1,
        )


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_actor_must_be_self(pipeline):
    """actor_type='user' with actor_id != user_id is rejected."""
    with pytest.raises(UnauthorizedParticipationMutationError):
        await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_out",
            actor_id=999,  # not self
            actor_type="user",
        )


@pytest.mark.asyncio
async def test_user_actor_requires_actor_id(pipeline):
    with pytest.raises(UnauthorizedParticipationMutationError):
        await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_out",
            actor_id=None,
            actor_type="user",
        )


@pytest.mark.asyncio
async def test_unknown_actor_type_rejected(pipeline):
    with pytest.raises(UnauthorizedParticipationMutationError):
        await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_out",
            actor_id=1,
            actor_type="hacker",
        )


@pytest.mark.asyncio
async def test_moderator_actor_requires_actor_id(pipeline):
    with pytest.raises(UnauthorizedParticipationMutationError):
        await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_out",
            actor_id=None,
            actor_type="moderator",
        )


@pytest.mark.asyncio
async def test_system_actor_allowed_without_actor_id(pipeline):
    """CI seeds use actor_type='system' with actor_id=None."""
    with (
        patch(
            "utils.db.user_participation.get_participation",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.user_participation.upsert_participation_with_audit",
            new_callable=AsyncMock,
        ),
        patch("core.events.bus.emit", new_callable=AsyncMock),
        patch("core.runtime.user_config.invalidate_user_guild"),
    ):
        result = await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_in",
            actor_id=None,
            actor_type="system",
        )
    assert result.actor_type == "system"
    assert result.actor_id is None


# ---------------------------------------------------------------------------
# Happy path: DB write → cache invalidate → event emit (in that order)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_participation_writes_db_invalidates_cache_emits_event(pipeline):
    with (
        patch(
            "utils.db.user_participation.get_participation",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.user_participation.upsert_participation_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch(
            "core.runtime.user_config.invalidate_user_guild",
        ) as mock_invalidate,
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        result = await pipeline.set_participation(
            user_id=42,
            guild_id=99,
            subsystem="xp",
            state="opted_out",
            actor_id=42,
        )

    # DB write with prev_state=None (no previous row)
    upsert_call = mock_upsert.await_args
    assert upsert_call.kwargs["user_id"] == 42
    assert upsert_call.kwargs["guild_id"] == 99
    assert upsert_call.kwargs["subsystem"] == "xp"
    assert upsert_call.kwargs["state"] == "opted_out"
    assert upsert_call.kwargs["prev_state"] is None
    assert upsert_call.kwargs["actor_type"] == "user"

    # Cache invalidated for this (user, guild)
    mock_invalidate.assert_called_once_with(42, 99)

    # Event emitted with full payload
    emit_call = mock_emit.await_args
    assert emit_call.args[0] == EVT_PARTICIPATION_CHANGED
    assert emit_call.kwargs["user_id"] == 42
    assert emit_call.kwargs["guild_id"] == 99
    assert emit_call.kwargs["subsystem"] == "xp"
    assert emit_call.kwargs["prev_state"] is None
    assert emit_call.kwargs["new_state"] == "opted_out"
    assert emit_call.kwargs["mutation_id"] == result.mutation_id
    assert "occurred_at" in emit_call.kwargs

    assert result.event_emitted is True
    assert result.mutation_type == "set_participation"
    assert isinstance(result.committed_at, datetime)
    assert result.committed_at.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_set_subscription_emits_correct_event(pipeline):
    with (
        patch(
            "utils.db.user_participation.get_subscription",
            new_callable=AsyncMock,
            return_value={"enabled": True},
        ),
        patch(
            "utils.db.user_participation.upsert_subscription_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch("core.runtime.user_config.invalidate_user_guild"),
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        result = await pipeline.set_subscription(
            user_id=1,
            guild_id=2,
            subsystem="economy",
            topic="daily",
            enabled=False,
            actor_id=1,
        )
    assert mock_emit.await_args.args[0] == EVT_SUBSCRIPTION_CHANGED
    assert mock_emit.await_args.kwargs["prev_enabled"] is True
    assert mock_emit.await_args.kwargs["new_enabled"] is False
    assert mock_upsert.await_args.kwargs["prev_enabled"] is True
    assert result.mutation_type == "set_subscription"


@pytest.mark.asyncio
async def test_set_preference_event_omits_value(pipeline):
    """Privacy: preference value MUST NOT appear in the event payload."""
    with (
        patch(
            "utils.db.user_participation.get_preference",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.user_participation.upsert_preference_with_audit",
            new_callable=AsyncMock,
        ),
        patch("core.runtime.user_config.invalidate_user_guild"),
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        result = await pipeline.set_preference(
            user_id=1,
            guild_id=2,
            key="digest_freq",
            value={"unit": "hours", "interval": 6},
            actor_id=1,
        )
    emit_call = mock_emit.await_args
    assert emit_call.args[0] == EVT_USER_PREFERENCE_CHANGED
    assert "value" not in emit_call.kwargs
    assert "prev_value" not in emit_call.kwargs
    assert "new_value" not in emit_call.kwargs
    # The result still carries the value for caller use
    assert result.new_value == {"unit": "hours", "interval": 6}


@pytest.mark.asyncio
async def test_set_visibility_emits_correct_event(pipeline):
    with (
        patch(
            "utils.db.user_participation.get_visibility",
            new_callable=AsyncMock,
            return_value={"visibility": "public"},
        ),
        patch(
            "utils.db.user_participation.upsert_visibility_with_audit",
            new_callable=AsyncMock,
        ),
        patch("core.runtime.user_config.invalidate_user_guild"),
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        await pipeline.set_visibility(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            visibility="hidden",
            actor_id=1,
        )
    assert mock_emit.await_args.args[0] == EVT_USER_VISIBILITY_CHANGED
    assert mock_emit.await_args.kwargs["prev_visibility"] == "public"
    assert mock_emit.await_args.kwargs["new_visibility"] == "hidden"


# ---------------------------------------------------------------------------
# Cache invalidation contract: synchronous, inline, BEFORE event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_invalidation_called_inline_after_write(pipeline):
    """Cache is invalidated in the mutation flow, not via event subscription.

    This is the architectural contract: even if no event subscriber is
    listening (or the bus is down), the cache stays consistent with DB.
    """
    call_order: list[str] = []

    async def fake_upsert(**_):
        call_order.append("upsert")

    def fake_invalidate(*_):
        call_order.append("invalidate")

    async def fake_emit(*_, **__):
        call_order.append("emit")

    with (
        patch(
            "utils.db.user_participation.get_participation",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.user_participation.upsert_participation_with_audit",
            side_effect=fake_upsert,
        ),
        patch(
            "core.runtime.user_config.invalidate_user_guild",
            side_effect=fake_invalidate,
        ),
        patch(
            "core.events.bus.emit",
            side_effect=fake_emit,
        ),
    ):
        await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_out",
            actor_id=1,
        )
    assert call_order == ["upsert", "invalidate", "emit"]


# ---------------------------------------------------------------------------
# Event failure isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_failure_does_not_roll_back_db_write(pipeline):
    """Subscriber failure logged + swallowed; result reflects but DB persists."""
    with (
        patch(
            "utils.db.user_participation.get_participation",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.user_participation.upsert_participation_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch("core.runtime.user_config.invalidate_user_guild"),
        patch(
            "core.events.bus.emit",
            new_callable=AsyncMock,
            side_effect=RuntimeError("subscriber crashed"),
        ),
    ):
        result = await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_out",
            actor_id=1,
        )
    # DB write happened
    mock_upsert.assert_awaited_once()
    # Event flagged as not emitted
    assert result.event_emitted is False
    # But the mutation result itself is returned successfully
    assert result.new_state == "opted_out"


# ---------------------------------------------------------------------------
# DB failure rolls back the entire flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_db_failure_skips_cache_and_event(pipeline):
    with (
        patch(
            "utils.db.user_participation.get_participation",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.user_participation.upsert_participation_with_audit",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
        patch(
            "core.runtime.user_config.invalidate_user_guild",
        ) as mock_invalidate,
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        with pytest.raises(RuntimeError):
            await pipeline.set_participation(
                user_id=1,
                guild_id=2,
                subsystem="xp",
                state="opted_out",
                actor_id=1,
            )
    mock_invalidate.assert_not_called()
    mock_emit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Rollback semantics: new audit row, not in-place update
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rollback_writes_new_audit_row_not_in_place_update(pipeline):
    upserts: list[dict] = []

    async def capture(**kwargs):
        upserts.append(kwargs)

    with (
        patch(
            "utils.db.user_participation.get_participation",
            new_callable=AsyncMock,
            side_effect=[
                None,
                {"state": "opted_out"},
            ],
        ),
        patch(
            "utils.db.user_participation.upsert_participation_with_audit",
            side_effect=capture,
        ),
        patch("core.runtime.user_config.invalidate_user_guild"),
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        first = await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_out",
            actor_id=1,
        )
        rollback = await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_in",
            actor_id=1,
        )
    assert first.mutation_id != rollback.mutation_id
    assert len(upserts) == 2
    # Each write has its own mutation_id (UUID-shaped)
    assert upserts[0]["mutation_id"] != upserts[1]["mutation_id"]
    # Rollback captured the prior state correctly
    assert upserts[1]["prev_state"] == "opted_out"
    assert upserts[1]["state"] == "opted_in"


# ---------------------------------------------------------------------------
# Catalogue check
# ---------------------------------------------------------------------------


def test_phase_2c_pr9_events_in_catalogue():
    from core.events_catalogue import KNOWN_EVENTS

    assert EVT_PARTICIPATION_CHANGED in KNOWN_EVENTS
    assert EVT_SUBSCRIPTION_CHANGED in KNOWN_EVENTS
    assert EVT_USER_PREFERENCE_CHANGED in KNOWN_EVENTS
    assert EVT_USER_VISIBILITY_CHANGED in KNOWN_EVENTS


# ---------------------------------------------------------------------------
# Result type carries UUID + tz-aware committed_at
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_carries_uuid_mutation_id_and_tz_aware_committed_at(pipeline):
    with (
        patch(
            "utils.db.user_participation.get_participation",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.user_participation.upsert_participation_with_audit",
            new_callable=AsyncMock,
        ),
        patch("core.runtime.user_config.invalidate_user_guild"),
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        result = await pipeline.set_participation(
            user_id=1,
            guild_id=2,
            subsystem="xp",
            state="opted_in",
            actor_id=1,
        )
    assert isinstance(result.mutation_id, str)
    assert len(result.mutation_id) == 36  # UUID standard format
    assert result.committed_at.tzinfo == timezone.utc
