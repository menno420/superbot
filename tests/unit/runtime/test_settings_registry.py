"""Unit tests for core.runtime.settings_registry — S1.

Covers the builder, the frozen snapshot, the findings buckets, the lookup
methods, and the diagnostics provider registration.
"""

from __future__ import annotations

import pytest

from core.runtime import settings_registry as registry_mod
from core.runtime import subsystem_schema as schema_mod
from core.runtime.settings_registry import (
    RegistryFindings,
    SettingEntry,
    SettingsRegistry,
    build_registry,
    get_cached_registry,
)
from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema


@pytest.fixture(autouse=True)
def _reset_state():
    """Snapshot the live schema registry and reset our cache around each
    test so we never leak between cases or interfere with other tests."""
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    registry_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)
    registry_mod._reset_for_tests()


def _register(subsystem: str, *settings: SettingSpec) -> None:
    schema_mod.register(SubsystemSchema(subsystem=subsystem, settings=settings))


# ---------------------------------------------------------------------------
# Empty registry / first build
# ---------------------------------------------------------------------------


def test_build_registry_returns_empty_snapshot_when_no_schemas():
    snap = build_registry()
    assert isinstance(snap, SettingsRegistry)
    assert snap.version == 1
    assert snap.entries == ()
    assert snap.findings.total == 0


def test_get_cached_registry_returns_none_before_first_build():
    assert get_cached_registry() is None


def test_get_cached_registry_returns_last_built():
    snap = build_registry()
    assert get_cached_registry() is snap


# ---------------------------------------------------------------------------
# Entry construction
# ---------------------------------------------------------------------------


def test_entries_carry_subsystem_and_name_and_type():
    _register(
        "economy",
        SettingSpec(
            name="daily_cooldown",
            value_type=int,
            default=86400,
            settings_key="ECONOMY_DAILY_COOLDOWN",
            capability_required="economy.settings.configure",
            hint="Seconds between !daily claims.",
        ),
    )
    snap = build_registry()
    assert len(snap.entries) == 1
    entry = snap.entries[0]
    assert isinstance(entry, SettingEntry)
    assert entry.subsystem == "economy"
    assert entry.name == "daily_cooldown"
    assert entry.value_type_name == "int"
    assert entry.default_repr == "86400"
    assert entry.settings_key == "ECONOMY_DAILY_COOLDOWN"
    assert entry.capability_required == "economy.settings.configure"
    assert entry.hint.startswith("Seconds")
    assert entry.has_validator is False


def test_entries_record_validator_presence():
    def _v(_value):  # pragma: no cover - never invoked in this test
        return None

    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, validator=_v),
    )
    snap = build_registry()
    assert snap.entries[0].has_validator is True


def test_entries_sorted_by_subsystem_alphabetically():
    _register("xp", SettingSpec(name="xp_min", value_type=int, default=1))
    _register(
        "economy", SettingSpec(name="daily_cooldown", value_type=int, default=86400)
    )
    _register(
        "moderation", SettingSpec(name="warn_threshold", value_type=int, default=3)
    )
    snap = build_registry()
    subsystems = [e.subsystem for e in snap.entries]
    assert subsystems == sorted(subsystems)


# ---------------------------------------------------------------------------
# by_subsystem / find / find_by_settings_key
# ---------------------------------------------------------------------------


def test_by_subsystem_returns_only_entries_for_that_subsystem():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1),
        SettingSpec(name="xp_max", value_type=int, default=10),
    )
    _register("moderation", SettingSpec(name="warn_threshold", value_type=int, default=3))
    snap = build_registry()
    xp_entries = snap.by_subsystem("xp")
    assert {e.name for e in xp_entries} == {"xp_min", "xp_max"}
    mod_entries = snap.by_subsystem("moderation")
    assert {e.name for e in mod_entries} == {"warn_threshold"}
    assert snap.by_subsystem("unknown") == ()


def test_find_returns_entry_for_known_subsystem_and_name():
    _register("xp", SettingSpec(name="xp_min", value_type=int, default=1))
    snap = build_registry()
    found = snap.find("xp", "xp_min")
    assert found is not None
    assert found.subsystem == "xp"
    assert found.name == "xp_min"


def test_find_returns_none_on_miss():
    _register("xp", SettingSpec(name="xp_min", value_type=int, default=1))
    snap = build_registry()
    assert snap.find("xp", "no_such_setting") is None
    assert snap.find("no_such_subsystem", "xp_min") is None


def test_find_by_settings_key_returns_entry():
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            settings_key="XP_MIN",
        ),
    )
    snap = build_registry()
    found = snap.find_by_settings_key("XP_MIN")
    assert found is not None
    assert found.name == "xp_min"


def test_find_by_settings_key_returns_none_when_empty():
    snap = build_registry()
    assert snap.find_by_settings_key("") is None
    assert snap.find_by_settings_key("UNKNOWN") is None


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


def test_findings_flag_missing_settings_key():
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            capability_required="xp.settings.configure",
            # No settings_key — transitional state.
        ),
    )
    snap = build_registry()
    assert snap.findings.settings_without_settings_key == ("xp.xp_min",)
    assert snap.findings.total >= 1


def test_findings_flag_missing_capability():
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=1,
            settings_key="XP_MIN",
            # No capability_required — uncommon but legal.
        ),
    )
    snap = build_registry()
    assert snap.findings.settings_without_capability == ("xp.xp_min",)


def test_findings_flag_duplicate_settings_keys():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="SHARED"),
    )
    _register(
        "moderation",
        SettingSpec(name="warn", value_type=int, default=3, settings_key="SHARED"),
    )
    snap = build_registry()
    assert "SHARED" in snap.findings.duplicate_settings_keys


def test_findings_have_total_property():
    findings = RegistryFindings(
        settings_without_settings_key=("a", "b"),
        settings_without_capability=("c",),
    )
    assert findings.total == 3


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


def test_rebuild_replaces_cached_snapshot():
    _register("xp", SettingSpec(name="xp_min", value_type=int, default=1))
    first = build_registry()
    schema_mod._reset_for_tests()
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1),
        SettingSpec(name="xp_max", value_type=int, default=10),
    )
    second = build_registry()
    assert second is not first
    assert get_cached_registry() is second
    assert len(second.entries) == 2


# ---------------------------------------------------------------------------
# Diagnostics provider
# ---------------------------------------------------------------------------


def test_diagnostics_provider_returns_not_built_before_first_build():
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("settings_registry")
    assert snap["status"] == "not_built"


def test_diagnostics_provider_returns_counts_after_build():
    _register(
        "xp",
        SettingSpec(name="xp_min", value_type=int, default=1, settings_key="XP_MIN"),
    )
    _register(
        "moderation",
        SettingSpec(
            name="warn_threshold",
            value_type=int,
            default=3,
            settings_key="WARN_THRESHOLD",
        ),
    )
    build_registry()
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("settings_registry")
    assert snap["status"] == "built"
    assert snap["version"] == 1
    assert snap["entry_count"] == 2
    assert snap["subsystems"] == 2
    assert snap["by_subsystem"] == {"xp": 1, "moderation": 1}


def test_diagnostics_provider_is_registered_at_import_time():
    from services import diagnostics_service

    assert "settings_registry" in diagnostics_service.registered_names()


# ---------------------------------------------------------------------------
# Frozen dataclass guards — registry must be immutable.
# ---------------------------------------------------------------------------


def test_entry_is_frozen_dataclass():
    _register("xp", SettingSpec(name="xp_min", value_type=int, default=1))
    snap = build_registry()
    entry = snap.entries[0]
    with pytest.raises(Exception):
        entry.subsystem = "moderation"  # type: ignore[misc]


def test_registry_is_frozen_dataclass():
    snap = build_registry()
    with pytest.raises(Exception):
        snap.version = 99  # type: ignore[misc]
