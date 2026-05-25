"""Unit tests for services.settings_mutation — S4.

Covers the 11-step pipeline contract: spec resolution, every error
class, actor / authority validation, coercion + validator hooks,
read-previous-value integration with S3's resolver, the
DB-write + audit transaction, cache invalidation, best-effort
event emission, and the typed result type.

The DB layer (utils.db.settings_audit) is monkeypatched to an
in-memory store so the tests never touch a real database.
"""

from __future__ import annotations

import pytest

from core.runtime import guild_config
from core.runtime import subsystem_schema as schema_mod
from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema
from services import settings_mutation as sm_mod
from services import settings_resolution as sr_mod
from services.settings_mutation import (
    EVT_SETTINGS_CHANGED,
    InvalidActorTypeError,
    SettingsCoercionError,
    SettingsMutationPipeline,
    SettingsMutationResult,
    SettingsValidationError,
    UnauthorizedSettingsMutationError,
    UndeclaredSettingError,
    UnknownSubsystemError,
    UnmigrateableSettingError,
)
from utils import db as db_pkg
from utils.db import settings as settings_db
from utils.db import settings_audit as audit_db

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeGuild:
    def __init__(self, guild_id: int, *, owner_id: int = 0):
        self.id = guild_id
        self.owner_id = owner_id


class _FakeGuildPermissions:
    def __init__(
        self,
        *,
        administrator: bool = False,
        moderate_members: bool = False,
        manage_guild: bool = False,
    ):
        self.administrator = administrator
        self.moderate_members = moderate_members
        self.manage_guild = manage_guild


class _FakeMember:
    def __init__(
        self,
        member_id: int,
        *,
        guild: _FakeGuild,
        tier: str = "administrator",
    ):
        self.id = member_id
        self.guild = guild
        perms = _FakeGuildPermissions()
        if tier == "administrator":
            perms.administrator = True
        elif tier == "moderator":
            perms.moderate_members = True
        elif tier == "staff":
            perms.manage_guild = True
        # "user" — no perms; matches Discord default member
        self.guild_permissions = perms


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch):
    """Snapshot live schema registry and DB stubs around each test."""
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    sr_mod._reset_counters_for_tests()
    guild_config._reset_for_tests()

    # In-memory legacy KV store.  Tests pre-populate `_kv` to seed
    # previous values; the pipeline's DB-write stub also pushes here.
    _kv: dict[tuple[int, str], str] = {}

    async def _fake_get_setting(
        guild_id: int,
        key: str,
        default: str = "",
    ) -> str:
        return _kv.get((guild_id, key), default)

    monkeypatch.setattr(settings_db, "get_setting", _fake_get_setting)
    monkeypatch.setattr(db_pkg, "get_setting", _fake_get_setting)

    # Audit DB stub: record every set_value_with_audit call AND
    # update the in-memory KV so resolve_setting reflects post-write
    # state on the next call.
    audit_log: list[dict] = []

    async def _fake_set_value_with_audit(
        *,
        guild_id: int,
        subsystem: str,
        name: str,
        settings_key: str,
        prev_value_raw: str | None,
        new_value_raw: str,
        actor_id: int | None,
        actor_type: str,
        mutation_id: str,
        mutation_type: str = "set_value",
    ) -> None:
        _kv[(guild_id, settings_key)] = new_value_raw
        audit_log.append(
            {
                "guild_id": guild_id,
                "subsystem": subsystem,
                "name": name,
                "settings_key": settings_key,
                "prev_value_raw": prev_value_raw,
                "new_value_raw": new_value_raw,
                "actor_id": actor_id,
                "actor_type": actor_type,
                "mutation_id": mutation_id,
                "mutation_type": mutation_type,
            },
        )

    monkeypatch.setattr(audit_db, "set_value_with_audit", _fake_set_value_with_audit)

    # Cache invalidation tracker.
    invalidations: list[tuple[int, str]] = []
    from utils import guild_config_accessors

    real_invalidate = guild_config_accessors.invalidate_setting_value

    def _tracked_invalidate(guild_id: int, settings_key: str) -> None:
        invalidations.append((guild_id, settings_key))
        real_invalidate(guild_id, settings_key)

    monkeypatch.setattr(
        guild_config_accessors,
        "invalidate_setting_value",
        _tracked_invalidate,
    )

    # Event bus stub.
    emitted: list[dict] = []
    bus_raises: dict[str, bool] = {"flag": False}

    async def _fake_emit(event: str, /, **payload):
        if bus_raises["flag"]:
            raise RuntimeError("simulated bus failure")
        emitted.append({"event": event, **payload})

    from core.events import bus

    monkeypatch.setattr(bus, "emit", _fake_emit)

    # AI projection stub — the post-PR-#310 hardening adds an inline
    # ai_policy_mutation.project_from_legacy_settings call inside the
    # pipeline for subsystem='ai'. Stub it so these unit tests stay
    # focused on the pipeline contract; a dedicated test file pins the
    # projection behaviour.
    projection_calls: list[dict] = []
    from services import ai_policy_mutation

    async def _fake_projection(
        guild_id: int,
        actor: object,
        *,
        mutation_id: str,
    ) -> object:
        projection_calls.append(
            {
                "guild_id": guild_id,
                "actor_id": getattr(actor, "id", None),
                "mutation_id": mutation_id,
            },
        )
        return None

    monkeypatch.setattr(
        ai_policy_mutation,
        "project_from_legacy_settings",
        _fake_projection,
    )

    yield {
        "kv": _kv,
        "audit_log": audit_log,
        "invalidations": invalidations,
        "emitted": emitted,
        "bus_raises": bus_raises,
        "projection_calls": projection_calls,
    }

    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    sr_mod._reset_counters_for_tests()
    guild_config._reset_for_tests()


def _register(subsystem: str, *specs: SettingSpec) -> None:
    schema_mod.register(SubsystemSchema(subsystem=subsystem, settings=specs))


# ---------------------------------------------------------------------------
# Step 1-2: spec resolution + unknown subsystem / setting / unmigrateable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_subsystem_raises():
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(UnknownSubsystemError):
        await pipeline.set_value(guild, "no_such_subsystem", "x", 1, actor)


@pytest.mark.asyncio
async def test_undeclared_setting_raises_when_subsystem_has_no_schema():
    """When the subsystem exists in SUBSYSTEMS but has no SubsystemSchema
    registered, the pipeline raises UndeclaredSettingError."""
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(UndeclaredSettingError):
        await pipeline.set_value(guild, "xp", "whatever", 1, actor)


@pytest.mark.asyncio
async def test_undeclared_setting_raises_when_name_not_in_schema():
    _register("xp", SettingSpec(name="xp_min", value_type=int, default=1))
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(UndeclaredSettingError):
        await pipeline.set_value(guild, "xp", "no_such_setting", 1, actor)


@pytest.mark.asyncio
async def test_unmigrateable_setting_raises_when_settings_key_empty():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1),
        # No settings_key — transitional state.
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(UnmigrateableSettingError):
        await pipeline.set_value(guild, "xp", "xp_min", 5, actor)


# ---------------------------------------------------------------------------
# Step 3: actor / authority validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_actor_type_raises():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(InvalidActorTypeError):
        await pipeline.set_value(
            guild,
            "xp",
            "xp_min",
            5,
            actor,
            actor_type="god_mode",
        )


@pytest.mark.asyncio
async def test_unauthorized_when_actor_missing_for_user_actor_type():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(UnauthorizedSettingsMutationError):
        await pipeline.set_value(guild, "xp", "xp_min", 5, None)


@pytest.mark.asyncio
async def test_unauthorized_when_actor_below_admin_tier():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild, tier="staff")
    pipeline = SettingsMutationPipeline()
    with pytest.raises(UnauthorizedSettingsMutationError):
        await pipeline.set_value(guild, "xp", "xp_min", 5, actor)


@pytest.mark.asyncio
async def test_admin_tier_actor_allowed():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild, tier="administrator")
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "xp", "xp_min", 5, actor)
    assert result.new_value == 5


@pytest.mark.asyncio
async def test_system_actor_bypasses_authority_check():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    pipeline = SettingsMutationPipeline()
    # No member — system writes are allowed without an actor.
    result = await pipeline.set_value(
        guild,
        "xp",
        "xp_min",
        5,
        None,
        actor_type="system",
    )
    assert result.new_value == 5
    assert result.event_emitted is True


@pytest.mark.asyncio
async def test_backfill_actor_bypasses_authority_check():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(
        guild,
        "xp",
        "xp_min",
        5,
        None,
        actor_type="backfill",
    )
    assert result.new_value == 5


# ---------------------------------------------------------------------------
# Steps 4-5: coercion + validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_int_coercion_from_string():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "xp", "xp_min", "42", actor)
    assert result.new_value == 42
    assert result.new_value_raw == "42"


@pytest.mark.asyncio
async def test_int_coercion_from_already_typed():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "xp", "xp_min", 42, actor)
    assert result.new_value == 42
    assert result.new_value_raw == "42"


@pytest.mark.asyncio
async def test_bool_coercion_serialises_to_true_false():
    _register(
        "moderation",
        SettingSpec(
            name="dm_on_action",
            value_type=bool,
            default=False,
            settings_key="MOD_DM_ON_ACTION",
        ),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "moderation", "dm_on_action", True, actor)
    assert result.new_value is True
    assert result.new_value_raw == "true"


@pytest.mark.asyncio
async def test_bool_coercion_from_string_synonym():
    _register(
        "moderation",
        SettingSpec(
            name="dm_on_action",
            value_type=bool,
            default=False,
            settings_key="MOD_DM_ON_ACTION",
        ),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "moderation", "dm_on_action", "yes", actor)
    assert result.new_value is True
    assert result.new_value_raw == "true"


@pytest.mark.asyncio
async def test_coercion_failure_raises():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(SettingsCoercionError):
        await pipeline.set_value(guild, "xp", "xp_min", "abc", actor)


@pytest.mark.asyncio
async def test_validator_value_error_raises():
    def _v(value):
        if value < 0:
            raise ValueError("must be non-negative")

    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            settings_key="XP_MIN",
            validator=_v,
        ),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(SettingsValidationError):
        await pipeline.set_value(guild, "xp", "xp_min", -5, actor)


@pytest.mark.asyncio
async def test_validator_type_error_raises():
    def _v(value):  # noqa: ARG001
        raise TypeError("bad shape")

    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            settings_key="XP_MIN",
            validator=_v,
        ),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(SettingsValidationError):
        await pipeline.set_value(guild, "xp", "xp_min", 5, actor)


# ---------------------------------------------------------------------------
# Step 6: read-previous-value integration with S3 resolver
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_previous_value_captured_when_no_kv_row(_isolated_state):
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=15, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "xp", "xp_min", 42, actor)
    # No prior KV row, so old_value is the default and old_value_raw is None.
    assert result.old_value == 15
    assert result.old_value_raw is None
    # Audit row records None for prev_value_raw.
    audit = _isolated_state["audit_log"][0]
    assert audit["prev_value_raw"] is None
    assert audit["new_value_raw"] == "42"


@pytest.mark.asyncio
async def test_previous_value_captured_from_existing_kv_row(_isolated_state):
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=15, settings_key="XP_MIN"),
    )
    _isolated_state["kv"][(1, "XP_MIN")] = "20"
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "xp", "xp_min", 42, actor)
    assert result.old_value == 20
    assert result.old_value_raw == "20"
    assert result.new_value == 42
    audit = _isolated_state["audit_log"][0]
    assert audit["prev_value_raw"] == "20"
    assert audit["new_value_raw"] == "42"


# ---------------------------------------------------------------------------
# Steps 7-9: DB write + audit + cache invalidation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_row_records_subsystem_name_settings_key(_isolated_state):
    _register(
        "moderation",
        SettingSpec(
            name="warn_threshold",
            value_type=int,
            default=3,
            settings_key="WARN_THRESHOLD",
            capability_required="moderation.settings.configure",
        ),
    )
    guild = _FakeGuild(42)
    actor = _FakeMember(99, guild=guild)
    pipeline = SettingsMutationPipeline()
    await pipeline.set_value(guild, "moderation", "warn_threshold", 5, actor)
    audit = _isolated_state["audit_log"][0]
    assert audit["guild_id"] == 42
    assert audit["subsystem"] == "moderation"
    assert audit["name"] == "warn_threshold"
    assert audit["settings_key"] == "WARN_THRESHOLD"
    assert audit["actor_id"] == 99
    assert audit["actor_type"] == "user"
    assert audit["mutation_type"] == "set_value"
    # mutation_id is a UUID string.
    assert len(audit["mutation_id"]) == 36


@pytest.mark.asyncio
async def test_audit_row_actor_id_is_none_for_system(_isolated_state):
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    pipeline = SettingsMutationPipeline()
    await pipeline.set_value(guild, "xp", "xp_min", 5, None, actor_type="system")
    audit = _isolated_state["audit_log"][0]
    assert audit["actor_id"] is None
    assert audit["actor_type"] == "system"


@pytest.mark.asyncio
async def test_cache_invalidated_with_settings_key(_isolated_state):
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    await pipeline.set_value(guild, "xp", "xp_min", 5, actor)
    assert (1, "XP_MIN") in _isolated_state["invalidations"]


@pytest.mark.asyncio
async def test_db_failure_skips_cache_and_event(_isolated_state, monkeypatch):
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )

    async def _raises(**_kw):
        raise RuntimeError("DB unavailable")

    monkeypatch.setattr(audit_db, "set_value_with_audit", _raises)
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    with pytest.raises(RuntimeError):
        await pipeline.set_value(guild, "xp", "xp_min", 5, actor)
    # Neither side effect should fire when the DB write fails.
    assert _isolated_state["invalidations"] == []
    assert _isolated_state["emitted"] == []


# ---------------------------------------------------------------------------
# Step 10: event emission (best-effort)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_emitted_with_full_payload(_isolated_state):
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "xp", "xp_min", 5, actor)
    # Phase 9c.2: settings_mutation now also emits the companion
    # ``audit.action_recorded`` event via the shared publisher. Filter
    # by topic so the test stays focused on EVT_SETTINGS_CHANGED.
    settings_emits = [
        e for e in _isolated_state["emitted"] if e["event"] == EVT_SETTINGS_CHANGED
    ]
    assert len(settings_emits) == 1
    payload = settings_emits[0]
    assert payload["guild_id"] == 1
    assert payload["subsystem"] == "xp"
    assert payload["name"] == "xp_min"
    assert payload["settings_key"] == "XP_MIN"
    assert payload["old_value_raw"] is None
    assert payload["new_value_raw"] == "5"
    assert payload["mutation_id"] == result.mutation_id
    assert "occurred_at" in payload
    assert result.event_emitted is True
    # And the companion audit event fires with matching mutation_id.
    audit_emits = [
        e for e in _isolated_state["emitted"] if e["event"] == "audit.action_recorded"
    ]
    assert len(audit_emits) == 1
    assert audit_emits[0]["mutation_id"] == result.mutation_id


@pytest.mark.asyncio
async def test_event_emission_failure_swallowed(_isolated_state):
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    _isolated_state["bus_raises"]["flag"] = True
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    # Mutation must still succeed; only event_emitted=False.
    result = await pipeline.set_value(guild, "xp", "xp_min", 5, actor)
    assert result.event_emitted is False
    assert result.new_value == 5
    # DB write + cache invalidation still happened.
    assert len(_isolated_state["audit_log"]) == 1
    assert (1, "XP_MIN") in _isolated_state["invalidations"]


# ---------------------------------------------------------------------------
# Step 11: typed result + invariants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_is_frozen():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, "xp", "xp_min", 5, actor)
    assert isinstance(result, SettingsMutationResult)
    with pytest.raises(Exception):
        result.new_value = 99  # type: ignore[misc]


@pytest.mark.asyncio
async def test_each_mutation_gets_distinct_id(_isolated_state):
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = SettingsMutationPipeline()
    r1 = await pipeline.set_value(guild, "xp", "xp_min", 5, actor)
    r2 = await pipeline.set_value(guild, "xp", "xp_min", 10, actor)
    assert r1.mutation_id != r2.mutation_id
    assert len(_isolated_state["audit_log"]) == 2
    # Second mutation captures the first as old_value_raw.
    assert _isolated_state["audit_log"][1]["prev_value_raw"] == "5"


@pytest.mark.asyncio
async def test_pipeline_is_stateless():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    # Two separate instances behave identically.
    r1 = await SettingsMutationPipeline().set_value(guild, "xp", "xp_min", 5, actor)
    r2 = await SettingsMutationPipeline().set_value(guild, "xp", "xp_min", 10, actor)
    assert r1.new_value == 5
    assert r2.new_value == 10


# ---------------------------------------------------------------------------
# Catalogue + event invariants
# ---------------------------------------------------------------------------


def test_event_name_registered_in_catalogue():
    from core.events_catalogue import KNOWN_EVENTS

    assert EVT_SETTINGS_CHANGED in KNOWN_EVENTS


def test_feature_flag_is_declared_and_default_off():
    from core.runtime.feature_flags import SETTINGS_MUTATION_PRIMARY

    assert SETTINGS_MUTATION_PRIMARY.name == "settings.mutation.primary"
    assert SETTINGS_MUTATION_PRIMARY.default_value is False


def test_actor_type_allowlist_matches_documented_set():
    """The pipeline's allowed actor_type set must match the migration's
    CHECK constraint.  The alignment test does the SQL side; this test
    pins the Python side to a fixed shape so future changes are
    intentional."""
    assert sm_mod._ALLOWED_ACTOR_TYPES == frozenset(
        {"user", "moderator", "admin", "system", "backfill"},
    )


def test_mutation_type_allowlist_is_set_value_only_in_v1():
    assert sm_mod._ALLOWED_MUTATION_TYPES == frozenset({"set_value"})


# ---------------------------------------------------------------------------
# M1 — AI subsystem scalars flow through the pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ai_minimum_level_default_writes_through_pipeline(_isolated_state):
    """The AI_CONFIG_SCHEMA setting routes through SettingsMutationPipeline
    with the right audit row, cache invalidation, and event payload.
    """
    from cogs.ai.schemas import AI_CONFIG_SCHEMA
    from utils.settings_keys import AI_MINIMUM_LEVEL_DEFAULT

    schema_mod.register(AI_CONFIG_SCHEMA)
    guild = _FakeGuild(101)
    actor = _FakeMember(202, guild=guild)

    result = await SettingsMutationPipeline().set_value(
        guild,
        "ai",
        "ai_minimum_level_default",
        5,
        actor,
    )

    assert isinstance(result, SettingsMutationResult)
    assert result.new_value == 5
    assert _isolated_state["kv"][(101, AI_MINIMUM_LEVEL_DEFAULT)] == "5"
    assert (101, AI_MINIMUM_LEVEL_DEFAULT) in _isolated_state["invalidations"]
    assert _isolated_state["audit_log"][-1]["subsystem"] == "ai"
    assert _isolated_state["audit_log"][-1]["settings_key"] == AI_MINIMUM_LEVEL_DEFAULT
    assert _isolated_state["emitted"][-1]["event"] == EVT_SETTINGS_CHANGED


@pytest.mark.asyncio
async def test_ai_natural_language_enabled_bool_round_trip(_isolated_state):
    """The bool scalar coerces through the pipeline as 'true' / 'false'.

    Pinned because the natural-language stage (M2) reads this value
    via the typed-resolver path and stays at the conservative default
    until the operator opts in.
    """
    from cogs.ai.schemas import AI_CONFIG_SCHEMA
    from utils.settings_keys import AI_NATURAL_LANGUAGE_ENABLED

    schema_mod.register(AI_CONFIG_SCHEMA)
    guild = _FakeGuild(303)
    actor = _FakeMember(404, guild=guild)

    result = await SettingsMutationPipeline().set_value(
        guild,
        "ai",
        "ai_natural_language_enabled",
        True,
        actor,
    )

    assert result.new_value is True
    assert _isolated_state["kv"][(303, AI_NATURAL_LANGUAGE_ENABLED)] == "true"
    assert (303, AI_NATURAL_LANGUAGE_ENABLED) in _isolated_state["invalidations"]
    assert _isolated_state["audit_log"][-1]["subsystem"] == "ai"
    assert _isolated_state["audit_log"][-1]["new_value_raw"] == "true"


@pytest.mark.asyncio
async def test_ai_subsystem_mutation_triggers_typed_policy_projection(
    _isolated_state,
):
    """Post-PR-#310 hardening: every projectable AI scalar mutation
    invokes ``ai_policy_mutation.project_from_legacy_settings`` with
    the live ``mutation_id`` so the typed policy stays in sync."""
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    schema_mod.register(AI_CONFIG_SCHEMA)
    guild = _FakeGuild(505)
    actor = _FakeMember(606, guild=guild)

    result = await SettingsMutationPipeline().set_value(
        guild,
        "ai",
        "ai_enabled",
        True,
        actor,
    )

    calls = _isolated_state["projection_calls"]
    assert len(calls) == 1, "expected exactly one projection call"
    assert calls[0]["guild_id"] == 505
    assert calls[0]["actor_id"] == 606
    assert calls[0]["mutation_id"] == result.mutation_id


@pytest.mark.asyncio
async def test_non_ai_subsystem_does_not_trigger_projection(_isolated_state):
    """Projection is gated on ``subsystem='ai'`` — other subsystems
    must NOT trigger the AI policy mutation chokepoint."""
    from cogs.xp.schemas import XP_CONFIG_SCHEMA

    schema_mod.register(XP_CONFIG_SCHEMA)
    guild = _FakeGuild(707)
    actor = _FakeMember(808, guild=guild)

    # Pick any XP scalar; the exact value doesn't matter.
    await SettingsMutationPipeline().set_value(
        guild,
        "xp",
        "xp_min",
        7,
        actor,
    )

    assert _isolated_state["projection_calls"] == []
