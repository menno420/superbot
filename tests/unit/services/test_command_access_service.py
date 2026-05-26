"""PR-3 — command-access mutation service tests.

Pins the 6-step contract for every public mutation:

  1. validates inputs (mode literal, actor_type)
  2. reads previous state via the DB primitives
  3. writes through ``utils.db.command_access`` primitives
  4. invalidates the typed-accessor cache INLINE
  5. emits ``audit.action_recorded`` with the correct payload
  6. returns a typed result carrying ``mutation_id``

Plus:

* idempotent no-ops on add / remove / replace skip the audit emission
* the composite ``set_policy`` runs the underlying ops in order and
  preserves the channel list when called with ``channel_ids=None``
* ``forget_guild`` paired cache-invalidate + DB-delete

The DB primitives, typed accessor, and ``emit_audit_action`` publisher
are all mocked so the tests are asyncpg-free and bus-free.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import command_access_service as service
from services.command_access_service import (
    CommandAccessMutationResult,
    InvalidCommandAccessModeError,
    UnauthorizedCommandAccessActorError,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_mock():
    """Patch the ``utils.db.command_access`` primitives referenced by
    the service as ``db`` (the module-level alias).  Returns the mock
    namespace so assertions can introspect call args.
    """
    with patch.object(service, "db") as db:
        # KNOWN_MODES is the real frozenset — the validator checks
        # against it directly.
        db.KNOWN_MODES = frozenset(
            {
                "all_channels",
                "selected_channels",
                "disabled_except_bootstrap",
            },
        )
        db.get_policy = AsyncMock(return_value=None)
        db.list_allowed_channels = AsyncMock(return_value=[])
        db.set_mode = AsyncMock()
        db.add_allowed_channel = AsyncMock()
        db.remove_allowed_channel = AsyncMock()
        db.replace_allowed_channels = AsyncMock()
        yield db


@pytest.fixture
def invalidate_mock():
    with patch.object(
        service,
        "invalidate_command_access_policy",
    ) as invalidate:
        yield invalidate


@pytest.fixture
def audit_mock():
    """Patch the shared ``emit_audit_action`` so tests inspect the
    payload without crossing the event-bus boundary.
    """
    with patch.object(
        service,
        "emit_audit_action",
        new=AsyncMock(return_value=True),
    ) as audit:
        yield audit


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_mode_rejects_unknown_mode(db_mock, invalidate_mock, audit_mock):
    with pytest.raises(InvalidCommandAccessModeError):
        await service.set_mode(guild_id=10, mode="garbage", actor_id=99)
    db_mock.set_mode.assert_not_awaited()
    invalidate_mock.assert_not_called()
    audit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_mode_rejects_unknown_actor_type(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    with pytest.raises(UnauthorizedCommandAccessActorError):
        await service.set_mode(
            guild_id=10,
            mode="all_channels",
            actor_id=99,
            actor_type="anonymous",
        )
    db_mock.set_mode.assert_not_awaited()
    invalidate_mock.assert_not_called()


@pytest.mark.asyncio
async def test_add_allowed_channel_rejects_non_int_channel_id(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    with pytest.raises(TypeError):
        await service.add_allowed_channel(
            guild_id=10,
            channel_id="555",  # type: ignore[arg-type]
            actor_id=99,
        )
    db_mock.add_allowed_channel.assert_not_awaited()


# ---------------------------------------------------------------------------
# set_mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_mode_writes_invalidates_and_emits_audit(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    db_mock.get_policy.return_value = {"mode": "all_channels"}
    result = await service.set_mode(
        guild_id=10,
        mode="selected_channels",
        actor_id=99,
    )

    # 3. DB write
    db_mock.set_mode.assert_awaited_once_with(
        guild_id=10,
        mode="selected_channels",
        updated_by=99,
    )
    # 4. cache invalidation INLINE
    invalidate_mock.assert_called_once_with(10)
    # 5. audit emission with the prev_value pulled from get_policy
    audit_mock.assert_awaited_once()
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["subsystem"] == "command_access"
    assert kwargs["mutation_type"] == "set_mode"
    assert kwargs["target"] == "command_access:mode"
    assert kwargs["scope"] == "guild"
    assert kwargs["guild_id"] == 10
    assert kwargs["prev_value"] == "all_channels"
    assert kwargs["new_value"] == "selected_channels"
    assert kwargs["actor_id"] == 99
    assert kwargs["actor_type"] == "admin"
    # 6. typed result
    assert isinstance(result, CommandAccessMutationResult)
    assert result.mutation_type == "set_mode"
    assert result.prev_value == "all_channels"
    assert result.new_value == "selected_channels"
    assert result.audit_emitted is True
    assert kwargs["mutation_id"] == result.mutation_id


@pytest.mark.asyncio
async def test_set_mode_uses_null_prev_value_when_unconfigured(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    db_mock.get_policy.return_value = None
    result = await service.set_mode(
        guild_id=10,
        mode="all_channels",
        actor_id=99,
    )
    assert result.prev_value is None
    assert audit_mock.await_args.kwargs["prev_value"] is None


# ---------------------------------------------------------------------------
# add_allowed_channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_allowed_channel_writes_and_emits_when_new(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    db_mock.list_allowed_channels.return_value = [100, 200]
    result = await service.add_allowed_channel(
        guild_id=10,
        channel_id=300,
        actor_id=99,
    )
    db_mock.add_allowed_channel.assert_awaited_once_with(
        guild_id=10,
        channel_id=300,
        created_by=99,
    )
    invalidate_mock.assert_called_once_with(10)
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["target"] == "command_access:channel:300"
    assert kwargs["prev_value"] is None
    assert kwargs["new_value"] == "300"
    assert result.audit_emitted is True


@pytest.mark.asyncio
async def test_add_allowed_channel_is_idempotent_no_audit_no_invalidate(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    """Already-present channel: skip DB write + cache invalidate + audit.

    The DB primitive is itself ON CONFLICT DO NOTHING, but emitting an
    audit row for a true no-op pollutes the audit trail.
    """
    db_mock.list_allowed_channels.return_value = [100, 200, 300]
    result = await service.add_allowed_channel(
        guild_id=10,
        channel_id=300,
        actor_id=99,
    )
    db_mock.add_allowed_channel.assert_not_awaited()
    invalidate_mock.assert_not_called()
    audit_mock.assert_not_awaited()
    assert result.audit_emitted is False


# ---------------------------------------------------------------------------
# remove_allowed_channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_allowed_channel_writes_and_emits_when_present(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    db_mock.list_allowed_channels.return_value = [100, 200, 300]
    result = await service.remove_allowed_channel(
        guild_id=10,
        channel_id=200,
        actor_id=99,
    )
    db_mock.remove_allowed_channel.assert_awaited_once_with(
        guild_id=10,
        channel_id=200,
    )
    invalidate_mock.assert_called_once_with(10)
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["mutation_type"] == "remove_allowed_channel"
    assert kwargs["target"] == "command_access:channel:200"
    assert kwargs["prev_value"] == "200"
    assert kwargs["new_value"] is None
    assert result.audit_emitted is True


@pytest.mark.asyncio
async def test_remove_allowed_channel_is_idempotent_when_absent(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    db_mock.list_allowed_channels.return_value = [100, 200]
    result = await service.remove_allowed_channel(
        guild_id=10,
        channel_id=999,
        actor_id=99,
    )
    db_mock.remove_allowed_channel.assert_not_awaited()
    invalidate_mock.assert_not_called()
    audit_mock.assert_not_awaited()
    assert result.audit_emitted is False


# ---------------------------------------------------------------------------
# replace_allowed_channels
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replace_allowed_channels_writes_and_emits_diff(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    db_mock.list_allowed_channels.return_value = [100, 200]
    result = await service.replace_allowed_channels(
        guild_id=10,
        channel_ids=[300, 100, 400],
        actor_id=99,
    )
    db_mock.replace_allowed_channels.assert_awaited_once_with(
        guild_id=10,
        channel_ids=[100, 300, 400],
        created_by=99,
    )
    invalidate_mock.assert_called_once_with(10)
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["mutation_type"] == "replace_allowed_channels"
    assert kwargs["target"] == "command_access:channels"
    # Rendered as stable sorted comma-separated bracketed list.
    assert kwargs["prev_value"] == "[100,200]"
    assert kwargs["new_value"] == "[100,300,400]"
    assert result.audit_emitted is True


@pytest.mark.asyncio
async def test_replace_allowed_channels_skips_when_unchanged(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    """prev == new (after sort + dedupe) — true no-op, no audit row."""
    db_mock.list_allowed_channels.return_value = [100, 200]
    result = await service.replace_allowed_channels(
        guild_id=10,
        channel_ids=[200, 100, 200],  # dedupes to {100, 200}
        actor_id=99,
    )
    db_mock.replace_allowed_channels.assert_not_awaited()
    invalidate_mock.assert_not_called()
    audit_mock.assert_not_awaited()
    assert result.audit_emitted is False
    assert result.prev_value == result.new_value == "[100,200]"


# ---------------------------------------------------------------------------
# set_policy composite
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_policy_runs_set_mode_then_replace_channels(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    db_mock.get_policy.return_value = {"mode": "all_channels"}
    db_mock.list_allowed_channels.return_value = []
    results = await service.set_policy(
        guild_id=10,
        mode="selected_channels",
        channel_ids=[100, 200],
        actor_id=99,
    )
    # Both underlying ops fired.
    db_mock.set_mode.assert_awaited_once()
    db_mock.replace_allowed_channels.assert_awaited_once()
    assert [r.mutation_type for r in results] == [
        "set_mode",
        "replace_allowed_channels",
    ]
    # Cache invalidated twice (once per inner mutation) — that's
    # intentional: each primitive owns its own invalidation discipline.
    assert invalidate_mock.call_count == 2


@pytest.mark.asyncio
async def test_set_policy_with_none_channel_ids_skips_channel_op(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    """``channel_ids=None`` is the "change mode only, preserve channels"
    path the settings UI uses when the operator picks a new mode but
    hasn't touched the channel list.
    """
    db_mock.get_policy.return_value = None
    results = await service.set_policy(
        guild_id=10,
        mode="all_channels",
        channel_ids=None,
        actor_id=99,
    )
    db_mock.set_mode.assert_awaited_once()
    db_mock.replace_allowed_channels.assert_not_awaited()
    assert [r.mutation_type for r in results] == ["set_mode"]


@pytest.mark.asyncio
async def test_set_policy_with_empty_channel_ids_clears_list(
    db_mock,
    invalidate_mock,
    audit_mock,
):
    """``channel_ids=[]`` is "explicitly clear the list" — different
    from ``None`` (preserve).  The replace op must run, so a real audit
    row records the clear.
    """
    db_mock.get_policy.return_value = None
    db_mock.list_allowed_channels.return_value = [100, 200]
    results = await service.set_policy(
        guild_id=10,
        mode="all_channels",
        channel_ids=[],
        actor_id=99,
    )
    db_mock.replace_allowed_channels.assert_awaited_once_with(
        guild_id=10,
        channel_ids=[],
        created_by=99,
    )
    assert [r.mutation_type for r in results] == [
        "set_mode",
        "replace_allowed_channels",
    ]


# ---------------------------------------------------------------------------
# get_policy_snapshot passthrough
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_policy_snapshot_passes_through_to_typed_accessor():
    from utils.guild_config_accessors import CommandAccessPolicySnapshot

    snap = CommandAccessPolicySnapshot(
        mode="selected_channels",
        allowed_channels=frozenset({100}),
    )
    with patch.object(
        service,
        "get_command_access_policy",
        new=AsyncMock(return_value=snap),
    ) as accessor:
        result = await service.get_policy_snapshot(10)
    accessor.assert_awaited_once_with(10)
    assert result is snap


# ---------------------------------------------------------------------------
# forget_guild via core.runtime.command_access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_core_forget_guild_invalidates_cache_then_deletes_db():
    """``core.runtime.command_access.forget_guild`` must invalidate the
    cache before the DB delete — order is important because a
    concurrent read between the two steps must miss cache and then
    fall through to the post-delete DB (which returns no row → safe
    default), not hit the cache and resurrect a stale row.
    """
    from core.runtime import command_access as runtime_ca

    invalidate_call_order: list[str] = []

    def _track_invalidate(_guild_id: int) -> None:
        invalidate_call_order.append("invalidate")

    async def _track_db_forget(_guild_id: int) -> None:
        invalidate_call_order.append("db_forget")

    with (
        patch(
            "utils.guild_config_accessors.invalidate_command_access_policy",
            new=MagicMock(side_effect=_track_invalidate),
        ),
        patch(
            "utils.db.command_access.forget_guild",
            new=AsyncMock(side_effect=_track_db_forget),
        ),
    ):
        await runtime_ca.forget_guild(10)
    assert invalidate_call_order == ["invalidate", "db_forget"]
