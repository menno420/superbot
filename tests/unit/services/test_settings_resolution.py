"""Unit tests for services.settings_resolution — S3.

Covers the resolver, all coercion paths (int / str / bool / float),
default vs legacy_kv provenance, the validator hook, the batch
helper, counters, immutability, and the diagnostics provider.
"""

from __future__ import annotations

import pytest

from core.runtime import guild_config
from core.runtime import subsystem_schema as schema_mod
from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema
from services import settings_resolution as sr_mod
from services.settings_resolution import (
    SettingResolution,
    counters_snapshot,
    resolve_batch,
    resolve_setting,
    resolve_value,
)
from utils import db as db_pkg
from utils.db import settings as settings_db

# ---------------------------------------------------------------------------
# Fixtures — snapshot live module state around each test to stay isolated.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    sr_mod._reset_counters_for_tests()
    guild_config._reset_for_tests()

    # Replace the legacy KV read with an in-memory store so tests don't
    # touch the DB. Tests populate `_kv` to control what get_setting
    # returns. The same store is used to verify caching.
    _kv: dict[tuple[int, str], str] = {}
    fetch_counter = {"calls": 0}

    async def _fake_get_setting(
        guild_id: int,
        key: str,
        default: str = "",
    ) -> str:
        fetch_counter["calls"] += 1
        return _kv.get((guild_id, key), default)

    # Patch the function at every binding site — `utils.db.__init__`
    # re-exports `get_setting` from `utils.db.settings`, so patching only
    # the source module leaves the re-exported reference unchanged.
    monkeypatch.setattr(settings_db, "get_setting", _fake_get_setting)
    monkeypatch.setattr(db_pkg, "get_setting", _fake_get_setting)

    yield {"kv": _kv, "fetches": fetch_counter}

    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    sr_mod._reset_counters_for_tests()
    guild_config._reset_for_tests()


def _register(subsystem: str, *specs: SettingSpec) -> None:
    schema_mod.register(SubsystemSchema(subsystem=subsystem, settings=specs))


# ---------------------------------------------------------------------------
# Unknown spec → None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_subsystem_returns_none():
    result = await resolve_setting(1, "no_such_subsystem", "anything")
    assert result is None


@pytest.mark.asyncio
async def test_unknown_setting_within_known_subsystem_returns_none():
    _register("xp", SettingSpec(name="xp_min", value_type=int, default=1))
    result = await resolve_setting(1, "xp", "no_such_setting")
    assert result is None


@pytest.mark.asyncio
async def test_unknown_spec_increments_counter():
    await resolve_setting(1, "no_such", "anything")
    snap = counters_snapshot()
    assert snap["unknown_spec"] == 1
    assert snap["calls_total"] == 1


# ---------------------------------------------------------------------------
# Default provenance — no settings_key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_spec_without_settings_key_returns_default():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=15),
    )
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    assert result.value == 15
    assert result.provenance == "default"
    assert result.default == 15
    assert result.valid is True
    assert result.raw is None
    assert any("settings_key unset" in d for d in result.diagnostics)


# ---------------------------------------------------------------------------
# Default provenance — settings_key present, KV row missing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kv_row_missing_returns_default():
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=15,
            settings_key="XP_MIN",
        ),
    )
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    assert result.value == 15
    assert result.provenance == "default"
    assert result.raw == ""
    assert result.valid is True


# ---------------------------------------------------------------------------
# Legacy KV provenance — happy path per type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_int_value_coerces_from_kv(_reset_state):
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=15,
            settings_key="XP_MIN",
        ),
    )
    _reset_state["kv"][(1, "XP_MIN")] = "42"
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    assert result.value == 42
    assert result.provenance == "legacy_kv"
    assert result.raw == "42"
    assert result.valid is True


@pytest.mark.asyncio
async def test_str_value_passes_through_from_kv(_reset_state):
    _register(
        "moderation",
        SettingSpec(
            name="dm_template",
            value_type=str,
            default="Hello",
            settings_key="DM_TEMPLATE",
        ),
    )
    _reset_state["kv"][(1, "DM_TEMPLATE")] = "Greetings"
    result = await resolve_setting(1, "moderation", "dm_template")
    assert result is not None
    assert result.value == "Greetings"
    assert result.provenance == "legacy_kv"
    assert result.valid is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("true", True),
        ("True", True),
        ("yes", True),
        ("on", True),
        ("1", True),
        ("false", False),
        ("False", False),
        ("no", False),
        ("off", False),
        ("0", False),
    ],
)
async def test_bool_value_coerces_from_kv(_reset_state, raw, expected):
    _register(
        "logging",
        SettingSpec(
            name="enabled",
            value_type=bool,
            default=False,
            settings_key="LOGGING_ENABLED",
        ),
    )
    _reset_state["kv"][(1, "LOGGING_ENABLED")] = raw
    result = await resolve_setting(1, "logging", "enabled")
    assert result is not None
    assert result.value is expected
    assert result.valid is True
    assert result.provenance == "legacy_kv"


@pytest.mark.asyncio
async def test_float_value_coerces_from_kv(_reset_state):
    _register(
        "rate",
        SettingSpec(
            name="multiplier",
            value_type=float,
            default=1.0,
            settings_key="RATE_MULTIPLIER",
        ),
    )
    _reset_state["kv"][(1, "RATE_MULTIPLIER")] = "2.5"
    result = await resolve_setting(1, "rate", "multiplier")
    assert result is not None
    assert result.value == 2.5
    assert result.valid is True


# ---------------------------------------------------------------------------
# Coercion failure → default with valid=False
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_int_coerce_failure_returns_default_with_valid_false(_reset_state):
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=15,
            settings_key="XP_MIN",
        ),
    )
    _reset_state["kv"][(1, "XP_MIN")] = "abc"
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    assert result.value == 15  # falls back to default
    assert result.valid is False
    # Provenance stays "legacy_kv" because a KV row *did* exist —
    # `valid=False` distinguishes the failure.
    assert result.provenance == "legacy_kv"
    assert result.raw == "abc"
    assert any("int coerce failed" in d for d in result.diagnostics)


@pytest.mark.asyncio
async def test_bool_coerce_failure_returns_default_with_valid_false(_reset_state):
    _register(
        "logging",
        SettingSpec(
            name="enabled",
            value_type=bool,
            default=False,
            settings_key="LOGGING_ENABLED",
        ),
    )
    _reset_state["kv"][(1, "LOGGING_ENABLED")] = "maybe"
    result = await resolve_setting(1, "logging", "enabled")
    assert result is not None
    assert result.value is False
    assert result.valid is False
    assert result.provenance == "legacy_kv"


# ---------------------------------------------------------------------------
# Validator hook
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validator_passes(_reset_state):
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
    _reset_state["kv"][(1, "XP_MIN")] = "10"
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    assert result.value == 10
    assert result.valid is True
    assert result.provenance == "legacy_kv"


@pytest.mark.asyncio
async def test_validator_rejects_value(_reset_state):
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
    _reset_state["kv"][(1, "XP_MIN")] = "-5"
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    assert result.value == 1  # falls back to default
    assert result.valid is False
    assert result.provenance == "legacy_kv"
    assert any("validator rejected" in d for d in result.diagnostics)
    assert any("must be non-negative" in d for d in result.diagnostics)


@pytest.mark.asyncio
async def test_validator_typeerror_rejects_value(_reset_state):
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
    _reset_state["kv"][(1, "XP_MIN")] = "10"
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    assert result.value == 1
    assert result.valid is False


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_batch_returns_every_setting_for_subsystem(_reset_state):
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=15,
            settings_key="XP_MIN",
        ),
        SettingSpec(
            name="xp_max",
            value_type=int,
            default=25,
            settings_key="XP_MAX",
        ),
        SettingSpec(
            name="cooldown",
            value_type=int,
            default=60,
            settings_key="XP_COOLDOWN",
        ),
    )
    _reset_state["kv"][(1, "XP_MIN")] = "5"
    _reset_state["kv"][(1, "XP_MAX")] = "30"
    # XP_COOLDOWN missing — falls back to default.
    results = await resolve_batch(1, "xp")
    assert {r.name for r in results} == {"xp_min", "xp_max", "cooldown"}
    by_name = {r.name: r for r in results}
    assert by_name["xp_min"].value == 5
    assert by_name["xp_max"].value == 30
    assert by_name["cooldown"].value == 60
    assert by_name["cooldown"].provenance == "default"


@pytest.mark.asyncio
async def test_resolve_batch_returns_empty_for_unknown_subsystem():
    results = await resolve_batch(1, "no_such_subsystem")
    assert results == ()


# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_counters_tally_provenance_and_validity(_reset_state):
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            settings_key="XP_MIN",
        ),
        SettingSpec(
            name="xp_max",
            value_type=int,
            default=10,
            settings_key="XP_MAX",
        ),
    )
    _reset_state["kv"][(1, "XP_MIN")] = "5"
    _reset_state["kv"][(1, "XP_MAX")] = "garbage"
    # 1 legacy_kv valid, 1 legacy_kv invalid
    await resolve_setting(1, "xp", "xp_min")
    await resolve_setting(1, "xp", "xp_max")
    # 1 default (missing key)
    await resolve_setting(2, "xp", "xp_min")
    # 1 unknown_spec
    await resolve_setting(1, "xp", "no_such")
    snap = counters_snapshot()
    assert snap["calls_total"] == 4
    assert snap["unknown_spec"] == 1
    assert snap["by_provenance"]["legacy_kv"] == 2
    assert snap["by_provenance"]["default"] == 1
    assert snap["by_valid"]["true"] == 2
    assert snap["by_valid"]["false"] == 1


# ---------------------------------------------------------------------------
# Caching via guild_config
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_repeated_reads_hit_guild_config_cache(_reset_state):
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            settings_key="XP_MIN",
        ),
    )
    _reset_state["kv"][(1, "XP_MIN")] = "5"

    await resolve_setting(1, "xp", "xp_min")
    fetches_after_first = _reset_state["fetches"]["calls"]
    assert fetches_after_first == 1

    await resolve_setting(1, "xp", "xp_min")
    fetches_after_second = _reset_state["fetches"]["calls"]
    assert fetches_after_second == 1  # cached — no new DB call

    # Different guild — new cache entry, new DB call.
    _reset_state["kv"][(2, "XP_MIN")] = "9"
    await resolve_setting(2, "xp", "xp_min")
    assert _reset_state["fetches"]["calls"] == 2


@pytest.mark.asyncio
async def test_guild_config_invalidate_drops_cached_value(_reset_state):
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            settings_key="XP_MIN",
        ),
    )
    _reset_state["kv"][(1, "XP_MIN")] = "5"
    await resolve_setting(1, "xp", "xp_min")
    assert _reset_state["fetches"]["calls"] == 1

    guild_config.invalidate(1)
    _reset_state["kv"][(1, "XP_MIN")] = "9"
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    assert result.value == 9
    assert _reset_state["fetches"]["calls"] == 2


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setting_resolution_is_frozen():
    _register("xp", SettingSpec(name="xp_min", value_type=int, default=1))
    result = await resolve_setting(1, "xp", "xp_min")
    assert result is not None
    with pytest.raises(Exception):
        result.value = 99  # type: ignore[misc]


def test_counters_snapshot_returns_copy():
    """Mutating the returned dict must not affect the live counters."""
    snap1 = counters_snapshot()
    snap1["by_provenance"]["default"] = 9999
    snap2 = counters_snapshot()
    assert snap2["by_provenance"]["default"] != 9999


# ---------------------------------------------------------------------------
# Diagnostics provider
# ---------------------------------------------------------------------------


def test_diagnostics_provider_is_registered_at_import_time():
    from services import diagnostics_service

    assert "settings_resolution" in diagnostics_service.registered_names()


@pytest.mark.asyncio
async def test_diagnostics_provider_exposes_counters(_reset_state):
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            settings_key="XP_MIN",
        ),
    )
    _reset_state["kv"][(1, "XP_MIN")] = "5"
    await resolve_setting(1, "xp", "xp_min")

    from services import diagnostics_service

    snap = diagnostics_service.snapshot("settings_resolution")
    assert "counters" in snap
    counters = snap["counters"]
    assert counters["calls_total"] >= 1
    assert counters["by_provenance"]["legacy_kv"] >= 1


# ---------------------------------------------------------------------------
# resolve_value — thin convenience wrapper used by migrated read-paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_value_returns_coerced_kv_value(_reset_state):
    _register(
        "moderation",
        SettingSpec(
            name="warn_threshold",
            value_type=int,
            default=3,
            settings_key="warn_threshold",
        ),
    )
    _reset_state["kv"][(1, "warn_threshold")] = "7"
    value = await resolve_value(1, "moderation", "warn_threshold", 3)
    assert value == 7
    assert isinstance(value, int)


@pytest.mark.asyncio
async def test_resolve_value_returns_spec_default_when_missing(_reset_state):
    _register(
        "moderation",
        SettingSpec(
            name="warn_threshold",
            value_type=int,
            default=3,
            settings_key="warn_threshold",
        ),
    )
    # No KV row → spec default, NOT the fallback arg.
    value = await resolve_value(1, "moderation", "warn_threshold", 999)
    assert value == 3


@pytest.mark.asyncio
async def test_resolve_value_returns_spec_default_when_malformed(_reset_state):
    """Malformed legacy value falls back to the spec default — never raises."""

    def _positive_int(value: object) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("expected positive int")

    _register(
        "moderation",
        SettingSpec(
            name="warn_threshold",
            value_type=int,
            default=3,
            settings_key="warn_threshold",
            validator=_positive_int,
        ),
    )
    _reset_state["kv"][(1, "warn_threshold")] = "not-a-number"
    value = await resolve_value(1, "moderation", "warn_threshold", 999)
    assert value == 3  # spec default, not the fallback, and no exception


@pytest.mark.asyncio
async def test_resolve_value_returns_fallback_for_undeclared_spec():
    # Undeclared (subsystem, name) → resolve_setting returns None → fallback.
    value = await resolve_value(1, "no_such_subsystem", "nope", 42)
    assert value == 42
