"""Unit tests for the karma subsystem schema (cogs.karma.schemas)."""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from services import karma_config


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)


def test_register_adds_karma_schema():
    from cogs.karma.schemas import register_schemas

    register_schemas()
    assert "karma" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("karma")
    assert schema is not None and schema.subsystem == "karma"


def test_register_is_idempotent():
    from cogs.karma.schemas import register_schemas

    register_schemas()
    schema_mod._reset_for_tests()
    register_schemas()
    assert schema_mod.get_schema("karma") is not None


# Each spec's default must equal the canonical karma_config default — they
# share the constant, so this pins that they never drift.
_EXPECTED_DEFAULTS = {
    "enabled": karma_config.DEFAULT_ENABLED,
    "cooldown_seconds": karma_config.DEFAULT_COOLDOWN_SECONDS,
    "daily_cap": karma_config.DEFAULT_DAILY_CAP,
    "reaction_emoji": karma_config.DEFAULT_REACTION_EMOJI,
}


def test_spec_defaults_match_config_defaults():
    from cogs.karma.schemas import KARMA_SETTINGS

    by_name = {s.name: s for s in KARMA_SETTINGS}
    assert set(by_name) == set(_EXPECTED_DEFAULTS)
    for name, expected in _EXPECTED_DEFAULTS.items():
        assert by_name[name].default == expected


def test_all_specs_require_the_configure_capability():
    from cogs.karma.schemas import KARMA_SETTINGS

    for spec in KARMA_SETTINGS:
        assert spec.capability_required == "karma.settings.configure"


def test_reaction_emoji_validator_accepts_empty_and_an_emoji():
    from cogs.karma.schemas import _validate_reaction_emoji

    _validate_reaction_emoji("")  # empty = off, valid
    _validate_reaction_emoji("✨")
    _validate_reaction_emoji("<:thanks:123456789012345678>")


def test_reaction_emoji_validator_rejects_overlong_and_non_str():
    from cogs.karma.schemas import _validate_reaction_emoji

    with pytest.raises(ValueError):
        _validate_reaction_emoji("x" * 65)
    with pytest.raises(ValueError):
        _validate_reaction_emoji(123)
