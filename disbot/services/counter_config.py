"""Counter policy — the config read model for server counters v1.

Server counters (owner decision Q-0110): keep channel names showing a live
server stat.  Mirrors :mod:`services.welcome_config` and
:mod:`services.automod_config` exactly — the behaviour is loaded **once** into a
frozen read model so the rename loop and the status command share identical
config resolution.  This module owns:

* the canonical **default constants** (one source of truth shared by the
  :class:`SettingSpec` declarations in ``cogs/counters/schemas.py`` and by
  :func:`load_policy`'s fallbacks);
* :class:`CounterPolicy`, the frozen read model, plus its :attr:`active`
  enumeration of bound (kind, channel_id, template) counters;
* :func:`load_policy`, which composes the typed values via
  :func:`services.settings_resolution.resolve_value`;
* :func:`render_counter_name`, the injection-safe ``{count}`` substitution
  shared by the rename loop and the status panel.

The settings are stored as ordinary scalar guild settings (the legacy KV
table); there is **no migration** — the keys live in
:mod:`utils.settings_keys.counters` and are operator-editable through the
existing ``!settings`` widget dispatcher.

Cycle discipline (mirrors :mod:`services.welcome_config`): the only
cross-package import (``settings_resolution``) is function-local; top-level
imports are stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

SUBSYSTEM = "counters"

# ---------------------------------------------------------------------------
# Counter kinds — the three Q-0110 stats. Each maps to one channel binding +
# one name template.
# ---------------------------------------------------------------------------

KIND_TOTAL = "total"  # total members (guild.member_count)
KIND_HUMANS = "humans"  # non-bot members
KIND_BOTS = "bots"  # bots

KINDS: tuple[str, ...] = (KIND_TOTAL, KIND_HUMANS, KIND_BOTS)

# Discord channel names cap at 100 chars; templates are short so a six-figure
# count still fits comfortably.
MAX_TEMPLATE_LENGTH = 80
MAX_CHANNEL_NAME_LENGTH = 100

# ---------------------------------------------------------------------------
# Canonical defaults — the single source of truth.
#
# ``cogs/counters/schemas.py`` imports these for its SettingSpec ``default=``
# values; :func:`load_policy` uses them as the ``resolve_value`` fallback, so a
# spec default and a policy default can never silently drift (pinned by the
# schema test).  The master flag defaults OFF and every channel defaults
# unbound so a fresh guild is unaffected.
# ---------------------------------------------------------------------------

DEFAULT_ENABLED = False  # master switch
DEFAULT_CHANNEL = ""  # channel id string; empty = counter unbound
DEFAULT_TOTAL_TEMPLATE = "👥 Members: {count}"
DEFAULT_HUMANS_TEMPLATE = "🧑 Humans: {count}"
DEFAULT_BOTS_TEMPLATE = "🤖 Bots: {count}"


@dataclass(frozen=True)
class CounterPolicy:
    """Resolved counter behaviour for one guild.

    ``frozen`` so it can be cached/compared safely.  :attr:`active` folds the
    master switch + each binding into the list of counters the loop should
    actually maintain.
    """

    enabled: bool = DEFAULT_ENABLED
    total_channel_id: int | None = None
    humans_channel_id: int | None = None
    bots_channel_id: int | None = None
    total_template: str = DEFAULT_TOTAL_TEMPLATE
    humans_template: str = DEFAULT_HUMANS_TEMPLATE
    bots_template: str = DEFAULT_BOTS_TEMPLATE

    @property
    def active(self) -> tuple[tuple[str, int, str], ...]:
        """Bound counters as ``(kind, channel_id, template)`` — empty if off.

        Gated by the master switch: a disabled policy maintains nothing even
        when channels are bound.
        """
        if not self.enabled:
            return ()
        out: list[tuple[str, int, str]] = []
        for kind, channel_id, template in (
            (KIND_TOTAL, self.total_channel_id, self.total_template),
            (KIND_HUMANS, self.humans_channel_id, self.humans_template),
            (KIND_BOTS, self.bots_channel_id, self.bots_template),
        ):
            if channel_id is not None:
                out.append((kind, channel_id, template))
        return tuple(out)

    @property
    def any_bound(self) -> bool:
        """True when at least one counter is bound (still gated by ``enabled``)."""
        return bool(self.active)


# ---------------------------------------------------------------------------
# Curated template presets (counters completion punch #1).
#
# A small catalog of ready-made ``{count}`` template sets so an operator can
# adopt a coherent look in one step instead of hand-typing three templates.
# Pure data: the apply path (``cogs.counters_cog``) writes each kind's template
# through the audited ``SettingsMutationPipeline``, exactly as the per-template
# ``!settings`` widget does — so no validation or audit is bypassed.  The
# ``default`` preset is byte-identical to the canonical defaults above.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CounterPreset:
    """One curated set of ``{count}`` templates (one per counter kind)."""

    key: str
    label: str
    templates: dict[str, str]  # kind -> template

    def template_for(self, kind: str) -> str:
        """Template for ``kind``, falling back to the canonical default."""
        return self.templates.get(kind, _DEFAULT_TEMPLATE_BY_KIND[kind])


_DEFAULT_TEMPLATE_BY_KIND: dict[str, str] = {
    KIND_TOTAL: DEFAULT_TOTAL_TEMPLATE,
    KIND_HUMANS: DEFAULT_HUMANS_TEMPLATE,
    KIND_BOTS: DEFAULT_BOTS_TEMPLATE,
}

TEMPLATE_PRESETS: tuple[CounterPreset, ...] = (
    CounterPreset(
        key="default",
        label="Default — emoji + label",
        templates={
            KIND_TOTAL: DEFAULT_TOTAL_TEMPLATE,
            KIND_HUMANS: DEFAULT_HUMANS_TEMPLATE,
            KIND_BOTS: DEFAULT_BOTS_TEMPLATE,
        },
    ),
    CounterPreset(
        key="minimal",
        label="Minimal — label only, no emoji",
        templates={
            KIND_TOTAL: "Members: {count}",
            KIND_HUMANS: "Humans: {count}",
            KIND_BOTS: "Bots: {count}",
        },
    ),
    CounterPreset(
        key="brackets",
        label="Brackets — compact count in brackets",
        templates={
            KIND_TOTAL: "Members [{count}]",
            KIND_HUMANS: "Humans [{count}]",
            KIND_BOTS: "Bots [{count}]",
        },
    ),
    CounterPreset(
        key="bullet",
        label="Bullet — separator dot",
        templates={
            KIND_TOTAL: "👥 Members • {count}",
            KIND_HUMANS: "🧑 Humans • {count}",
            KIND_BOTS: "🤖 Bots • {count}",
        },
    ),
)

# Lookup keyed by preset key — built once (the catalog is immutable).
_PRESETS_BY_KEY: dict[str, CounterPreset] = {p.key: p for p in TEMPLATE_PRESETS}


def get_preset(key: str) -> CounterPreset | None:
    """Return the :class:`CounterPreset` for ``key`` (case-insensitive), or None."""
    return _PRESETS_BY_KEY.get(key.strip().lower())


# The ``SettingSpec.name`` (in ``cogs/counters/schemas.py``) that stores each
# kind's template — the apply path writes through these via the pipeline.
TEMPLATE_SETTING_BY_KIND: dict[str, str] = {
    KIND_TOTAL: "total_template",
    KIND_HUMANS: "humans_template",
    KIND_BOTS: "bots_template",
}


def preset_setting_writes(preset: CounterPreset) -> tuple[tuple[str, str], ...]:
    """Return the ``(setting_name, template)`` writes that apply ``preset``.

    Pure: maps the preset's per-kind templates onto the three template
    ``SettingSpec`` names in kind order.  The cog feeds each pair to
    :class:`services.settings_mutation.SettingsMutationPipeline` so coercion,
    validation, audit, and the capability check all run unchanged.
    """
    return tuple(
        (TEMPLATE_SETTING_BY_KIND[kind], preset.template_for(kind)) for kind in KINDS
    )


def parse_id(raw: object) -> int | None:
    """Parse a single id setting (channel) into an int, or None.

    Tolerant: a blank or malformed value degrades to "unbound" rather than
    raising, so a fat-fingered id never disables the whole policy load.
    """
    if raw is None:
        return None
    token = str(raw).strip()
    if not token:
        return None
    try:
        return int(token)
    except ValueError:
        return None


def render_counter_name(template: str, count: int) -> str:
    """Render a counter channel name, ``{count}`` expanded + length-capped.

    Uses plain ``str.replace`` (not ``str.format``) so a stray ``{`` in the
    template never raises, and truncates to Discord's 100-char channel-name
    limit as a final safety net.
    """
    name = template.replace("{count}", f"{count:,}")
    return name[:MAX_CHANNEL_NAME_LENGTH]


async def load_policy(guild_id: int) -> CounterPolicy:
    """Load the effective :class:`CounterPolicy` for ``guild_id``.

    Each field resolves through :func:`services.settings_resolution.resolve_value`
    so coercion, validation, and provenance stay centralised; a missing or
    malformed stored value transparently falls back to the canonical default.
    """
    from services.settings_resolution import resolve_value

    enabled = await resolve_value(guild_id, SUBSYSTEM, "enabled", DEFAULT_ENABLED)
    total_channel = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "total_channel",
        DEFAULT_CHANNEL,
    )
    humans_channel = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "humans_channel",
        DEFAULT_CHANNEL,
    )
    bots_channel = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "bots_channel",
        DEFAULT_CHANNEL,
    )
    total_template = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "total_template",
        DEFAULT_TOTAL_TEMPLATE,
    )
    humans_template = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "humans_template",
        DEFAULT_HUMANS_TEMPLATE,
    )
    bots_template = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "bots_template",
        DEFAULT_BOTS_TEMPLATE,
    )

    return CounterPolicy(
        enabled=enabled,
        total_channel_id=parse_id(total_channel),
        humans_channel_id=parse_id(humans_channel),
        bots_channel_id=parse_id(bots_channel),
        total_template=total_template,
        humans_template=humans_template,
        bots_template=bots_template,
    )


__all__ = [
    "DEFAULT_BOTS_TEMPLATE",
    "DEFAULT_CHANNEL",
    "DEFAULT_ENABLED",
    "DEFAULT_HUMANS_TEMPLATE",
    "DEFAULT_TOTAL_TEMPLATE",
    "KINDS",
    "KIND_BOTS",
    "KIND_HUMANS",
    "KIND_TOTAL",
    "MAX_CHANNEL_NAME_LENGTH",
    "MAX_TEMPLATE_LENGTH",
    "SUBSYSTEM",
    "TEMPLATE_PRESETS",
    "TEMPLATE_SETTING_BY_KIND",
    "CounterPolicy",
    "CounterPreset",
    "get_preset",
    "preset_setting_writes",
    "load_policy",
    "parse_id",
    "render_counter_name",
]
