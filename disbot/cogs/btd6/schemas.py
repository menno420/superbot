"""BTD6 SubsystemSchema.

M4 landed the first BTD6 binding: ``btd6.strategy_submission_channel``.
The central natural-language stage still decides whether the user
may talk naturally; this binding decides whether a message in the
bound channel is treated as a strategy intake rather than a question.

Settings Phase 2 (Q-0064, 2026-06-09) promoted the **version-announcement
channel** to a first-class binding: ``services.btd6_version_announce``
reads the binding first and falls back to the legacy
``BTD6_VERSION_ANNOUNCEMENT_CHANNEL`` KV pointer (the typed
``!btd6 ops announcechannel`` command still writes the KV lane — write-path
convergence is settings Phase 3 territory).
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
)

_CAPABILITY = "btd6.settings.configure"


BTD6_BINDINGS: tuple[BindingSpec, ...] = (
    BindingSpec(
        name="strategy_submission_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel where natural-language strategy submissions are "
            "routed into the BTD6 strategy review pipeline. Leave "
            "unbound to disable the strategy-intake path; admins can "
            "still submit strategies via the dedicated command."
        ),
        capability_required=_CAPABILITY,
    ),
    BindingSpec(
        name="version_announce_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel where new BTD6 game versions are announced. When "
            "bound it takes precedence over the legacy "
            "`!btd6 ops announcechannel` pointer; leave both unset to "
            "disable announcements."
        ),
        capability_required=_CAPABILITY,
    ),
)


BTD6_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="btd6",
    bindings=BTD6_BINDINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the BTD6 subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(BTD6_CONFIG_SCHEMA)


__all__ = ["BTD6_BINDINGS", "BTD6_CONFIG_SCHEMA", "register_schemas"]
