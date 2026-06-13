"""Counters subsystem schema — operator config for server stat channels.

Declares the typed guild-config schema for server counters v1 (Q-0110): a
master switch, three counter channel bindings (total / humans / bots), and a
name template per counter.  All settings are scalar guild settings (the legacy
KV table) — **no migration**.  Declaring the :class:`SubsystemSchema` makes
counters an actionable Settings group surfaced through the existing ``!settings``
widget.

The ``default=`` values come from :mod:`services.counter_config` (the single
source of truth shared with :func:`services.counter_config.load_policy`), so a
spec default and a policy default can never silently drift — pinned by
``test_counters_schemas``.  The channel settings carry ``input_hint="channel"``
so the S6 edit-flow renders a Discord channel picker (the id stores as a string).
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from services.counter_config import (
    DEFAULT_BOTS_TEMPLATE,
    DEFAULT_CHANNEL,
    DEFAULT_ENABLED,
    DEFAULT_HUMANS_TEMPLATE,
    DEFAULT_TOTAL_TEMPLATE,
    MAX_TEMPLATE_LENGTH,
)
from utils.settings_keys import (
    COUNTERS_BOTS_CHANNEL,
    COUNTERS_BOTS_TEMPLATE,
    COUNTERS_ENABLED,
    COUNTERS_HUMANS_CHANNEL,
    COUNTERS_HUMANS_TEMPLATE,
    COUNTERS_TOTAL_CHANNEL,
    COUNTERS_TOTAL_TEMPLATE,
)

_COUNTERS_CAPABILITY = "counters.settings.configure"


def _validate_bool(value: object) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {value!r}")


def _validate_id(value: object) -> None:
    """Accept an empty string (unbound) or a single numeric channel id."""
    if not isinstance(value, str):
        raise ValueError(f"expected a channel id string, got {value!r}")
    token = value.strip()
    if not token:
        return  # empty = unbound
    try:
        int(token)
    except ValueError:
        raise ValueError(f"'{token}' is not a numeric id") from None


def _validate_template(value: object) -> None:
    """A non-empty template within the length cap.

    ``{count}`` is substituted at render time by
    ``counter_config.render_counter_name`` (injection-safe), so any text is
    accepted — only emptiness and length are gated, keeping the rendered
    channel name within Discord's 100-char limit.
    """
    if not isinstance(value, str):
        raise ValueError(f"expected a template string, got {value!r}")
    if not value.strip():
        raise ValueError("counter template cannot be empty")
    if len(value) > MAX_TEMPLATE_LENGTH:
        raise ValueError(
            f"counter template must be <= {MAX_TEMPLATE_LENGTH} characters",
        )


COUNTERS_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="enabled",
        value_type=bool,
        default=DEFAULT_ENABLED,
        settings_key=COUNTERS_ENABLED,
        capability_required=_COUNTERS_CAPABILITY,
        hint=(
            "Master switch for server counters.  When off, no channel is "
            "renamed regardless of the bindings.  Off by default — a fresh "
            "server is unaffected."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="total_channel",
        value_type=str,
        default=DEFAULT_CHANNEL,
        settings_key=COUNTERS_TOTAL_CHANNEL,
        capability_required=_COUNTERS_CAPABILITY,
        hint=(
            "Channel whose name shows the total member count (a locked voice "
            "channel works well).  Leave unset to disable this counter."
        ),
        validator=_validate_id,
        input_hint="channel",
    ),
    SettingSpec(
        name="humans_channel",
        value_type=str,
        default=DEFAULT_CHANNEL,
        settings_key=COUNTERS_HUMANS_CHANNEL,
        capability_required=_COUNTERS_CAPABILITY,
        hint="Channel whose name shows the non-bot member count.  Unset to disable.",
        validator=_validate_id,
        input_hint="channel",
    ),
    SettingSpec(
        name="bots_channel",
        value_type=str,
        default=DEFAULT_CHANNEL,
        settings_key=COUNTERS_BOTS_CHANNEL,
        capability_required=_COUNTERS_CAPABILITY,
        hint="Channel whose name shows the bot count.  Unset to disable.",
        validator=_validate_id,
        input_hint="channel",
    ),
    SettingSpec(
        name="total_template",
        value_type=str,
        default=DEFAULT_TOTAL_TEMPLATE,
        settings_key=COUNTERS_TOTAL_TEMPLATE,
        capability_required=_COUNTERS_CAPABILITY,
        hint="Name template for the total counter.  Placeholder: {count}.",
        validator=_validate_template,
    ),
    SettingSpec(
        name="humans_template",
        value_type=str,
        default=DEFAULT_HUMANS_TEMPLATE,
        settings_key=COUNTERS_HUMANS_TEMPLATE,
        capability_required=_COUNTERS_CAPABILITY,
        hint="Name template for the humans counter.  Placeholder: {count}.",
        validator=_validate_template,
    ),
    SettingSpec(
        name="bots_template",
        value_type=str,
        default=DEFAULT_BOTS_TEMPLATE,
        settings_key=COUNTERS_BOTS_TEMPLATE,
        capability_required=_COUNTERS_CAPABILITY,
        hint="Name template for the bots counter.  Placeholder: {count}.",
        validator=_validate_template,
    ),
)


COUNTERS_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="counters",
    settings=COUNTERS_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the counters subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(COUNTERS_CONFIG_SCHEMA)


__all__ = [
    "COUNTERS_CONFIG_SCHEMA",
    "COUNTERS_SETTINGS",
    "register_schemas",
]
