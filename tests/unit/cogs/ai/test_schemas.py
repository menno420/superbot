"""M1 — AI subsystem schema shape pins.

The AI cog ships its first SubsystemSchema in M1. These tests pin
names, defaults, allowed values, the ``audit_log_channel`` binding,
and the multiline ``ai_guild_instruction_profile`` scalar so future
edits cannot silently drift the contract.

M2 backfills the scalars into typed ``ai_guild_policy`` /
``ai_instruction_profile`` rows and adds a separate test
(``test_ai_policy_runtime_reads_typed_tables``) that pins runtime
reads to the typed tables. M1 only owns scalar shape.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


# ---------------------------------------------------------------------------
# Schema identity
# ---------------------------------------------------------------------------


def test_ai_config_schema_targets_ai_subsystem():
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    assert AI_CONFIG_SCHEMA.subsystem == "ai"
    assert AI_CONFIG_SCHEMA.version == 1


def test_register_schemas_is_idempotent():
    from cogs.ai.schemas import AI_CONFIG_SCHEMA, register_schemas
    from core.runtime import subsystem_schema

    register_schemas()
    register_schemas()  # second call must not raise
    assert subsystem_schema.get_schema("ai") is AI_CONFIG_SCHEMA


# ---------------------------------------------------------------------------
# Settings — names, types, defaults, validators
# ---------------------------------------------------------------------------


def _spec(name: str):
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    spec = next(
        (s for s in AI_CONFIG_SCHEMA.settings if s.name == name),
        None,
    )
    assert spec is not None, f"AI schema must declare setting {name!r}"
    return spec


def test_ai_enabled_default_off_and_bool_typed():
    from utils.settings_keys import AI_ENABLED

    spec = _spec("ai_enabled")
    assert spec.value_type is bool
    assert spec.default is False
    assert spec.settings_key == AI_ENABLED
    assert spec.capability_required == "ai.settings.configure"


def test_ai_natural_language_enabled_default_off():
    from utils.settings_keys import AI_NATURAL_LANGUAGE_ENABLED

    spec = _spec("ai_natural_language_enabled")
    assert spec.value_type is bool
    assert spec.default is False
    assert spec.settings_key == AI_NATURAL_LANGUAGE_ENABLED


def test_ai_default_provider_is_enum_with_known_values():
    spec = _spec("ai_default_provider")
    assert spec.value_type is str
    assert spec.default == "deterministic"
    assert spec.allowed_values == ("deterministic", "openai", "anthropic")


def test_ai_default_provider_validator_accepts_supported_providers():
    """anthropic is a first-class provider (the runtime already supports
    it via routing + AnthropicProvider); the policy/settings layer must
    offer it too.
    """
    spec = _spec("ai_default_provider")
    spec.validator("deterministic")  # type: ignore[misc]
    spec.validator("openai")  # type: ignore[misc]
    spec.validator("anthropic")  # type: ignore[misc]


def test_ai_default_provider_validator_rejects_unknown_provider():
    spec = _spec("ai_default_provider")
    with pytest.raises(ValueError):
        spec.validator("gemini")  # type: ignore[misc]


def test_ai_minimum_level_default_is_two_with_presets():
    spec = _spec("ai_minimum_level_default")
    assert spec.value_type is int
    assert spec.default == 2
    assert spec.input_hint == "numeric_presets"
    assert spec.presets == (0, 1, 2, 3, 5, 10)


def test_ai_cooldown_seconds_default_thirty_with_presets():
    spec = _spec("ai_cooldown_seconds")
    assert spec.value_type is int
    assert spec.default == 30
    assert spec.input_hint == "numeric_presets"
    assert spec.presets == (0, 15, 30, 60, 120, 300)


def test_ai_fresh_user_mention_allowance_default_one():
    spec = _spec("ai_fresh_user_mention_allowance")
    assert spec.value_type is int
    assert spec.default == 1
    assert spec.presets == (0, 1, 3, 5, 10)


def test_ai_guild_instruction_profile_is_free_text_default_empty():
    """The instruction profile is a multiline free-text scalar in M1.

    Pinned so a future edit cannot accidentally promote it to an
    enum or a binding (which would skip the M2 backfill path into
    ai_instruction_profile rows).
    """
    spec = _spec("ai_guild_instruction_profile")
    assert spec.value_type is str
    assert spec.default == ""
    assert spec.allowed_values == ()  # free-form, not enum
    assert spec.input_hint == ""  # default modal — multiline-friendly


def test_non_negative_int_validator_rejects_negatives():
    spec = _spec("ai_minimum_level_default")
    with pytest.raises(ValueError):
        spec.validator(-1)  # type: ignore[misc]


def test_non_negative_int_validator_accepts_zero():
    spec = _spec("ai_minimum_level_default")
    spec.validator(0)  # type: ignore[misc] — must not raise


# ---------------------------------------------------------------------------
# Bindings — audit_log_channel is the canonical owner
# ---------------------------------------------------------------------------


def test_audit_log_channel_is_a_channel_binding_not_a_scalar():
    """The audit_log_channel is a BindingSpec, not a scalar SettingSpec.

    Pinned by accepted decision: the M1 binding remains the single
    source of truth for the AI audit channel across all later
    milestones; M2 does not add an audit_log_channel_id column to
    ai_guild_policy.
    """
    from cogs.ai.schemas import AI_CONFIG_SCHEMA
    from core.runtime.subsystem_schema import BindingKind

    binding = next(
        (b for b in AI_CONFIG_SCHEMA.bindings if b.name == "audit_log_channel"),
        None,
    )
    assert binding is not None, "AI schema must declare audit_log_channel binding"
    assert binding.kind is BindingKind.CHANNEL
    assert binding.required is False
    assert binding.capability_required == "ai.settings.configure"


def test_ai_schema_does_not_declare_audit_log_channel_as_a_scalar():
    """audit_log_channel must live in BINDINGS, never in SETTINGS.

    A second source of truth would defeat the "one BindingSpec, one
    binding mutation pipeline write" rule that M2 relies on.
    """
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    setting_names = {s.name for s in AI_CONFIG_SCHEMA.settings}
    assert "audit_log_channel" not in setting_names
    assert "audit_log_channel_id" not in setting_names


# ---------------------------------------------------------------------------
# Capability hygiene
# ---------------------------------------------------------------------------


def test_every_ai_setting_requires_the_configure_capability():
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    for spec in AI_CONFIG_SCHEMA.settings:
        assert (
            spec.capability_required == "ai.settings.configure"
        ), f"AI setting {spec.name!r} must require ai.settings.configure"


def test_settings_keys_re_export_all_ai_keys():
    """Every M1 AI scalar must be re-exported from utils.settings_keys.

    Pinned so adding a new AI scalar without updating the package
    __init__ surfaces as a test failure rather than an obscure
    ImportError at runtime.
    """
    import utils.settings_keys as keys

    for name in (
        "AI_ENABLED",
        "AI_NATURAL_LANGUAGE_ENABLED",
        "AI_DEFAULT_PROVIDER",
        "AI_DEFAULT_MODEL",
        "AI_MINIMUM_LEVEL_DEFAULT",
        "AI_COOLDOWN_SECONDS",
        "AI_FRESH_USER_MENTION_ALLOWANCE",
        "AI_GUILD_INSTRUCTION_PROFILE",
    ):
        assert hasattr(keys, name), f"utils.settings_keys must re-export {name}"
