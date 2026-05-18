"""Phase 2d PR-3 — RolloutMutationPipeline 7-step contract.

Mocks the DB primitives so the pipeline can be exercised end-to-end
without an asyncpg pool.  Covers:

* Input validation: unknown flag, invalid state/tier/percent, scope
  mismatch.
* Authority: unknown actor_type rejected; platform_owner requires
  actor_id.
* DB write + audit row land atomically (the primitive returns; the
  pipeline does not branch on its sub-steps).
* Cache invalidation: clear_cache called with the right scope.
* Event emission: catalogued events fired with full payload; emission
  failure is swallowed (DB state is correct).
* Rollback semantics: a follow-up mutation that flips state back
  writes a NEW audit row — history is never mutated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime import feature_flags
from services.rollout_mutation import (
    EVT_ENVIRONMENT_TIER_CHANGED,
    EVT_FEATURE_FLAGS_CHANGED,
    EVT_ROLLOUT_ADVANCED,
    InvalidRolloutPercentError,
    InvalidStateError,
    InvalidTierError,
    RolloutMutationError,
    RolloutMutationPipeline,
    UnauthorizedRolloutMutationError,
    UnknownFeatureFlagError,
)


@pytest.fixture(autouse=True)
def _reset_state():
    feature_flags._reset_for_tests()
    feature_flags._register_builtins()
    yield
    feature_flags._reset_for_tests()


@pytest.fixture
def pipeline():
    return RolloutMutationPipeline()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_flag_state_rejects_unknown_flag(pipeline):
    with pytest.raises(UnknownFeatureFlagError):
        await pipeline.set_flag_state(
            flag_name="does.not.exist",
            scope="global",
            state="on",
            actor_id=1,
        )


@pytest.mark.asyncio
async def test_set_flag_state_rejects_invalid_state(pipeline):
    with pytest.raises(InvalidStateError):
        await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="maybe",
            actor_id=1,
        )


@pytest.mark.asyncio
async def test_set_flag_state_rejects_guild_scope_without_guild_id(pipeline):
    with pytest.raises(RolloutMutationError):
        await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="guild",
            state="on",
            actor_id=1,
            guild_id=None,
        )


@pytest.mark.asyncio
async def test_set_flag_state_rejects_global_scope_with_guild_id(pipeline):
    with pytest.raises(RolloutMutationError):
        await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="on",
            actor_id=1,
            guild_id=42,
        )


@pytest.mark.asyncio
async def test_set_rollout_percent_rejects_out_of_range(pipeline):
    with pytest.raises(InvalidRolloutPercentError):
        await pipeline.set_rollout_percent(
            flag_name="bindings.primary",
            percent=101,
            actor_id=1,
        )
    with pytest.raises(InvalidRolloutPercentError):
        await pipeline.set_rollout_percent(
            flag_name="bindings.primary",
            percent=-1,
            actor_id=1,
        )


@pytest.mark.asyncio
async def test_set_environment_tier_rejects_unknown_tier(pipeline):
    with pytest.raises(InvalidTierError):
        await pipeline.set_environment_tier(
            guild_id=42,
            tier="ultra-canary",
            actor_id=1,
        )


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_actor_type_rejected(pipeline):
    with pytest.raises(UnauthorizedRolloutMutationError):
        await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="on",
            actor_id=1,
            actor_type="random_user",
        )


@pytest.mark.asyncio
async def test_platform_owner_requires_actor_id(pipeline):
    with pytest.raises(UnauthorizedRolloutMutationError):
        await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="on",
            actor_id=None,
            actor_type="platform_owner",
        )


@pytest.mark.asyncio
async def test_system_actor_allowed_without_actor_id(pipeline):
    """CI seeds use actor_type='system' with actor_id=None."""
    with (
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.upsert_global_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        result = await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="off",
            actor_id=None,
            actor_type="system",
        )
    assert result.event_emitted is True
    mock_upsert.assert_awaited_once()


# ---------------------------------------------------------------------------
# DB write + cache invalidation + event emission (set_flag_state global)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_flag_state_global_writes_db_clears_cache_emits_event(pipeline):
    with (
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value={"state": "off", "rollout_percent": None},
        ),
        patch(
            "utils.db.feature_flag_state.upsert_global_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch.object(feature_flags, "clear_cache") as mock_clear,
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        result = await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="canary",
            actor_id=99,
        )
    # DB write happened with correct prev/new transition
    upsert_call = mock_upsert.await_args
    assert upsert_call.kwargs["flag_name"] == "bindings.primary"
    assert upsert_call.kwargs["state"] == "canary"
    assert upsert_call.kwargs["prev_state"] == "off"
    assert upsert_call.kwargs["mutation_type"] == "set_state"
    # Cache cleared for that flag
    mock_clear.assert_called_with(flag_name="bindings.primary")
    # Event emitted with full payload
    emit_call = mock_emit.await_args
    assert emit_call.args[0] == EVT_FEATURE_FLAGS_CHANGED
    payload = emit_call.kwargs
    assert payload["flag_name"] == "bindings.primary"
    assert payload["scope"] == "global"
    assert payload["guild_id"] is None
    assert payload["prev_state"] == "off"
    assert payload["new_state"] == "canary"
    assert payload["mutation_id"] == result.mutation_id
    assert payload["actor_id"] == 99
    assert payload["actor_type"] == "platform_owner"
    assert "occurred_at" in payload
    assert result.event_emitted is True


# ---------------------------------------------------------------------------
# DB write + cache + event (set_flag_state guild scope)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_flag_state_guild_clears_both_cache_scopes(pipeline):
    """Per-guild set must invalidate both per-guild AND global cache entries."""
    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.upsert_guild_with_audit",
            new_callable=AsyncMock,
        ),
        patch.object(feature_flags, "clear_cache") as mock_clear,
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="guild",
            state="on",
            actor_id=99,
            guild_id=42,
        )
    # clear_cache called twice: per-guild + global
    assert mock_clear.call_count == 2
    calls = {tuple(sorted(c.kwargs.items())) for c in mock_clear.call_args_list}
    assert (("flag_name", "bindings.primary"), ("guild_id", 42)) in calls
    assert (("flag_name", "bindings.primary"), ("guild_id", None)) in calls


# ---------------------------------------------------------------------------
# Event failure isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_emission_failure_does_not_raise(pipeline):
    """A subscriber that raises must not break the mutation contract."""
    with (
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.upsert_global_with_audit",
            new_callable=AsyncMock,
        ),
        patch(
            "core.events.bus.emit",
            new_callable=AsyncMock,
            side_effect=RuntimeError("subscriber crashed"),
        ),
    ):
        result = await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="on",
            actor_id=1,
        )
    assert result.event_emitted is False
    # DB write happened; the result reflects it
    assert result.new_state == "on"


# ---------------------------------------------------------------------------
# DB failure does NOT invalidate cache or emit event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_db_failure_does_not_invalidate_cache_or_emit_event(pipeline):
    with (
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.upsert_global_with_audit",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
        patch.object(feature_flags, "clear_cache") as mock_clear,
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        with pytest.raises(RuntimeError):
            await pipeline.set_flag_state(
                flag_name="bindings.primary",
                scope="global",
                state="on",
                actor_id=1,
            )
    mock_clear.assert_not_called()
    mock_emit.assert_not_awaited()


# ---------------------------------------------------------------------------
# set_rollout_percent — clears every cached guild decision
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_rollout_percent_clears_all_guild_caches_for_flag(pipeline):
    with (
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value={"state": "production", "rollout_percent": 10},
        ),
        patch(
            "utils.db.feature_flag_state.upsert_global_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch.object(feature_flags, "clear_cache") as mock_clear,
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        result = await pipeline.set_rollout_percent(
            flag_name="bindings.primary",
            percent=50,
            actor_id=99,
        )
    upsert_call = mock_upsert.await_args
    assert upsert_call.kwargs["rollout_percent"] == 50
    assert upsert_call.kwargs["prev_rollout_percent"] == 10
    assert upsert_call.kwargs["mutation_type"] == "set_rollout_percent"
    # State is preserved on a rollout-percent-only change
    assert upsert_call.kwargs["state"] == "production"
    # Cache cleared for the flag (every guild)
    mock_clear.assert_called_with(flag_name="bindings.primary")
    # Event emitted: rollout.advanced
    emit_call = mock_emit.await_args
    assert emit_call.args[0] == EVT_ROLLOUT_ADVANCED
    assert emit_call.kwargs["prev_percent"] == 10
    assert emit_call.kwargs["new_percent"] == 50
    assert result.new_rollout_percent == 50


# ---------------------------------------------------------------------------
# set_environment_tier — clears every cached entry for that guild
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_environment_tier_clears_full_guild_cache(pipeline):
    with (
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
        patch(
            "utils.db.environment_tiers.upsert_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch.object(feature_flags, "clear_cache") as mock_clear,
        patch("core.events.bus.emit", new_callable=AsyncMock) as mock_emit,
    ):
        result = await pipeline.set_environment_tier(
            guild_id=42,
            tier="canary",
            actor_id=99,
        )
    upsert_call = mock_upsert.await_args
    assert upsert_call.kwargs["guild_id"] == 42
    assert upsert_call.kwargs["tier"] == "canary"
    assert upsert_call.kwargs["prev_tier"] == "production"
    # The whole guild's cache is dropped (any flag could be affected).
    mock_clear.assert_called_with(guild_id=42)
    emit_call = mock_emit.await_args
    assert emit_call.args[0] == EVT_ENVIRONMENT_TIER_CHANGED
    assert emit_call.kwargs["prev_tier"] == "production"
    assert emit_call.kwargs["new_tier"] == "canary"
    assert result.new_tier == "canary"


# ---------------------------------------------------------------------------
# Rollback semantics — history is append-only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rollback_writes_new_audit_row_does_not_mutate_history(pipeline):
    """Flipping a flag back to its previous state writes a fresh audit row."""
    upserts: list[dict] = []

    async def _capture_upsert(**kwargs):
        upserts.append(dict(kwargs))

    with (
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            side_effect=[
                None,  # first call: no row → prev=None
                {"state": "on", "rollout_percent": None},  # rollback read
            ],
        ),
        patch(
            "utils.db.feature_flag_state.upsert_global_with_audit",
            side_effect=_capture_upsert,
        ),
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        first = await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="on",
            actor_id=1,
        )
        rollback = await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="off",
            actor_id=1,
        )
    assert first.mutation_id != rollback.mutation_id
    assert len(upserts) == 2
    # Each upsert is a NEW row — they carry distinct mutation_ids
    assert upserts[0]["mutation_id"] != upserts[1]["mutation_id"]
    # Rollback's prev_state is the value the forward write set; the new
    # state lands in the ``state`` kwarg (the column being written).
    assert upserts[1]["prev_state"] == "on"
    assert upserts[1]["state"] == "off"


# ---------------------------------------------------------------------------
# Catalogued event names — sanity check the literals haven't drifted
# ---------------------------------------------------------------------------


def test_catalogue_includes_phase_2d_event_names():
    from core.events_catalogue import KNOWN_EVENTS

    assert EVT_FEATURE_FLAGS_CHANGED in KNOWN_EVENTS
    assert EVT_ROLLOUT_ADVANCED in KNOWN_EVENTS
    assert EVT_ENVIRONMENT_TIER_CHANGED in KNOWN_EVENTS


# ---------------------------------------------------------------------------
# Minimal smoke: result type carries committed_at + mutation_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_carries_mutation_id_and_committed_at(pipeline):
    with (
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.upsert_global_with_audit",
            new_callable=AsyncMock,
        ),
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        result = await pipeline.set_flag_state(
            flag_name="bindings.primary",
            scope="global",
            state="on",
            actor_id=99,
        )
    assert isinstance(result.mutation_id, str)
    # UUID format: 36 chars with dashes
    assert len(result.mutation_id) == 36
    assert isinstance(result.committed_at, datetime)
    assert result.committed_at.tzinfo == timezone.utc
