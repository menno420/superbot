"""Image-moderation subsystem schema — operator config for the image-mod stage.

Declares the typed guild-config schema for image moderation v1 (Q-0108): a
master switch, four per-category enable flags, the confidence threshold, and the
exempt role/channel safety valve.  All settings are scalar guild settings (the
legacy KV table) — **no migration**.  Declaring the :class:`SubsystemSchema`
makes image moderation an actionable Settings group surfaced through the existing
``!settings`` widget.

The ``default=`` values and validator bounds come from
:mod:`services.image_moderation_config` (the single source of truth shared with
:func:`services.image_moderation_config.load_policy`), so a spec default and a
policy default can never silently drift — pinned by ``test_image_moderation_schemas``.

Edit authority borrows the moderation configure capability
(``moderation.settings.configure``): image moderation *is* moderation's automated
image layer, so the same staff who configure moderation configure it.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from services.automod_config import parse_id_csv
from services.image_moderation_config import (
    DEFAULT_ENABLED,
    DEFAULT_EXEMPT_CHANNELS,
    DEFAULT_EXEMPT_ROLES,
    DEFAULT_HARASSMENT_ENABLED,
    DEFAULT_HATE_ENABLED,
    DEFAULT_SEXUAL_ENABLED,
    DEFAULT_THRESHOLD_PERCENT,
    DEFAULT_VIOLENCE_ENABLED,
    MAX_THRESHOLD_PERCENT,
    MIN_THRESHOLD_PERCENT,
)
from utils.settings_keys import (
    IMAGE_MODERATION_ENABLED,
    IMAGE_MODERATION_EXEMPT_CHANNELS,
    IMAGE_MODERATION_EXEMPT_ROLES,
    IMAGE_MODERATION_HARASSMENT_ENABLED,
    IMAGE_MODERATION_HATE_ENABLED,
    IMAGE_MODERATION_SEXUAL_ENABLED,
    IMAGE_MODERATION_THRESHOLD_PERCENT,
    IMAGE_MODERATION_VIOLENCE_ENABLED,
)

_IMAGE_MOD_CAPABILITY = "moderation.settings.configure"


def _validate_bool(value: object) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {value!r}")


def _validate_threshold(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"expected int, got {value!r}")
    if not (MIN_THRESHOLD_PERCENT <= value <= MAX_THRESHOLD_PERCENT):
        raise ValueError(
            f"must be between {MIN_THRESHOLD_PERCENT} and {MAX_THRESHOLD_PERCENT}",
        )


def _validate_id_csv(value: object) -> None:
    """Reject non-numeric tokens so a typo'd exempt list fails loudly.

    ``parse_id_csv`` itself is tolerant (it powers the read model and must never
    raise); this validator is the *write*-time gate that gives the operator
    feedback instead of silently dropping a bad id.
    """
    if not isinstance(value, str):
        raise ValueError(f"expected a comma-separated id string, got {value!r}")
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            int(token)
        except ValueError:
            raise ValueError(
                f"'{token}' is not a numeric id — use comma-separated ids",
            ) from None


_PRIVACY_HINT = (
    "  When on, the image URL is sent to OpenAI's free moderation endpoint "
    "for scanning — disclose external image analysis in your server rules."
)


IMAGE_MODERATION_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="enabled",
        value_type=bool,
        default=DEFAULT_ENABLED,
        settings_key=IMAGE_MODERATION_ENABLED,
        capability_required=_IMAGE_MOD_CAPABILITY,
        hint=(
            "Master switch for image moderation.  When off, no image is scanned "
            "or sent anywhere regardless of the per-category toggles.  Off by "
            "default — a fresh server is unaffected." + _PRIVACY_HINT
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="sexual_enabled",
        value_type=bool,
        default=DEFAULT_SEXUAL_ENABLED,
        settings_key=IMAGE_MODERATION_SEXUAL_ENABLED,
        capability_required=_IMAGE_MOD_CAPABILITY,
        hint="Delete + warn on images flagged sexual / sexual-minors content.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="violence_enabled",
        value_type=bool,
        default=DEFAULT_VIOLENCE_ENABLED,
        settings_key=IMAGE_MODERATION_VIOLENCE_ENABLED,
        capability_required=_IMAGE_MOD_CAPABILITY,
        hint="Delete + warn on images flagged violent / graphic content.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="harassment_enabled",
        value_type=bool,
        default=DEFAULT_HARASSMENT_ENABLED,
        settings_key=IMAGE_MODERATION_HARASSMENT_ENABLED,
        capability_required=_IMAGE_MOD_CAPABILITY,
        hint="Delete + warn on images flagged harassment content.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="hate_enabled",
        value_type=bool,
        default=DEFAULT_HATE_ENABLED,
        settings_key=IMAGE_MODERATION_HATE_ENABLED,
        capability_required=_IMAGE_MOD_CAPABILITY,
        hint="Delete + warn on images flagged hate content.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="threshold_percent",
        value_type=int,
        default=DEFAULT_THRESHOLD_PERCENT,
        settings_key=IMAGE_MODERATION_THRESHOLD_PERCENT,
        capability_required=_IMAGE_MOD_CAPABILITY,
        hint=(
            "Confidence (percent) a category score must reach before an image "
            "is removed.  Higher = fewer false positives (80 recommended)."
        ),
        validator=_validate_threshold,
        input_hint="numeric_presets",
        presets=(70, 80, 90),
    ),
    SettingSpec(
        name="exempt_roles",
        value_type=str,
        default=DEFAULT_EXEMPT_ROLES,
        settings_key=IMAGE_MODERATION_EXEMPT_ROLES,
        capability_required=_IMAGE_MOD_CAPABILITY,
        hint=(
            "Comma-separated role ids whose members' images are never scanned "
            "(staff, trusted, …).  Leave empty for none."
        ),
        validator=_validate_id_csv,
    ),
    SettingSpec(
        name="exempt_channels",
        value_type=str,
        default=DEFAULT_EXEMPT_CHANNELS,
        settings_key=IMAGE_MODERATION_EXEMPT_CHANNELS,
        capability_required=_IMAGE_MOD_CAPABILITY,
        hint=(
            "Comma-separated channel ids image moderation never scans "
            "(art, memes, NSFW-gated, …).  Leave empty for none."
        ),
        validator=_validate_id_csv,
    ),
)


IMAGE_MODERATION_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="image_moderation",
    settings=IMAGE_MODERATION_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the image-moderation subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(IMAGE_MODERATION_CONFIG_SCHEMA)


# Re-export the tolerant parser so callers import it from one place.
__all__ = [
    "IMAGE_MODERATION_CONFIG_SCHEMA",
    "IMAGE_MODERATION_SETTINGS",
    "parse_id_csv",
    "register_schemas",
]
