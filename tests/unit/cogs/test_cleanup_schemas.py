"""Unit tests for the cleanup subsystem schema (cogs.cleanup.schemas).

Cleanup completion-cert punch #4: the ``!cleanuphistory`` spam-duplicate window
is now a real per-guild scalar setting with a config-input widget.  These tests
pin the spec shape (default / bounds / capability / widget) and the consumer's
runtime resolution so the spec default and the cog fallback can never drift.
"""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)


def test_register_adds_cleanup_schema():
    from cogs.cleanup.schemas import register_schemas

    register_schemas()
    assert "cleanup" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("cleanup")
    assert schema is not None and schema.subsystem == "cleanup"


def test_register_is_idempotent():
    from cogs.cleanup.schemas import register_schemas

    register_schemas()
    schema_mod._reset_for_tests()
    register_schemas()
    assert schema_mod.get_schema("cleanup") is not None


def test_schema_keeps_its_domain_panel():
    """Punch #4 adds a scalar setting *without* dropping the governance-policy
    domain panel — cleanup surfaces both.
    """
    from cogs.cleanup.schemas import CLEANUP_CONFIG_SCHEMA

    assert CLEANUP_CONFIG_SCHEMA.domain_panels
    assert CLEANUP_CONFIG_SCHEMA.domain_panels[0].name == "Cleanup policies"


def test_spam_window_spec_shape():
    from cogs.cleanup.schemas import (
        CLEANUP_SETTINGS,
        DEFAULT_SPAM_WINDOW_SECONDS,
    )
    from utils.settings_keys import CLEANUP_SPAM_WINDOW_SECONDS

    by_name = {s.name: s for s in CLEANUP_SETTINGS}
    assert set(by_name) == {"spam_window_seconds"}
    spec = by_name["spam_window_seconds"]
    # Default equals the canonical constant (the cog fallback shares it).
    assert spec.default == DEFAULT_SPAM_WINDOW_SECONDS
    assert spec.value_type is int
    assert spec.settings_key == CLEANUP_SPAM_WINDOW_SECONDS
    # Config-input widget: a numeric preset row.
    assert spec.input_hint == "numeric_presets"
    assert spec.presets == (10, 15, 30)


def test_spam_window_default_is_the_historical_constant():
    """Byte-identical for existing guilds: the default stays the old 15s."""
    from cogs.cleanup.schemas import DEFAULT_SPAM_WINDOW_SECONDS

    assert DEFAULT_SPAM_WINDOW_SECONDS == 15


def test_spam_window_requires_a_registered_capability():
    from cogs.cleanup.schemas import CLEANUP_SETTINGS

    for spec in CLEANUP_SETTINGS:
        # Must be cleanup's registered policy-configure capability (an
        # unregistered cap would trip the identity-contract registry check).
        assert spec.capability_required == "cleanup.policy.configure"


def test_spam_window_validator_bounds():
    from cogs.cleanup.schemas import (
        CLEANUP_SETTINGS,
        MAX_SPAM_WINDOW_SECONDS,
        MIN_SPAM_WINDOW_SECONDS,
    )

    validator = {s.name: s for s in CLEANUP_SETTINGS}["spam_window_seconds"].validator
    assert validator is not None
    validator(MIN_SPAM_WINDOW_SECONDS)  # ok — lower bound
    validator(MAX_SPAM_WINDOW_SECONDS)  # ok — upper bound
    validator(15)  # ok — the default
    with pytest.raises(ValueError):
        validator(MIN_SPAM_WINDOW_SECONDS - 1)  # below MIN
    with pytest.raises(ValueError):
        validator(MAX_SPAM_WINDOW_SECONDS + 1)  # above MAX
    with pytest.raises(ValueError):
        validator(True)  # bool is not a valid int
    with pytest.raises(ValueError):
        validator("15")  # str is not an int
