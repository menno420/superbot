"""Unit tests for the logging subsystem schema (S7a).

Verifies the schema declarations register correctly and conform to
the contracts the Settings Manager / customization catalogue /
provisioning catalogue depend on:

- two scalar settings (``enabled``, ``auto_create_channels``) with
  ``settings_key`` pointing at the existing legacy keys so the S6
  edit/reset flows work today;
- two channel bindings (``mod_channel``, ``cleanup_channel``) — both
  optional — that S7b will wire through
  :class:`BindingMutationPipeline`;
- two resource requirements with ``RECOMMENDED`` priority for S7c's
  create-channel flow.

The schema is registered via
:func:`cogs.logging.schemas.register_schemas` so the test can call
it directly without needing a live cog/bot.
"""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from core.runtime.resource_specs import ProvisioningPriority, ResourceKind
from core.runtime.subsystem_schema import BindingKind
from utils.settings_keys import logging as _log_keys


@pytest.fixture(autouse=True)
def _isolated_state():
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_schemas_adds_logging_to_registry():
    from cogs.logging.schemas import register_schemas

    register_schemas()
    assert "logging" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("logging")
    assert schema is not None
    assert schema.subsystem == "logging"


def test_register_schemas_is_idempotent_after_reset():
    from cogs.logging.schemas import register_schemas

    register_schemas()
    schema_mod._reset_for_tests()
    register_schemas()
    assert schema_mod.get_schema("logging") is not None


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def test_logging_settings_include_enabled_and_auto_create():
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    setting_names = {s.name for s in LOGGING_CONFIG_SCHEMA.settings}
    assert {"enabled", "auto_create_channels"}.issubset(setting_names)


def test_logging_settings_include_event_logging_v1():
    """Server event logging v1 (Q-0109) adds the category flags + routing mode."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    setting_names = {s.name for s in LOGGING_CONFIG_SCHEMA.settings}
    assert setting_names == {
        "enabled",
        "auto_create_channels",
        "messages_enabled",
        "members_enabled",
        "roles_enabled",
        "event_routing",
        # Completion cert punch #1 — exclusion lists.
        "ignored_channels",
        "ignored_users",
        # Server event logging v2 — audit-log + voice categories.
        "moderation_enabled",
        "channels_enabled",
        "server_enabled",
        "voice_enabled",
    }


def test_event_category_flags_point_at_legacy_keys_and_default_off():
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    by_name = {s.name: s for s in LOGGING_CONFIG_SCHEMA.settings}
    for name, key in (
        ("messages_enabled", _log_keys.LOGGING_MESSAGES_ENABLED),
        ("members_enabled", _log_keys.LOGGING_MEMBERS_ENABLED),
        ("roles_enabled", _log_keys.LOGGING_ROLES_ENABLED),
    ):
        spec = by_name[name]
        assert spec.value_type is bool
        assert spec.default is False
        assert spec.settings_key == key
        assert spec.capability_required == "logging.settings.configure"


def test_messages_enabled_hint_carries_privacy_disclosure():
    """Q-0109 requires the deleted-message privacy implication be surfaced."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    spec = next(
        s for s in LOGGING_CONFIG_SCHEMA.settings if s.name == "messages_enabled"
    )
    assert "Privacy" in spec.hint
    assert "deleted" in spec.hint.lower()


def test_event_routing_validator_accepts_modes_rejects_others():
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    spec = next(
        s for s in LOGGING_CONFIG_SCHEMA.settings if s.name == "event_routing"
    )
    assert spec.value_type is str
    assert spec.default == "combined"
    assert spec.allowed_values == ("combined", "per_category")
    spec.validator("combined")
    spec.validator("per_category")
    with pytest.raises(ValueError):
        spec.validator("nonsense")
    with pytest.raises(ValueError):
        spec.validator(1)


def test_logging_enabled_setting_points_at_legacy_key():
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    enabled = next(s for s in LOGGING_CONFIG_SCHEMA.settings if s.name == "enabled")
    assert enabled.value_type is bool
    assert enabled.default is False
    assert enabled.settings_key == _log_keys.LOGGING_ENABLED
    assert enabled.capability_required == "logging.settings.configure"


def test_logging_auto_create_setting_points_at_legacy_key():
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    auto = next(
        s for s in LOGGING_CONFIG_SCHEMA.settings if s.name == "auto_create_channels"
    )
    assert auto.value_type is bool
    assert auto.default is False
    assert auto.settings_key == _log_keys.LOGGING_AUTO_CREATE_CHANNELS
    assert auto.capability_required == "logging.settings.configure"


def test_logging_bool_settings_have_validators_that_reject_non_bool():
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    bool_specs = [s for s in LOGGING_CONFIG_SCHEMA.settings if s.value_type is bool]
    assert bool_specs  # sanity: there are bool settings to check
    for spec in bool_specs:
        assert spec.validator is not None
        # accepts bool
        spec.validator(True)
        spec.validator(False)
        # rejects non-bool — int subclasses (e.g. 1) are not accepted.
        with pytest.raises(ValueError):
            spec.validator(1)
        with pytest.raises(ValueError):
            spec.validator("true")


# ---------------------------------------------------------------------------
# Bindings
# ---------------------------------------------------------------------------


def test_logging_bindings_declare_mod_and_cleanup_channels():
    """Phase 9a expanded the binding set; the original two are still here."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    binding_names = {b.name for b in LOGGING_CONFIG_SCHEMA.bindings}
    assert {"mod_channel", "cleanup_channel"}.issubset(binding_names)


def test_logging_bindings_include_severity_and_audit_routes_phase_9a():
    """Phase 9a adds debug / info / warning / error / audit channel slots."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    binding_names = {b.name for b in LOGGING_CONFIG_SCHEMA.bindings}
    assert {
        "mod_channel",
        "cleanup_channel",
        "debug_channel",
        "info_channel",
        "warning_channel",
        "error_channel",
        "audit_channel",
    }.issubset(binding_names)


def test_logging_bindings_include_event_routes_v1():
    """Server event logging v1 (Q-0109) adds the four passive-event slots."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    binding_names = {b.name for b in LOGGING_CONFIG_SCHEMA.bindings}
    assert binding_names == {
        "mod_channel",
        "cleanup_channel",
        "debug_channel",
        "info_channel",
        "warning_channel",
        "error_channel",
        "audit_channel",
        "events_channel",
        "message_channel",
        "member_channel",
        "role_channel",
    }


def test_logging_schema_version_bumped_for_audit_log_v2():
    """Schema-shape change → version bump (v4 ignore lists → v5 audit-log v2)."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    assert LOGGING_CONFIG_SCHEMA.version == 5


def test_ignore_list_settings_point_at_legacy_keys_and_default_empty():
    """Completion cert punch #1 — the two exclusion-list scalars."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    by_name = {s.name: s for s in LOGGING_CONFIG_SCHEMA.settings}
    for name, key in (
        ("ignored_channels", _log_keys.LOGGING_IGNORED_CHANNELS),
        ("ignored_users", _log_keys.LOGGING_IGNORED_USERS),
    ):
        spec = by_name[name]
        assert spec.value_type is str
        assert spec.default == ""
        assert spec.settings_key == key
        assert spec.capability_required == "logging.settings.configure"
        # Loud write-time validator: numeric CSV accepted, junk rejected.
        assert spec.validator is not None
        spec.validator("42, 43")
        spec.validator("")  # empty = no exclusion
        with pytest.raises(ValueError):
            spec.validator("not-an-id")
        with pytest.raises(ValueError):
            spec.validator(123)


def test_logging_bindings_are_channel_kind_and_optional():
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    for binding in LOGGING_CONFIG_SCHEMA.bindings:
        assert binding.kind == BindingKind.CHANNEL
        assert binding.required is False
        assert binding.capability_required == "logging.settings.configure"


# ---------------------------------------------------------------------------
# Resource requirements
# ---------------------------------------------------------------------------


def test_logging_resource_requirements_cover_both_channels():
    """Phase 9a expanded the requirement set; the original two are still here."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    intents = {r.intent for r in LOGGING_CONFIG_SCHEMA.resource_requirements}
    assert {"mod_log", "cleanup_log"}.issubset(intents)


def test_logging_resource_requirements_include_phase_9a_intents():
    """Phase 9a adds RECOMMENDED resource requirements for every new route."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    intents = {r.intent for r in LOGGING_CONFIG_SCHEMA.resource_requirements}
    assert {
        "mod_log",
        "cleanup_log",
        "debug_log",
        "info_log",
        "warning_log",
        "error_log",
        "audit_log",
    }.issubset(intents)


def test_logging_resource_requirements_include_event_intents_v1():
    """Server event logging v1 (Q-0109) adds the four passive-event intents."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    intents = {r.intent for r in LOGGING_CONFIG_SCHEMA.resource_requirements}
    assert {"events_log", "message_log", "member_log", "role_log"}.issubset(intents)


def test_logging_resource_requirements_link_to_bindings():
    """Each ResourceRequirement.binding_name must match a declared BindingSpec."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    binding_names = {b.name for b in LOGGING_CONFIG_SCHEMA.bindings}
    for req in LOGGING_CONFIG_SCHEMA.resource_requirements:
        assert req.binding_name in binding_names, (
            f"ResourceRequirement intent={req.intent!r} "
            f"references unknown binding {req.binding_name!r}"
        )


def test_logging_resource_requirements_are_recommended_not_required():
    """Logging is opt-in by default; channels are RECOMMENDED, not REQUIRED."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    for req in LOGGING_CONFIG_SCHEMA.resource_requirements:
        assert req.provisioning.priority == ProvisioningPriority.RECOMMENDED


def test_logging_resource_requirements_have_suggested_channel_names():
    """Match the existing DEFAULT_*_CHANNEL_NAME constants so S7c's
    create-channel flow does not have to invent new names."""
    from cogs.logging.schemas import LOGGING_CONFIG_SCHEMA

    by_intent = {r.intent: r for r in LOGGING_CONFIG_SCHEMA.resource_requirements}
    assert by_intent["mod_log"].provisioning.suggested_name == "bot-mod-log"
    assert by_intent["cleanup_log"].provisioning.suggested_name == "bot-cleanup-log"
    for req in LOGGING_CONFIG_SCHEMA.resource_requirements:
        assert req.kind == ResourceKind.CHANNEL


# ---------------------------------------------------------------------------
# Registry-level checks (logging shows up in SUBSYSTEMS)
# ---------------------------------------------------------------------------


def test_subsystems_registry_includes_logging():
    from utils.subsystem_registry import SUBSYSTEMS

    assert "logging" in SUBSYSTEMS
    meta = SUBSYSTEMS["logging"]
    assert meta["visibility_mode"] == "normal"
    assert meta["visibility_tier"] == "administrator"
    assert "logging" in meta["entry_points"]


def test_logging_subsystem_has_three_declared_capabilities():
    from utils.subsystem_registry import SUBSYSTEMS

    caps = set(SUBSYSTEMS["logging"]["capabilities"])
    assert caps == {
        "logging.settings.configure",
        "logging.channel.bind",
        "logging.channel.create",
    }


def test_logging_in_known_panel_commands():
    """Discoverability invariant relies on KNOWN_PANEL_COMMANDS for
    cogs that don't have a build_help_menu_view hook of their own."""
    from services.customization_catalogue import KNOWN_PANEL_COMMANDS

    assert ("logging", "logging") in KNOWN_PANEL_COMMANDS
