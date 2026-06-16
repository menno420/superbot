"""Unit tests for the image-moderation subsystem schema."""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from services import image_moderation_config


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)


def test_register_adds_image_moderation_schema():
    from cogs.image_moderation.schemas import register_schemas

    register_schemas()
    assert "image_moderation" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("image_moderation")
    assert schema is not None and schema.subsystem == "image_moderation"


def test_register_is_idempotent():
    from cogs.image_moderation.schemas import register_schemas

    register_schemas()
    schema_mod._reset_for_tests()
    register_schemas()
    assert schema_mod.get_schema("image_moderation") is not None


# Each spec's default must equal the canonical config default — they share the
# constant, so this pins that they never drift.
_EXPECTED_DEFAULTS = {
    "enabled": image_moderation_config.DEFAULT_ENABLED,
    "sexual_enabled": image_moderation_config.DEFAULT_SEXUAL_ENABLED,
    "violence_enabled": image_moderation_config.DEFAULT_VIOLENCE_ENABLED,
    "harassment_enabled": image_moderation_config.DEFAULT_HARASSMENT_ENABLED,
    "hate_enabled": image_moderation_config.DEFAULT_HATE_ENABLED,
    "threshold_percent": image_moderation_config.DEFAULT_THRESHOLD_PERCENT,
    "exempt_roles": image_moderation_config.DEFAULT_EXEMPT_ROLES,
    "exempt_channels": image_moderation_config.DEFAULT_EXEMPT_CHANNELS,
}


def test_spec_defaults_match_config_defaults():
    from cogs.image_moderation.schemas import IMAGE_MODERATION_SETTINGS

    by_name = {s.name: s for s in IMAGE_MODERATION_SETTINGS}
    assert set(by_name) == set(_EXPECTED_DEFAULTS)
    for name, expected in _EXPECTED_DEFAULTS.items():
        assert by_name[name].default == expected


def test_every_flag_default_is_off():
    """A fresh guild must be unaffected — every bool flag defaults False."""
    from cogs.image_moderation.schemas import IMAGE_MODERATION_SETTINGS

    for spec in IMAGE_MODERATION_SETTINGS:
        if spec.value_type is bool:
            assert spec.default is False, spec.name


def test_all_specs_require_a_configure_capability():
    from cogs.image_moderation.schemas import IMAGE_MODERATION_SETTINGS

    for spec in IMAGE_MODERATION_SETTINGS:
        assert spec.capability_required == "moderation.settings.configure"


def test_threshold_validator_rejects_out_of_range():
    from cogs.image_moderation.schemas import IMAGE_MODERATION_SETTINGS

    by_name = {s.name: s for s in IMAGE_MODERATION_SETTINGS}
    validator = by_name["threshold_percent"].validator
    validator(80)  # ok
    with pytest.raises(ValueError):
        validator(40)  # below MIN_THRESHOLD_PERCENT
    with pytest.raises(ValueError):
        validator(101)  # above MAX_THRESHOLD_PERCENT
    with pytest.raises(ValueError):
        by_name["enabled"].validator("yes")  # not a bool


def test_exempt_csv_validator():
    from cogs.image_moderation.schemas import IMAGE_MODERATION_SETTINGS

    by_name = {s.name: s for s in IMAGE_MODERATION_SETTINGS}
    validator = by_name["exempt_roles"].validator
    validator("1, 2, 3")  # ok
    validator("")  # ok — empty means none
    with pytest.raises(ValueError):
        validator("1, notanid, 3")
