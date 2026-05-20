"""Phase 9g / Track 6 PR 16 — automation mutation pipeline tests.

Pins:

* Input validation rejects unknown kinds + missing required config keys.
* Authority gate: ``platform_owner`` requires ``actor_id ==
  guild_owner_id``; ``system`` actor allowed without actor_id;
  any other actor_type rejected.
* Create / set_enabled / delete each emit
  ``automation.rule_changed`` AND ``audit.action_recorded`` with
  matching ``mutation_id``.
* set_enabled is idempotent for a no-op flip: still emits an audit
  row but does NOT emit ``automation.rule_changed``.
* Pipeline failures in the bus.emit path do NOT roll back DB
  writes — the audit emitter swallows.
* Unknown rule_id (or wrong guild_id) on update/delete raises
  ``UnknownAutomationRuleError``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.automation_mutation import (
    AutomationMutationPipeline,
    InvalidAutomationConfigError,
    UnauthorizedAutomationMutationError,
    UnknownAutomationRuleError,
)


@pytest.fixture
def pipeline():
    return AutomationMutationPipeline()


@pytest.fixture
def _mock_db():
    with (
        patch(
            "services.automation_mutation.db.insert_rule",
            new_callable=AsyncMock,
        ) as insert_rule,
        patch(
            "services.automation_mutation.db.get_rule",
            new_callable=AsyncMock,
        ) as get_rule,
        patch(
            "services.automation_mutation.db.set_enabled",
            new_callable=AsyncMock,
        ) as set_enabled,
        patch(
            "services.automation_mutation.db.delete_rule",
            new_callable=AsyncMock,
        ) as delete_rule,
        patch(
            "services.automation_mutation.emit_audit_action",
            new_callable=AsyncMock,
            return_value=True,
        ) as emit_audit,
        patch("core.events.bus.emit", new_callable=AsyncMock) as bus_emit,
    ):
        yield {
            "insert_rule": insert_rule,
            "get_rule": get_rule,
            "set_enabled": set_enabled,
            "delete_rule": delete_rule,
            "emit_audit": emit_audit,
            "bus_emit": bus_emit,
        }


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_rejects_unknown_trigger_kind(pipeline, _mock_db):
    with pytest.raises(InvalidAutomationConfigError, match="trigger_kind"):
        await pipeline.create_rule(
            guild_id=1,
            guild_owner_id=99,
            name="x",
            trigger_kind="garbage",
            action_kind="notify_owner",
            action_config={"template": "hi"},
            actor_id=99,
        )
    _mock_db["insert_rule"].assert_not_awaited()


@pytest.mark.asyncio
async def test_create_rejects_unknown_action_kind(pipeline, _mock_db):
    with pytest.raises(InvalidAutomationConfigError, match="action_kind"):
        await pipeline.create_rule(
            guild_id=1,
            guild_owner_id=99,
            name="x",
            trigger_kind="manual",
            action_kind="eat_sandwich",
            actor_id=99,
        )


@pytest.mark.asyncio
async def test_create_rejects_missing_required_config_key(pipeline, _mock_db):
    with pytest.raises(InvalidAutomationConfigError, match="template"):
        # send_message requires channel_id + template; only channel_id given.
        await pipeline.create_rule(
            guild_id=1,
            guild_owner_id=99,
            name="x",
            trigger_kind="manual",
            action_kind="send_message",
            action_config={"channel_id": 555},
            actor_id=99,
        )


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_rejects_unknown_actor_type(pipeline, _mock_db):
    with pytest.raises(UnauthorizedAutomationMutationError, match="actor_type"):
        await pipeline.create_rule(
            guild_id=1,
            guild_owner_id=99,
            name="x",
            trigger_kind="manual",
            action_kind="notify_owner",
            action_config={"template": "hi"},
            actor_id=99,
            actor_type="user",
        )


@pytest.mark.asyncio
async def test_create_rejects_non_owner(pipeline, _mock_db):
    with pytest.raises(UnauthorizedAutomationMutationError, match="not the guild owner"):
        await pipeline.create_rule(
            guild_id=1,
            guild_owner_id=99,
            name="x",
            trigger_kind="manual",
            action_kind="notify_owner",
            action_config={"template": "hi"},
            actor_id=42,
            actor_type="platform_owner",
        )


@pytest.mark.asyncio
async def test_create_accepts_system_actor_without_actor_id(pipeline, _mock_db):
    _mock_db["insert_rule"].return_value = 7
    result = await pipeline.create_rule(
        guild_id=1,
        guild_owner_id=99,
        name="seed",
        trigger_kind="manual",
        action_kind="notify_owner",
        action_config={"template": "hi"},
        actor_id=None,
        actor_type="system",
    )
    assert result.mutation_type == "create"
    assert result.rule_id == 7


# ---------------------------------------------------------------------------
# Happy paths + event emission
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_emits_rule_changed_and_audit(pipeline, _mock_db):
    _mock_db["insert_rule"].return_value = 7
    result = await pipeline.create_rule(
        guild_id=1,
        guild_owner_id=99,
        name="welcome",
        trigger_kind="member_join",
        action_kind="send_message",
        action_config={"channel_id": 1, "template": "hi"},
        actor_id=99,
    )
    # Pipeline event
    bus_call = _mock_db["bus_emit"].await_args
    assert bus_call.args[0] == "automation.rule_changed"
    assert bus_call.kwargs["mutation_id"] == result.mutation_id
    assert bus_call.kwargs["mutation_type"] == "create"
    # Companion audit
    audit_kwargs = _mock_db["emit_audit"].await_args.kwargs
    assert audit_kwargs["mutation_id"] == result.mutation_id
    assert audit_kwargs["subsystem"] == "automation"
    assert audit_kwargs["mutation_type"] == "create_rule"
    assert audit_kwargs["target"] == "rule:welcome"
    assert audit_kwargs["new_value"] == "member_join->send_message"
    assert audit_kwargs["actor_id"] == 99


@pytest.mark.asyncio
async def test_set_enabled_emits_when_state_changes(pipeline, _mock_db):
    _mock_db["get_rule"].return_value = {
        "id": 7,
        "guild_id": 1,
        "name": "welcome",
        "enabled": False,
        "trigger_kind": "manual",
        "action_kind": "notify_owner",
    }
    result = await pipeline.set_enabled(
        guild_id=1,
        guild_owner_id=99,
        rule_id=7,
        enabled=True,
        actor_id=99,
    )
    _mock_db["set_enabled"].assert_awaited_once_with(7, True)
    assert result.event_emitted is True
    assert result.prev_enabled is False
    assert result.new_enabled is True


@pytest.mark.asyncio
async def test_set_enabled_is_idempotent_for_no_op(pipeline, _mock_db):
    """Flipping enabled from True to True still emits an audit row
    but does NOT emit ``automation.rule_changed``."""
    _mock_db["get_rule"].return_value = {
        "id": 7,
        "guild_id": 1,
        "name": "welcome",
        "enabled": True,
        "trigger_kind": "manual",
        "action_kind": "notify_owner",
    }
    result = await pipeline.set_enabled(
        guild_id=1,
        guild_owner_id=99,
        rule_id=7,
        enabled=True,
        actor_id=99,
    )
    _mock_db["set_enabled"].assert_not_awaited()
    _mock_db["bus_emit"].assert_not_awaited()
    _mock_db["emit_audit"].assert_awaited_once()
    assert result.event_emitted is False
    assert result.prev_enabled is True
    assert result.new_enabled is True


@pytest.mark.asyncio
async def test_delete_emits_audit_with_old_value(pipeline, _mock_db):
    _mock_db["get_rule"].return_value = {
        "id": 7,
        "guild_id": 1,
        "name": "welcome",
        "enabled": True,
        "trigger_kind": "member_join",
        "action_kind": "send_message",
    }
    result = await pipeline.delete_rule(
        guild_id=1,
        guild_owner_id=99,
        rule_id=7,
        actor_id=99,
    )
    _mock_db["delete_rule"].assert_awaited_once_with(7)
    audit_kwargs = _mock_db["emit_audit"].await_args.kwargs
    assert audit_kwargs["mutation_type"] == "delete_rule"
    assert audit_kwargs["prev_value"] == "member_join->send_message"
    assert audit_kwargs["new_value"] is None
    assert result.event_emitted is True


# ---------------------------------------------------------------------------
# Unknown rule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_enabled_raises_when_rule_missing(pipeline, _mock_db):
    _mock_db["get_rule"].return_value = None
    with pytest.raises(UnknownAutomationRuleError):
        await pipeline.set_enabled(
            guild_id=1,
            guild_owner_id=99,
            rule_id=7,
            enabled=True,
            actor_id=99,
        )


@pytest.mark.asyncio
async def test_set_enabled_raises_when_rule_in_different_guild(pipeline, _mock_db):
    _mock_db["get_rule"].return_value = {
        "id": 7,
        "guild_id": 2,  # different guild
        "name": "x",
        "enabled": False,
        "trigger_kind": "manual",
        "action_kind": "notify_owner",
    }
    with pytest.raises(UnknownAutomationRuleError):
        await pipeline.set_enabled(
            guild_id=1,
            guild_owner_id=99,
            rule_id=7,
            enabled=True,
            actor_id=99,
        )


@pytest.mark.asyncio
async def test_delete_raises_when_rule_missing(pipeline, _mock_db):
    _mock_db["get_rule"].return_value = None
    with pytest.raises(UnknownAutomationRuleError):
        await pipeline.delete_rule(
            guild_id=1,
            guild_owner_id=99,
            rule_id=7,
            actor_id=99,
        )


# ---------------------------------------------------------------------------
# Failure isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_emission_failure_does_not_undo_db_write(pipeline, _mock_db):
    """A raising bus.emit must not propagate; the pipeline returns
    ``event_emitted=False`` and the DB write stays."""
    _mock_db["insert_rule"].return_value = 7
    _mock_db["bus_emit"].side_effect = RuntimeError("bus down")
    result = await pipeline.create_rule(
        guild_id=1,
        guild_owner_id=99,
        name="welcome",
        trigger_kind="manual",
        action_kind="notify_owner",
        action_config={"template": "hi"},
        actor_id=99,
    )
    _mock_db["insert_rule"].assert_awaited_once()
    assert result.event_emitted is False


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def test_event_topic_in_known_events():
    from core.events_catalogue import KNOWN_EVENTS

    assert "automation.rule_changed" in KNOWN_EVENTS
