"""Unit tests for the moderation subsystem schema (server-management PR10).

The PR10 settings make moderation behaviour operator-configurable through
the ordinary ``!settings`` widget dispatcher.  These tests pin the spec
shapes the dispatcher and the :mod:`services.moderation_config` policy
loader depend on, and guard against spec-default / policy-default drift.
"""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from services import moderation_config
from utils.settings_keys import moderation as _mod_keys


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


def test_register_schemas_adds_moderation_to_registry():
    from cogs.moderation.schemas import register_schemas

    register_schemas()
    assert "moderation" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("moderation")
    assert schema is not None
    assert schema.version == 7


def test_moderation_settings_cover_legacy_plus_pr10():
    from cogs.moderation.schemas import MODERATION_CONFIG_SCHEMA

    names = {s.name for s in MODERATION_CONFIG_SCHEMA.settings}
    assert names == {
        "warn_threshold",
        "warn_timeout_minutes",
        "warn_escalation_action",
        "dm_on_action",
        "dm_actions",
        "dm_template",
        "require_reason",
        "ban_delete_message_days",
        "max_timeout_minutes",
        "post_action_cleanup",
        "post_action_cleanup_limit",
        "public_log_actions",
        "public_log_channel",
        "moderator_role",
        "trusted_role",
    }


def _spec(name: str):
    from cogs.moderation.schemas import MODERATION_CONFIG_SCHEMA

    return next(s for s in MODERATION_CONFIG_SCHEMA.settings if s.name == name)


# ---------------------------------------------------------------------------
# Per-setting shape
# ---------------------------------------------------------------------------


def test_dm_on_action_is_bool_toggle():
    spec = _spec("dm_on_action")
    assert spec.value_type is bool
    assert spec.default is False
    assert spec.settings_key == _mod_keys.MOD_DM_ON_ACTION
    assert spec.capability_required == "moderation.settings.configure"
    spec.validator(True)
    spec.validator(False)
    with pytest.raises(ValueError):
        spec.validator(1)  # int is not bool


def test_dm_actions_is_validated_csv_subset():
    spec = _spec("dm_actions")
    assert spec.value_type is str
    assert spec.default == moderation_config.DEFAULT_DM_ACTIONS
    assert spec.settings_key == _mod_keys.MOD_DM_ACTIONS
    assert spec.capability_required == "moderation.settings.configure"
    # Free-form modal (a multi-token csv, not a single-choice enum select).
    assert spec.allowed_values == ()
    assert spec.input_hint == ""
    spec.validator("warn,timeout")
    spec.validator("")  # empty = no action DMs, allowed
    spec.validator(" Warn , BAN ")  # case/space tolerant
    with pytest.raises(ValueError):
        spec.validator("warn,bogus")  # unknown token rejected
    with pytest.raises(ValueError):
        spec.validator(123)  # not a str


def test_require_reason_is_bool_toggle():
    spec = _spec("require_reason")
    assert spec.value_type is bool
    assert spec.default is False
    assert spec.settings_key == _mod_keys.MOD_REQUIRE_REASON
    assert spec.capability_required == "moderation.settings.configure"
    spec.validator(True)
    spec.validator(False)
    with pytest.raises(ValueError):
        spec.validator(1)  # int is not bool


def test_dm_template_is_free_text():
    spec = _spec("dm_template")
    assert spec.value_type is str
    assert spec.default == ""
    assert spec.settings_key == _mod_keys.MOD_DM_TEMPLATE
    # No allowed_values / input_hint → renders the free-form text modal.
    assert spec.allowed_values == ()
    assert spec.input_hint == ""
    spec.validator("Goodbye {user}")
    with pytest.raises(ValueError):
        spec.validator("x" * 5000)


def test_ban_delete_days_is_numeric_presets_in_range():
    spec = _spec("ban_delete_message_days")
    assert spec.value_type is int
    assert spec.default == 0
    assert spec.settings_key == _mod_keys.MOD_BAN_DELETE_MESSAGE_DAYS
    assert spec.input_hint == "numeric_presets"
    assert spec.presets == (0, 1, 7)
    spec.validator(0)
    spec.validator(7)
    with pytest.raises(ValueError):
        spec.validator(8)
    with pytest.raises(ValueError):
        spec.validator(-1)
    with pytest.raises(ValueError):
        spec.validator(True)  # bool is not a valid day count


def test_warn_escalation_action_is_enum_select():
    spec = _spec("warn_escalation_action")
    assert spec.value_type is str
    assert spec.default == "timeout"  # behaviour-preserving today
    assert spec.settings_key == _mod_keys.MOD_WARN_ESCALATION_ACTION
    assert spec.capability_required == "moderation.settings.configure"
    # Non-empty allowed_values → the edit flow renders a Select, not free text.
    assert spec.allowed_values == ("timeout", "kick", "ban", "none")
    spec.validator("timeout")
    spec.validator("none")
    with pytest.raises(ValueError):
        spec.validator("explode")
    with pytest.raises(ValueError):
        spec.validator(3)


def test_max_timeout_minutes_is_numeric_presets_in_range():
    spec = _spec("max_timeout_minutes")
    assert spec.value_type is int
    assert spec.default == 40320  # Discord's 28-day max
    assert spec.settings_key == _mod_keys.MOD_MAX_TIMEOUT_MINUTES
    assert spec.input_hint == "numeric_presets"
    assert 40320 in spec.presets
    spec.validator(1)
    spec.validator(40320)
    with pytest.raises(ValueError):
        spec.validator(0)
    with pytest.raises(ValueError):
        spec.validator(40321)


def test_post_action_cleanup_is_enum_select():
    spec = _spec("post_action_cleanup")
    assert spec.value_type is str
    assert spec.default == "none"  # behaviour-preserving today
    assert spec.settings_key == _mod_keys.MOD_POST_ACTION_CLEANUP
    assert spec.capability_required == "moderation.settings.configure"
    # Non-empty allowed_values → the edit flow renders a Select, not free text.
    assert spec.allowed_values == ("none", "kick", "ban", "both")
    spec.validator("none")
    spec.validator("both")
    with pytest.raises(ValueError):
        spec.validator("nuke")
    with pytest.raises(ValueError):
        spec.validator(1)


def test_post_action_cleanup_limit_is_numeric_presets_in_range():
    spec = _spec("post_action_cleanup_limit")
    assert spec.value_type is int
    assert spec.default == 100
    assert spec.settings_key == _mod_keys.MOD_POST_ACTION_CLEANUP_LIMIT
    assert spec.input_hint == "numeric_presets"
    assert spec.presets == (50, 100, 200, 500)
    spec.validator(1)
    spec.validator(500)
    with pytest.raises(ValueError):
        spec.validator(0)
    with pytest.raises(ValueError):
        spec.validator(501)
    with pytest.raises(ValueError):
        spec.validator(True)  # bool is not a valid scan limit


def test_public_log_actions_is_enum_select():
    spec = _spec("public_log_actions")
    assert spec.value_type is str
    assert spec.default == "none"  # off by default
    assert spec.settings_key == _mod_keys.MOD_PUBLIC_LOG_ACTIONS
    assert spec.capability_required == "moderation.settings.configure"
    assert spec.allowed_values == ("none", "bans", "removals", "all")
    spec.validator("none")
    spec.validator("removals")
    with pytest.raises(ValueError):
        spec.validator("everything")
    with pytest.raises(ValueError):
        spec.validator(1)


def test_public_log_channel_is_channel_picker():
    spec = _spec("public_log_channel")
    assert spec.value_type is str
    assert spec.default == ""
    assert spec.settings_key == _mod_keys.MOD_PUBLIC_LOG_CHANNEL
    assert spec.input_hint == "channel"  # native channel select
    spec.validator("")  # empty = off
    spec.validator("123456789012345678")  # numeric channel id
    with pytest.raises(ValueError):
        spec.validator("not-an-id")
    with pytest.raises(ValueError):
        spec.validator(123)  # must be a string id


def test_moderator_role_is_role_picker():
    """ADR-008 — the moderator role grants the moderator tier; settable via a
    native role select, admin-floor capability, stored as the numeric role id."""
    from utils.settings_keys import governance as _gov_keys

    spec = _spec("moderator_role")
    assert spec.value_type is str
    assert spec.default == ""  # unset = Discord permissions only
    assert spec.settings_key == _gov_keys.MODERATOR_TIER_ROLE_ID
    assert spec.capability_required == "moderation.settings.configure"
    assert spec.input_hint == "role"  # native role select
    spec.validator("")  # empty = unset
    spec.validator("123456789012345678")  # numeric role id
    with pytest.raises(ValueError):
        spec.validator("not-an-id")
    with pytest.raises(ValueError):
        spec.validator(123)  # must be a string id


def test_trusted_role_is_role_picker():
    """ADR-008 — the trusted role is wired symmetrically to the moderator role."""
    from utils.settings_keys import governance as _gov_keys

    spec = _spec("trusted_role")
    assert spec.value_type is str
    assert spec.default == ""
    assert spec.settings_key == _gov_keys.TRUSTED_TIER_ROLE_ID
    assert spec.capability_required == "moderation.settings.configure"
    assert spec.input_hint == "role"
    spec.validator("")
    spec.validator("123456789012345678")
    with pytest.raises(ValueError):
        spec.validator("not-an-id")
    with pytest.raises(ValueError):
        spec.validator(123)


# ---------------------------------------------------------------------------
# Drift guard — spec defaults must equal the policy defaults
# ---------------------------------------------------------------------------


def test_spec_defaults_match_policy_defaults():
    """The SettingSpec ``default`` and the ModerationPolicy default are the
    same canonical constants — a divergence would make an unconfigured guild
    behave differently than the settings panel claims."""
    assert _spec("dm_on_action").default == moderation_config.DEFAULT_DM_ON_ACTION
    assert _spec("dm_actions").default == moderation_config.DEFAULT_DM_ACTIONS
    assert _spec("dm_template").default == moderation_config.DEFAULT_DM_TEMPLATE
    assert _spec("require_reason").default == moderation_config.DEFAULT_REQUIRE_REASON
    assert (
        _spec("ban_delete_message_days").default
        == moderation_config.DEFAULT_BAN_DELETE_MESSAGE_DAYS
    )
    assert (
        _spec("max_timeout_minutes").default
        == moderation_config.DEFAULT_MAX_TIMEOUT_MINUTES
    )
    assert _spec("warn_threshold").default == moderation_config.DEFAULT_WARN_THRESHOLD
    assert (
        _spec("warn_timeout_minutes").default
        == moderation_config.DEFAULT_WARN_TIMEOUT_MINUTES
    )
    assert (
        _spec("warn_escalation_action").default
        == moderation_config.DEFAULT_WARN_ESCALATION_ACTION
    )
    assert (
        _spec("post_action_cleanup").default
        == moderation_config.DEFAULT_POST_ACTION_CLEANUP
    )
    assert (
        _spec("post_action_cleanup_limit").default
        == moderation_config.DEFAULT_POST_ACTION_CLEANUP_LIMIT
    )
    assert (
        _spec("public_log_actions").default
        == moderation_config.DEFAULT_PUBLIC_LOG_ACTIONS
    )
    assert (
        _spec("public_log_channel").default
        == moderation_config.DEFAULT_PUBLIC_LOG_CHANNEL
    )
