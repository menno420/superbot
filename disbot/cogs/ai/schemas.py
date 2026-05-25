"""AI Platform subsystem schemas — Milestone 1.

M1 ships the AI cog's guild-level configuration as plain scalars +
one channel binding + one multiline instruction text. The schema is
modelled on :data:`cogs.xp.schemas.XP_CONFIG_SCHEMA` so the
auto-dispatched settings UI renders the AI section for free.

The instruction profile setting (``ai.guild_instruction_profile``)
is a **transitional scalar seed**: M2 backfills its body into a
typed ``ai_instruction_profile`` row named ``"default"`` and points
``ai_guild_policy.guild_instruction_profile_id`` at it. After the M2
backfill, the typed tables become the runtime source of truth and
the scalar becomes a presentation / backcompat surface.

The ``audit_log_channel`` binding is the **single source of truth**
for the AI audit channel for the rest of this initiative — M2 does
NOT add an ``audit_log_channel_id`` column to ``ai_guild_policy``.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SettingSpec,
    SubsystemSchema,
)
from utils.settings_keys import (
    AI_COOLDOWN_SECONDS,
    AI_DEFAULT_MODEL,
    AI_DEFAULT_PROVIDER,
    AI_ENABLED,
    AI_FRESH_USER_MENTION_ALLOWANCE,
    AI_GUILD_INSTRUCTION_PROFILE,
    AI_MINIMUM_LEVEL_DEFAULT,
    AI_NATURAL_LANGUAGE_ENABLED,
)

_CAPABILITY = "ai.settings.configure"


def _validate_bool(value: object) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {type(value).__name__}")


def _validate_provider(value: object) -> None:
    if value not in ("deterministic", "openai"):
        raise ValueError(
            "default_provider must be 'deterministic' or 'openai', "
            f"got {value!r}",
        )


def _validate_str(value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")


def _validate_non_negative_int(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"expected non-negative int, got {value!r}",
        )


# ---------------------------------------------------------------------------
# Bindings
# ---------------------------------------------------------------------------

AI_BINDINGS: tuple[BindingSpec, ...] = (
    BindingSpec(
        name="audit_log_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel where AI Platform writes audit entries (policy "
            "changes, denials, kill-switch flips, decision-audit "
            "summaries). Single source of truth for the rest of this "
            "initiative — M2 does not duplicate this binding into the "
            "typed AI policy tables."
        ),
        capability_required=_CAPABILITY,
    ),
)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

AI_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="ai_enabled",
        value_type=bool,
        default=False,
        settings_key=AI_ENABLED,
        capability_required=_CAPABILITY,
        hint=(
            "Master switch for the AI Platform. When false, no AI "
            "feature runs for this guild — including BTD6 AI "
            "augmentation and the central natural-language stage."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="ai_natural_language_enabled",
        value_type=bool,
        default=False,
        settings_key=AI_NATURAL_LANGUAGE_ENABLED,
        capability_required=_CAPABILITY,
        hint=(
            "Whether the bot may reply to natural-language messages "
            "(channel- and role-policy still apply). Independent of "
            "ai.enabled so admins can keep AI features available "
            "without enabling passive replies."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="ai_default_provider",
        value_type=str,
        default="deterministic",
        settings_key=AI_DEFAULT_PROVIDER,
        capability_required=_CAPABILITY,
        hint=(
            "Default provider used by AI tasks that don't specify "
            "their own. 'deterministic' keeps responses local; "
            "'openai' routes through the configured OpenAI account."
        ),
        validator=_validate_provider,
        allowed_values=("deterministic", "openai"),
    ),
    SettingSpec(
        name="ai_default_model",
        value_type=str,
        default="",
        settings_key=AI_DEFAULT_MODEL,
        capability_required=_CAPABILITY,
        hint=(
            "Default model identifier for the chosen provider. Leave "
            "empty to use the provider's own default."
        ),
        validator=_validate_str,
    ),
    SettingSpec(
        name="ai_minimum_level_default",
        value_type=int,
        default=2,
        settings_key=AI_MINIMUM_LEVEL_DEFAULT,
        capability_required=_CAPABILITY,
        hint=(
            "Default minimum XP level required to talk to the bot "
            "naturally. Channels, categories, and roles may override "
            "this in M2."
        ),
        validator=_validate_non_negative_int,
        input_hint="numeric_presets",
        presets=(0, 1, 2, 3, 5, 10),
    ),
    SettingSpec(
        name="ai_cooldown_seconds",
        value_type=int,
        default=30,
        settings_key=AI_COOLDOWN_SECONDS,
        capability_required=_CAPABILITY,
        hint=(
            "Seconds between natural-language replies per user. Zero "
            "disables the cooldown."
        ),
        validator=_validate_non_negative_int,
        input_hint="numeric_presets",
        presets=(0, 15, 30, 60, 120, 300),
    ),
    SettingSpec(
        name="ai_fresh_user_mention_allowance",
        value_type=int,
        default=1,
        settings_key=AI_FRESH_USER_MENTION_ALLOWANCE,
        capability_required=_CAPABILITY,
        hint=(
            "How many @-mention replies a fresh user (below the "
            "minimum level) is allowed before the level gate kicks in."
        ),
        validator=_validate_non_negative_int,
        input_hint="numeric_presets",
        presets=(0, 1, 3, 5, 10),
    ),
    SettingSpec(
        name="ai_guild_instruction_profile",
        value_type=str,
        default="",
        settings_key=AI_GUILD_INSTRUCTION_PROFILE,
        capability_required=_CAPABILITY,
        hint=(
            "Free-text guild-wide instruction body that prefixes every "
            "AI prompt for this guild. Transitional scalar seed: M2 "
            "backfills this into a typed ai_instruction_profile row "
            "named 'default' and the typed table becomes the runtime "
            "source of truth."
        ),
        validator=_validate_str,
    ),
)


AI_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="ai",
    bindings=AI_BINDINGS,
    settings=AI_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the AI subsystem schema. Called from ``AICog.cog_load``.

    Re-registration-safe (the underlying registry logs and replaces).
    """
    from core.runtime import subsystem_schema

    subsystem_schema.register(AI_CONFIG_SCHEMA)


__all__ = [
    "AI_BINDINGS",
    "AI_CONFIG_SCHEMA",
    "AI_SETTINGS",
    "register_schemas",
]
