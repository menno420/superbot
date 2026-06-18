"""Image-moderation policy — the config read model for the image-mod stage.

image moderation v1 (owner decision Q-0108): scan uploaded images against
OpenAI's free ``omni-moderation-latest`` endpoint.  Mirrors
:mod:`services.automod_config` exactly — the behaviour is loaded **once** into a
frozen read model so the pipeline stage and any future caller share identical
config resolution.  This module owns:

* the canonical **default constants** (one source of truth shared by the
  :class:`SettingSpec` declarations in ``cogs/image_moderation/schemas.py`` and
  by :func:`load_policy`'s fallbacks);
* :class:`ImageModerationPolicy`, the frozen read model;
* :func:`load_policy`, which composes the typed values via
  :func:`services.settings_resolution.resolve_value`.

The settings are stored as ordinary scalar guild settings (the legacy KV table);
there is **no migration** — the keys live in
:mod:`utils.settings_keys.image_moderation` and are operator-editable through the
existing ``!settings`` widget dispatcher.

The exempt-list parsing reuses :func:`services.automod_config.parse_id_csv`
(the same tolerant CSV-of-ids safety valve both reactive features share).

Cycle discipline (mirrors :mod:`services.automod_config`): the only
cross-package import (``settings_resolution``) is function-local; top-level
imports are stdlib + the sibling ``automod_config`` parser only.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.automod_config import parse_id_csv

SUBSYSTEM = "image_moderation"

# ---------------------------------------------------------------------------
# Canonical defaults — the single source of truth.
#
# ``cogs/image_moderation/schemas.py`` imports these for its SettingSpec
# ``default=`` values and validator bounds; :func:`load_policy` uses them as the
# ``resolve_value`` fallback.  A spec default and a policy default can therefore
# never silently drift (pinned by the schema test).
#
# Every flag defaults OFF so a fresh guild behaves exactly as it does today —
# no image is ever sent to an external API until an operator opts in.
# ---------------------------------------------------------------------------

DEFAULT_ENABLED = False  # master switch
DEFAULT_SEXUAL_ENABLED = False
DEFAULT_VIOLENCE_ENABLED = False
DEFAULT_HARASSMENT_ENABLED = False
DEFAULT_HATE_ENABLED = False

# Confidence threshold: a category trips when its score reaches this percent.
# Owner decision Q-0108 / research: action at >= 0.80 to bound false positives.
DEFAULT_THRESHOLD_PERCENT = 80
MIN_THRESHOLD_PERCENT = 50
MAX_THRESHOLD_PERCENT = 100

# Exempt safety valve — CSV of ids never acted on (shared shape with automod).
DEFAULT_EXEMPT_ROLES = ""
DEFAULT_EXEMPT_CHANNELS = ""


@dataclass(frozen=True)
class ImageModerationPolicy:
    """Resolved image-moderation behaviour for one guild.

    ``frozen`` so it can be cached/compared safely; the exempt collections are
    ``frozenset`` for the same reason.  Every category is gated by both the
    master :attr:`enabled` flag and its own per-category flag.
    """

    enabled: bool = DEFAULT_ENABLED
    sexual_enabled: bool = DEFAULT_SEXUAL_ENABLED
    violence_enabled: bool = DEFAULT_VIOLENCE_ENABLED
    harassment_enabled: bool = DEFAULT_HARASSMENT_ENABLED
    hate_enabled: bool = DEFAULT_HATE_ENABLED
    threshold_percent: int = DEFAULT_THRESHOLD_PERCENT
    exempt_role_ids: frozenset[int] = frozenset()
    exempt_channel_ids: frozenset[int] = frozenset()

    @property
    def any_category_enabled(self) -> bool:
        """True when at least one category could act (still gated by ``enabled``)."""
        return (
            self.sexual_enabled
            or self.violence_enabled
            or self.harassment_enabled
            or self.hate_enabled
        )

    def is_exempt_channel(self, channel_id: int | None) -> bool:
        """True when ``channel_id`` is on the exempt list (never scanned)."""
        return channel_id is not None and channel_id in self.exempt_channel_ids

    def is_exempt_member(self, role_ids: frozenset[int] | set[int]) -> bool:
        """True when any of ``role_ids`` is on the exempt list."""
        return bool(self.exempt_role_ids & frozenset(role_ids))


async def load_policy(guild_id: int) -> ImageModerationPolicy:
    """Load the effective :class:`ImageModerationPolicy` for ``guild_id``.

    Each field resolves through :func:`services.settings_resolution.resolve_value`
    so coercion, validation, and provenance stay centralised; a missing or
    malformed stored value transparently falls back to the canonical default.
    """
    from services.settings_resolution import resolve_value

    enabled = await resolve_value(guild_id, SUBSYSTEM, "enabled", DEFAULT_ENABLED)
    sexual_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "sexual_enabled",
        DEFAULT_SEXUAL_ENABLED,
    )
    violence_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "violence_enabled",
        DEFAULT_VIOLENCE_ENABLED,
    )
    harassment_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "harassment_enabled",
        DEFAULT_HARASSMENT_ENABLED,
    )
    hate_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "hate_enabled",
        DEFAULT_HATE_ENABLED,
    )
    threshold_percent = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "threshold_percent",
        DEFAULT_THRESHOLD_PERCENT,
    )
    exempt_roles_raw = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "exempt_roles",
        DEFAULT_EXEMPT_ROLES,
    )
    exempt_channels_raw = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "exempt_channels",
        DEFAULT_EXEMPT_CHANNELS,
    )

    return ImageModerationPolicy(
        enabled=enabled,
        sexual_enabled=sexual_enabled,
        violence_enabled=violence_enabled,
        harassment_enabled=harassment_enabled,
        hate_enabled=hate_enabled,
        threshold_percent=threshold_percent,
        exempt_role_ids=parse_id_csv(exempt_roles_raw),
        exempt_channel_ids=parse_id_csv(exempt_channels_raw),
    )
