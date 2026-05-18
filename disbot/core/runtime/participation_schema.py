"""Phase 1b — Subsystem-owned user participation schema protocol.

A subsystem declares the *per-user* runtime shape it supports via a
:class:`ParticipationSchema` instance registered in ``cog_load``.  This
is a sibling protocol to :mod:`core.runtime.subsystem_schema` (Phase
1a); the two are deliberately kept separate because guild configuration
and per-user state are different runtime domains with different
authority models, audit semantics, cache lifecycles, and mutation
pipelines.

The schema enforces a structural separation:

* :class:`SubscriptionSpec` — opt-in / opt-out toggles for *participation*
  in a feature (e.g. "I participate in XP").
* :class:`VisibilityIntent` — toggles for *visibility surfaces*
  (e.g. "show my rank on the public leaderboard").
* :class:`NotificationIntent` — toggles for *messages the bot sends to
  the user* (e.g. "DM me when I level up").
* :class:`PreferenceSpec` — UX / UI preferences (e.g. "digest hourly",
  "compact embed style").

These are four distinct concerns and a :class:`ParticipationSchema`
must keep them in four distinct fields.  A subsystem MAY NOT collapse
them into a single ``dict[str, Any]`` — the structural test in
``tests/unit/schema/test_participation_separation.py`` enforces this.

Why the strict separation:

* A user might participate in XP (``SubscriptionSpec.enabled = True``)
  but suppress level-up DMs (``NotificationIntent`` disabled) AND hide
  their rank from the public leaderboard (``VisibilityIntent`` off) —
  these are three independent decisions with three different defaults,
  three different routing layers (Phase 6.5), and three different
  storage tables (Phase 2c).
* Mixing them into a single settings object reintroduces the god-object
  trap at the per-user layer.

Opt-in discipline:

* Subsystems with ``SubscriptionSpec.requires_optin = True`` default
  to ``opted_out`` until the user explicitly opts in.  Tournaments,
  automations, AI subsystems MUST use ``requires_optin = True``.
* Notification intents default to suppressed until the user opts into
  the parent subsystem (Phase 6.5 enforces this at delivery time).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger("bot.participation_schema")


class PreferenceValueType(Enum):
    """Coercion target for a :class:`PreferenceSpec` value."""

    STRING = "str"
    INT = "int"
    BOOL = "bool"
    FLOAT = "float"
    ENUM = "enum"  # value validated against a fixed set; spec carries the set


@dataclass(frozen=True)
class SubscriptionSpec:
    """Per-user participation toggle for a feature.

    Bound to the ``user_subscriptions`` table (Phase 2c).  A user with
    ``enabled = False`` does not participate at all; the feature behaves
    as if disabled for that user (XP not awarded, daily not claimable,
    etc.).  This is the broadest opt-out.

    Fields:

    name:
        Stable identifier (e.g. ``"levelups"`` for XP, ``"daily"`` for
        economy).  Combined with the subsystem name to form the storage
        key.
    description:
        Short human-readable label rendered by ``/myprofile``.
    default_enabled:
        Default participation state.  Subsystems that touch sensitive
        surfaces (tournaments, automations, AI) MUST set
        ``requires_optin=True``, which forces effective default off
        regardless of this field.
    requires_optin:
        If ``True``, the user must explicitly opt in.  Effective default
        is ``False`` for these subscriptions.
    capability_required:
        Three-part capability the user must hold to toggle.  Empty if
        the user can toggle their own subscription unconditionally
        (typical for opt-out flows).
    eligibility_rule:
        Optional ``(member) -> bool`` callable.  Returning ``False``
        forces ``enabled`` to be effectively off regardless of stored
        value (e.g. an age-gated subsystem).
    """

    name: str
    description: str
    default_enabled: bool
    requires_optin: bool = False
    capability_required: str = ""
    eligibility_rule: Callable[[Any], bool] | None = None


@dataclass(frozen=True)
class VisibilityIntent:
    """Per-user toggle for a visibility surface.

    Bound to the ``user_visibility_overrides`` table (Phase 2c) and
    consumed by Phase 6.5's :class:`visibility_filter`.

    A user with ``enabled = False`` is filtered out of leaderboards,
    public ranks, social feeds — whatever the intent names.  Unlike
    :class:`SubscriptionSpec`, disabling visibility does NOT disable
    participation; the user keeps earning XP, they're just hidden from
    the public surfaces.

    Fields:

    name:
        Dotted intent string (e.g. ``"xp.leaderboard.public"``,
        ``"tournaments.bracket.public"``).  The dotted prefix groups
        related intents.
    description:
        Short label rendered by ``/myprofile``.
    default_enabled:
        Default visibility state.
    """

    name: str
    description: str
    default_enabled: bool = True


@dataclass(frozen=True)
class NotificationIntent:
    """Per-user toggle for a category of bot-initiated messages.

    Bound (indirectly) to the ``user_subscriptions`` table when the
    subscription has notification semantics; consumed by Phase 6.5's
    :func:`notification_service.notify`.

    Notifications differ from subscriptions:

    * A *subscription* governs whether the user participates at all.
    * A *notification intent* governs whether the platform sends a
      message in a specific category, given the user is participating.

    Default suppression is the *binding rule*: notifications default
    OFF until the user explicitly opts in, even if the parent
    subscription is on.  This is enforced by Phase 6.5's suppression
    engine; declaring ``default_enabled=True`` here only takes effect
    AFTER the user has opted into the parent subscription.

    Fields:

    name:
        Dotted intent string (e.g. ``"xp.levelup"``,
        ``"economy.daily.reminder"``).
    description:
        Short label rendered by ``/myprofile``.
    default_enabled:
        Default delivery state, conditional on parent subscription
        being active.
    digestable:
        If ``True``, Phase 6.5's digest engine may bucket this intent
        instead of delivering individually (e.g. daily digest of XP
        levelups instead of one DM per level).
    """

    name: str
    description: str
    default_enabled: bool = False
    digestable: bool = False


@dataclass(frozen=True)
class PreferenceSpec:
    """Per-user UX / UI preference.

    Bound to the ``user_preferences`` table (Phase 2c).  Preferences
    are neither participation toggles nor visibility filters — they
    customize how the platform presents itself to the user (digest
    frequency, embed style, language hint).

    Fields:

    name:
        Stable identifier (e.g. ``"digest_frequency"``,
        ``"embed_style"``).
    description:
        Short label rendered by ``/myprofile``.
    value_type:
        Coercion target on read.
    default:
        Default value when unset.
    allowed_values:
        Optional tuple of allowed values (used when ``value_type ==
        PreferenceValueType.ENUM``).
    """

    name: str
    description: str
    value_type: PreferenceValueType
    default: Any
    allowed_values: tuple[Any, ...] = ()


@dataclass(frozen=True)
class ParticipationSchema:
    """A subsystem's complete per-user shape declaration.

    Registered in ``cog_load`` via :func:`register`.  The four fields
    are deliberately separate: a subsystem MUST NOT collapse
    participation, visibility, notifications, and preferences into a
    single bag.  ``tests/unit/schema/test_participation_separation.py``
    enforces this structurally.

    Fields:

    subsystem:
        Must match a key in :data:`utils.subsystem_registry.SUBSYSTEMS`.
    subscriptions:
        Top-level opt-in / opt-out toggles.
    visibility_intents:
        Visibility surface toggles.
    notification_intents:
        Notification delivery toggles.
    preference_specs:
        UX / UI preferences.
    version:
        Schema version; Phase 1 schemas start at ``1``.
    """

    subsystem: str
    subscriptions: tuple[SubscriptionSpec, ...] = ()
    visibility_intents: tuple[VisibilityIntent, ...] = ()
    notification_intents: tuple[NotificationIntent, ...] = ()
    preference_specs: tuple[PreferenceSpec, ...] = ()
    version: int = 1


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, ParticipationSchema] = {}


def register(schema: ParticipationSchema) -> None:
    """Register ``schema`` under its subsystem name.

    Re-registration is allowed (hot-reload-friendly) and emits a
    DEBUG-level log entry so accidental duplicates are visible.
    """
    if schema.subsystem in _REGISTRY:
        logger.debug(
            "participation_schema: re-registering schema for %r",
            schema.subsystem,
        )
    _REGISTRY[schema.subsystem] = schema


def get_schema(subsystem: str) -> ParticipationSchema | None:
    """Return the registered participation schema, or ``None``."""
    return _REGISTRY.get(subsystem)


def all_schemas() -> dict[str, ParticipationSchema]:
    """Return a copy of the participation registry, keyed by subsystem."""
    return dict(_REGISTRY)


def registered_subsystems() -> list[str]:
    """Return registered subsystems, alphabetically sorted."""
    return sorted(_REGISTRY)


def _reset_for_tests() -> None:
    """Wipe the registry.  Tests call this in their setup/teardown fixture."""
    _REGISTRY.clear()


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _participation_schemas_snapshot() -> dict[str, Any]:
    """Snapshot provider for ``!platform participation-schemas``."""
    schemas = all_schemas()
    return {
        "registered": len(schemas),
        "subscriptions_total": sum(len(s.subscriptions) for s in schemas.values()),
        "visibility_intents_total": sum(
            len(s.visibility_intents) for s in schemas.values()
        ),
        "notification_intents_total": sum(
            len(s.notification_intents) for s in schemas.values()
        ),
        "preferences_total": sum(len(s.preference_specs) for s in schemas.values()),
        "by_subsystem": {
            name: {
                "subscriptions": len(schema.subscriptions),
                "visibility_intents": len(schema.visibility_intents),
                "notification_intents": len(schema.notification_intents),
                "preferences": len(schema.preference_specs),
                "version": schema.version,
            }
            for name, schema in sorted(schemas.items())
        },
    }


def _register_diagnostics_providers() -> None:
    from services import diagnostics_service

    diagnostics_service.register(
        "participation_schemas",
        _participation_schemas_snapshot,
    )


_register_diagnostics_providers()


__all__ = [
    "NotificationIntent",
    "ParticipationSchema",
    "PreferenceSpec",
    "PreferenceValueType",
    "SubscriptionSpec",
    "VisibilityIntent",
    "all_schemas",
    "get_schema",
    "register",
    "registered_subsystems",
]
