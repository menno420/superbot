"""Phase 2b unit tests — BindingMutationPipeline contract."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.resources.status import ResourceStatus
from core.runtime.bindings import BindingValue
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
)
from services.binding_mutation import (
    EVT_BINDING_CHANGED,
    BindingKindMismatchError,
    BindingMutationPipeline,
    UnauthorizedBindingMutationError,
    UndeclaredBindingError,
    UnknownSubsystemError,
)

# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def _xp_schema():
    """Register a minimal XP schema for the duration of one test."""
    from core.runtime import subsystem_schema

    subsystem_schema._reset_for_tests()
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(
            BindingSpec(
                name="announce_channel",
                kind=BindingKind.CHANNEL,
                required=False,
                hint="",
                capability_required="xp.settings.configure",
            ),
            BindingSpec(
                name="moderator_target",
                kind=BindingKind.MEMBER,
                required=False,
                hint="",
                capability_required="xp.settings.configure",
            ),
        ),
        version=1,
    )
    subsystem_schema.register(schema)
    yield schema
    subsystem_schema._reset_for_tests()


def _admin_actor(member_id: int = 1, guild_id: int = 1):
    """Build a Member mock that passes the administrator-tier check.

    The actor must be a member of the target guild (``guild_id`` must match the
    guild passed to the pipeline) — ADR-005 authority is bound to the target guild.
    """
    member = MagicMock()
    member.id = member_id
    guild = MagicMock()
    guild.id = guild_id  # must match the target guild passed to the pipeline
    guild.owner_id = member_id
    member.guild = guild
    member.guild_permissions = MagicMock(administrator=True)
    return member


def _below_tier_actor(member_id: int = 2):
    """A member of the target guild with no elevated permissions."""
    member = MagicMock()
    member.id = member_id
    guild = MagicMock()
    guild.id = 1  # same guild as the target; denial comes from the tier check
    guild.owner_id = 999  # Different from member.id
    member.guild = guild
    member.guild_permissions = MagicMock(
        administrator=False,
        manage_guild=False,
        manage_messages=False,
        kick_members=False,
        ban_members=False,
        moderate_members=False,
    )
    member.roles = []
    return member


def _guild(guild_id: int = 1):
    g = MagicMock()
    g.id = guild_id
    return g


# ---------------------------------------------------------------------------
# Step 1: input validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_binding_rejects_unknown_subsystem(_xp_schema):
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with pytest.raises(UnknownSubsystemError, match="unknown subsystem"):
        await pipeline.set_binding(
            _guild(),
            "totally_not_a_subsystem",
            "announce_channel",
            BindingKind.CHANNEL,
            42,
            actor,
        )


@pytest.mark.asyncio
async def test_set_binding_rejects_undeclared_binding(_xp_schema):
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with pytest.raises(UndeclaredBindingError, match="not declared"):
        await pipeline.set_binding(
            _guild(),
            "xp",
            "fake_binding_name",
            BindingKind.CHANNEL,
            42,
            actor,
        )


@pytest.mark.asyncio
async def test_set_binding_rejects_wrong_kind(_xp_schema):
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with pytest.raises(BindingKindMismatchError, match="kind="):
        # announce_channel is declared as CHANNEL, caller supplies ROLE.
        await pipeline.set_binding(
            _guild(),
            "xp",
            "announce_channel",
            BindingKind.ROLE,
            42,
            actor,
        )


@pytest.mark.asyncio
async def test_set_binding_rejects_subsystem_without_schema():
    """A subsystem in SUBSYSTEMS but with no registered SubsystemSchema."""
    from core.runtime import subsystem_schema

    subsystem_schema._reset_for_tests()  # ensure no schema is registered
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with pytest.raises(UndeclaredBindingError, match="no registered SubsystemSchema"):
        await pipeline.set_binding(
            _guild(),
            "xp",  # exists in SUBSYSTEMS
            "announce_channel",
            BindingKind.CHANNEL,
            42,
            actor,
        )


# ---------------------------------------------------------------------------
# Step 2: authority validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_binding_rejects_below_tier_actor(_xp_schema):
    pipeline = BindingMutationPipeline()
    actor = _below_tier_actor()
    with pytest.raises(UnauthorizedBindingMutationError, match="administrator"):
        await pipeline.set_binding(
            _guild(),
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            42,
            actor,
        )


@pytest.mark.asyncio
async def test_set_binding_rejects_none_actor(_xp_schema):
    pipeline = BindingMutationPipeline()
    with pytest.raises(UnauthorizedBindingMutationError):
        await pipeline.set_binding(
            _guild(),
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            42,
            None,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Steps 3-7: target validation, commit, event emission
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_binding_success_writes_row_and_emits_event(_xp_schema):
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    guild = _guild()

    with (
        patch(
            "services.binding_mutation.validate_binding_target",
            AsyncMock(return_value=ResourceStatus.BOUND),
        ),
        patch(
            "services.binding_mutation.get_binding",
            AsyncMock(
                return_value=BindingValue(
                    guild_id=1,
                    subsystem="xp",
                    binding_name="announce_channel",
                    kind=BindingKind.CHANNEL,
                ),
            ),
        ),
        patch(
            "services.binding_mutation.bindings_db.upsert_with_audit",
            AsyncMock(),
        ) as mock_upsert,
        patch(
            "core.events.bus.emit",
            AsyncMock(),
        ) as mock_emit,
    ):
        result = await pipeline.set_binding(
            guild,
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            42,
            actor,
        )

    assert result.new_target_id == 42
    assert result.new_status is ResourceStatus.BOUND
    assert result.event_emitted is True
    mock_upsert.assert_awaited_once()
    # Phase 9c.2: binding_mutation now also emits the companion
    # ``audit.action_recorded`` event. Filter by topic so this test
    # stays focused on EVT_BINDING_CHANGED.
    binding_emits = [
        c
        for c in mock_emit.await_args_list
        if c.args and c.args[0] == EVT_BINDING_CHANGED
    ]
    assert len(binding_emits) == 1
    assert "mutation_id" in binding_emits[0].kwargs
    assert result.mutation_id == binding_emits[0].kwargs["mutation_id"]
    # And the companion audit event fires with matching mutation_id.
    audit_emits = [
        c
        for c in mock_emit.await_args_list
        if c.args and c.args[0] == "audit.action_recorded"
    ]
    assert len(audit_emits) == 1
    assert audit_emits[0].kwargs["mutation_id"] == result.mutation_id


@pytest.mark.asyncio
async def test_set_binding_missing_target_writes_row_no_exception(_xp_schema):
    """A missing target still writes the row (with status=MISSING) so the
    diagnostics layer can surface it; mutation succeeds, only the
    validation result reflects the gap."""
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with (
        patch(
            "services.binding_mutation.validate_binding_target",
            AsyncMock(return_value=ResourceStatus.MISSING),
        ),
        patch(
            "services.binding_mutation.get_binding",
            AsyncMock(
                return_value=BindingValue(
                    guild_id=1,
                    subsystem="xp",
                    binding_name="announce_channel",
                    kind=BindingKind.CHANNEL,
                ),
            ),
        ),
        patch(
            "services.binding_mutation.bindings_db.upsert_with_audit",
            AsyncMock(),
        ) as mock_upsert,
        patch(
            "core.events.bus.emit",
            AsyncMock(),
        ),
    ):
        result = await pipeline.set_binding(
            _guild(),
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            42,
            actor,
        )

    assert result.new_status is ResourceStatus.MISSING
    mock_upsert.assert_awaited_once()
    # The upsert receives status='missing' so the diagnostic surface
    # has the right state.
    assert mock_upsert.await_args.kwargs["status"] == "missing"


@pytest.mark.asyncio
async def test_set_binding_event_emit_failure_does_not_undo_commit(_xp_schema):
    """If event emission raises after a successful DB commit, the DB
    state is preserved and the failure is logged but not re-raised."""
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with (
        patch(
            "services.binding_mutation.validate_binding_target",
            AsyncMock(return_value=ResourceStatus.BOUND),
        ),
        patch(
            "services.binding_mutation.get_binding",
            AsyncMock(
                return_value=BindingValue(
                    guild_id=1,
                    subsystem="xp",
                    binding_name="announce_channel",
                    kind=BindingKind.CHANNEL,
                ),
            ),
        ),
        patch(
            "services.binding_mutation.bindings_db.upsert_with_audit",
            AsyncMock(),
        ) as mock_upsert,
        patch(
            "core.events.bus.emit",
            AsyncMock(side_effect=RuntimeError("bus down")),
        ),
    ):
        result = await pipeline.set_binding(
            _guild(),
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            42,
            actor,
        )

    mock_upsert.assert_awaited_once()
    assert result.event_emitted is False
    assert result.new_status is ResourceStatus.BOUND


@pytest.mark.asyncio
async def test_set_binding_db_failure_skips_event_emission(_xp_schema):
    """If the DB write raises, the failure propagates and the event is
    not emitted — the DB is the source of truth for emission."""
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with (
        patch(
            "services.binding_mutation.validate_binding_target",
            AsyncMock(return_value=ResourceStatus.BOUND),
        ),
        patch(
            "services.binding_mutation.get_binding",
            AsyncMock(
                return_value=BindingValue(
                    guild_id=1,
                    subsystem="xp",
                    binding_name="announce_channel",
                    kind=BindingKind.CHANNEL,
                ),
            ),
        ),
        patch(
            "services.binding_mutation.bindings_db.upsert_with_audit",
            AsyncMock(side_effect=RuntimeError("db down")),
        ),
        patch(
            "core.events.bus.emit",
            AsyncMock(),
        ) as mock_emit,
    ):
        with pytest.raises(RuntimeError, match="db down"):
            await pipeline.set_binding(
                _guild(),
                "xp",
                "announce_channel",
                BindingKind.CHANNEL,
                42,
                actor,
            )

    mock_emit.assert_not_called()


@pytest.mark.asyncio
async def test_set_binding_member_kind_uses_member_resolver(_xp_schema):
    """Phase 2b design decision: MEMBER bindings dispatch to the member
    resolver path; the resource cache is not touched.

    Validates the end-to-end pipeline for a non-resource kind.
    """
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    sentinel_member = object()
    with (
        patch(
            "core.runtime.bindings.guild_resources.resolve_member",
            return_value=sentinel_member,
        ) as mock_resolve,
        patch(
            "core.runtime.bindings.discovery.validate_resource",
            AsyncMock(),
        ) as mock_validate_resource,
        patch(
            "services.binding_mutation.get_binding",
            AsyncMock(
                return_value=BindingValue(
                    guild_id=1,
                    subsystem="xp",
                    binding_name="moderator_target",
                    kind=BindingKind.MEMBER,
                ),
            ),
        ),
        patch(
            "services.binding_mutation.bindings_db.upsert_with_audit",
            AsyncMock(),
        ),
        patch(
            "core.events.bus.emit",
            AsyncMock(),
        ),
    ):
        result = await pipeline.set_binding(
            _guild(),
            "xp",
            "moderator_target",
            BindingKind.MEMBER,
            777,
            actor,
        )

    assert result.new_status is ResourceStatus.BOUND
    mock_resolve.assert_called_once()
    mock_validate_resource.assert_not_called()


# ---------------------------------------------------------------------------
# clear_binding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_binding_idempotent_when_no_row_exists(_xp_schema):
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with (
        patch(
            "services.binding_mutation.get_binding",
            AsyncMock(
                return_value=BindingValue(
                    guild_id=1,
                    subsystem="xp",
                    binding_name="announce_channel",
                    kind=BindingKind.CHANNEL,
                ),
            ),
        ),
        patch(
            "services.binding_mutation.bindings_db.clear_with_audit",
            AsyncMock(),
        ) as mock_clear,
        patch(
            "core.events.bus.emit",
            AsyncMock(),
        ) as mock_emit,
    ):
        result = await pipeline.clear_binding(
            _guild(),
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            actor,
        )

    assert result.new_status is ResourceStatus.UNRESOLVED
    # Idempotent: clearing an already-clear slot does not touch DB or events.
    mock_clear.assert_not_called()
    mock_emit.assert_not_called()


@pytest.mark.asyncio
async def test_clear_binding_writes_and_emits_when_bound(_xp_schema):
    from datetime import datetime, timezone

    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with (
        patch(
            "services.binding_mutation.get_binding",
            AsyncMock(
                return_value=BindingValue(
                    guild_id=1,
                    subsystem="xp",
                    binding_name="announce_channel",
                    kind=BindingKind.CHANNEL,
                    target_id=42,
                    status=ResourceStatus.BOUND,
                    last_updated_at=datetime.now(timezone.utc),
                    version=3,
                ),
            ),
        ),
        patch(
            "services.binding_mutation.bindings_db.clear_with_audit",
            AsyncMock(),
        ) as mock_clear,
        patch(
            "core.events.bus.emit",
            AsyncMock(),
        ) as mock_emit,
    ):
        result = await pipeline.clear_binding(
            _guild(),
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            actor,
        )

    assert result.old_target_id == 42
    assert result.new_target_id is None
    assert result.new_status is ResourceStatus.UNRESOLVED
    mock_clear.assert_awaited_once()
    # Phase 9c.2: clear_binding now also emits ``audit.action_recorded``.
    binding_emits = [
        c
        for c in mock_emit.await_args_list
        if c.args and c.args[0] == EVT_BINDING_CHANGED
    ]
    audit_emits = [
        c
        for c in mock_emit.await_args_list
        if c.args and c.args[0] == "audit.action_recorded"
    ]
    assert len(binding_emits) == 1
    assert len(audit_emits) == 1
    assert audit_emits[0].kwargs["mutation_id"] == result.mutation_id


@pytest.mark.asyncio
async def test_clear_binding_rejects_below_tier_actor(_xp_schema):
    pipeline = BindingMutationPipeline()
    actor = _below_tier_actor()
    with pytest.raises(UnauthorizedBindingMutationError):
        await pipeline.clear_binding(
            _guild(),
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            actor,
        )


# ---------------------------------------------------------------------------
# M1 — AI audit_log_channel binding flows through the pipeline
# ---------------------------------------------------------------------------


@pytest.fixture
def _ai_schema():
    """Register the real AI_CONFIG_SCHEMA for one test.

    Mirrors the ``_xp_schema`` fixture but uses the actual M1 schema
    so the test exercises the same BindingSpec the runtime sees.
    """
    from core.runtime import subsystem_schema

    saved = subsystem_schema.all_schemas()
    subsystem_schema._reset_for_tests()
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    subsystem_schema.register(AI_CONFIG_SCHEMA)
    yield AI_CONFIG_SCHEMA
    subsystem_schema._reset_for_tests()
    for schema in saved.values():
        subsystem_schema.register(schema)


@pytest.mark.asyncio
async def test_set_ai_audit_log_channel_binding_writes_through_pipeline(_ai_schema):
    """The M1 AI audit-channel binding is the canonical owner.

    A successful write must produce a BindingValue with the right
    kind, invoke ``upsert_with_audit`` once, and emit
    EVT_BINDING_CHANGED. Pinned so the M2 work does not bypass this
    pipeline by adding an audit_log_channel_id column to
    ai_guild_policy.
    """
    pipeline = BindingMutationPipeline()
    actor = _admin_actor(guild_id=999)
    guild = _guild(guild_id=999)

    with (
        patch(
            "services.binding_mutation.validate_binding_target",
            AsyncMock(return_value=ResourceStatus.BOUND),
        ),
        patch(
            "services.binding_mutation.get_binding",
            AsyncMock(
                return_value=BindingValue(
                    guild_id=999,
                    subsystem="ai",
                    binding_name="audit_log_channel",
                    kind=BindingKind.CHANNEL,
                ),
            ),
        ),
        patch(
            "services.binding_mutation.bindings_db.upsert_with_audit",
            AsyncMock(),
        ) as mock_upsert,
        patch(
            "core.events.bus.emit",
            AsyncMock(),
        ) as mock_emit,
    ):
        result = await pipeline.set_binding(
            guild,
            "ai",
            "audit_log_channel",
            BindingKind.CHANNEL,
            5555,
            actor,
        )

    assert result.new_target_id == 5555
    assert result.new_status is ResourceStatus.BOUND
    assert result.event_emitted is True
    mock_upsert.assert_awaited_once()

    binding_emits = [
        c
        for c in mock_emit.await_args_list
        if c.args and c.args[0] == EVT_BINDING_CHANGED
    ]
    assert len(binding_emits) == 1
    assert binding_emits[0].kwargs.get("subsystem") == "ai"
    assert binding_emits[0].kwargs.get("binding_name") == "audit_log_channel"


@pytest.mark.asyncio
async def test_set_ai_binding_rejects_undeclared_name(_ai_schema):
    """A binding that does not appear in AI_CONFIG_SCHEMA must be
    rejected before any DB write — the schema is the contract."""
    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    with pytest.raises(UndeclaredBindingError):
        await pipeline.set_binding(
            _guild(),
            "ai",
            "audit_log_channel_id",  # M2-style typo, must be rejected
            BindingKind.CHANNEL,
            42,
            actor,
        )


# ---------------------------------------------------------------------------
# No-cache contract: committed writes are immediately visible to readers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_and_clear_visible_to_reads_without_invalidation(_xp_schema):
    """Cache observation across set/clear: there is nothing to invalidate.

    The pipeline deliberately has no cache-invalidation step (module
    docstring): binding reads (``core.runtime.bindings.get_binding``) hit
    the DB on every call. Simulate the DB row store under the mocked
    primitives and verify a reader observes each commit immediately —
    the property that makes the missing step correct. If a binding read
    cache is ever introduced, this test must change to observe explicit
    post-commit invalidation.
    """
    from core.runtime.bindings import get_binding as read_binding

    store: dict[tuple[int, str, str], dict] = {}

    async def fake_get_one(guild_id, subsystem, binding_name):
        return store.get((guild_id, subsystem, binding_name))

    async def fake_upsert(**kw):
        from datetime import datetime, timezone

        key = (kw["guild_id"], kw["subsystem"], kw["binding_name"])
        prev = store.get(key)
        store[key] = {
            "guild_id": kw["guild_id"],
            "subsystem": kw["subsystem"],
            "binding_name": kw["binding_name"],
            "kind": kw["kind"],
            "target_id": kw["target_id"],
            "status": kw["status"],
            "last_validated_at": None,
            "last_updated_at": datetime.now(timezone.utc),
            "version": (prev["version"] + 1) if prev else 1,
        }

    async def fake_clear(**kw):
        from datetime import datetime, timezone

        key = (kw["guild_id"], kw["subsystem"], kw["binding_name"])
        row = store[key]
        row["target_id"] = None
        row["status"] = "unresolved"
        row["last_updated_at"] = datetime.now(timezone.utc)
        row["version"] += 1

    pipeline = BindingMutationPipeline()
    actor = _admin_actor()
    guild = _guild()

    with (
        patch(
            "core.runtime.bindings.bindings_db.get_one",
            AsyncMock(side_effect=fake_get_one),
        ),
        patch(
            "services.binding_mutation.bindings_db.upsert_with_audit",
            AsyncMock(side_effect=fake_upsert),
        ),
        patch(
            "services.binding_mutation.bindings_db.clear_with_audit",
            AsyncMock(side_effect=fake_clear),
        ),
        patch(
            "services.binding_mutation.validate_binding_target",
            AsyncMock(return_value=ResourceStatus.BOUND),
        ),
        patch(
            "core.events.bus.emit",
            AsyncMock(),
        ),
    ):
        # Never bound: a reader sees the unresolved default.
        before = await read_binding(1, "xp", "announce_channel")
        assert before.target_id is None
        assert before.status is ResourceStatus.UNRESOLVED

        # set → the very next uncached read sees the committed target.
        await pipeline.set_binding(
            guild,
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            42,
            actor,
        )
        after_set = await read_binding(1, "xp", "announce_channel")
        assert after_set.target_id == 42
        assert after_set.status is ResourceStatus.BOUND

        # clear → the very next uncached read sees the cleared slot
        # (last_updated_at survives, distinguishing cleared from never-bound).
        await pipeline.clear_binding(
            guild,
            "xp",
            "announce_channel",
            BindingKind.CHANNEL,
            actor,
        )
        after_clear = await read_binding(1, "xp", "announce_channel")
        assert after_clear.target_id is None
        assert after_clear.status is ResourceStatus.UNRESOLVED
        assert after_clear.last_updated_at is not None
