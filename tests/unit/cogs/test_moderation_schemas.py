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
    assert schema.version == 2


def test_moderation_settings_cover_legacy_plus_pr10():
    from cogs.moderation.schemas import MODERATION_CONFIG_SCHEMA

    names = {s.name for s in MODERATION_CONFIG_SCHEMA.settings}
    assert names == {
        "warn_threshold",
        "warn_timeout_minutes",
        "dm_on_action",
        "dm_template",
        "require_reason",
        "ban_delete_message_days",
        "max_timeout_minutes",
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


# ---------------------------------------------------------------------------
# Drift guard — spec defaults must equal the policy defaults
# ---------------------------------------------------------------------------


def test_spec_defaults_match_policy_defaults():
    """The SettingSpec ``default`` and the ModerationPolicy default are the
    same canonical constants — a divergence would make an unconfigured guild
    behave differently than the settings panel claims."""
    assert _spec("dm_on_action").default == moderation_config.DEFAULT_DM_ON_ACTION
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
