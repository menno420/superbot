"""Phase 1d — Feature flag, environment tier, and rollout policy declarations.

This module declares the *types* — :class:`FeatureFlag`,
:class:`EnvironmentTier`, :class:`RolloutPolicy` — that Phase 2d's
storage + :class:`RolloutMutationPipeline` will consume.  Phase 1d
intentionally stops at declarations so subsystems can declare flags
during ``cog_load`` ahead of the runtime landing in Phase 2d.

Why declarations land before runtime:

* Phase 1d's :func:`utils.subsystem_registry.validate_registry`
  extension can validate that every flag referenced by a schema has a
  declaration here.
* Phase 2d's RolloutMutationPipeline ships behind ``FEATURE_FLAG_PRIMARY``
  itself — but by then every subsystem that wants a flag has already
  declared one, so the migration is mechanical.

Public surface:

* :class:`EnvironmentTier` — typed taxonomy of deployment environments.
* :class:`RolloutPolicy` — staged rollout description.
* :class:`FeatureFlag` — a typed declaration of a gated behavior.
* ``FeatureFlagRegistry`` operations: ``register``, ``get``,
  ``all_flags``.

Phase 2d adds:

* ``is_enabled(name, guild_id) -> bool`` runtime evaluator.
* ``feature_flag_state`` table + ``RolloutMutationPipeline``.
* Migration of existing env-var gates to declared flags.

Until Phase 2d lands, declared flags are *introspection only* — they
appear in ``!platform flags`` but cannot be mutated and their value is
``default`` everywhere.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("bot.feature_flags")


class EnvironmentTier(Enum):
    """Deployment-environment taxonomy.

    A guild's environment tier governs which experimental features it
    sees.  Phase 2d's :data:`environment_tier` table maps guild IDs to
    tiers; the owner guild + designated test guilds are seeded on
    install.

    Members (broadest → strictest exposure):

    PRODUCTION:
        Default for every guild.  Sees only stable flags.
    BETA:
        Designated guilds opted into pre-release features.
    CANARY:
        Smaller subset — typically the bot author's own server — that
        sees brand-new features ahead of beta.
    OWNER_GUILD_ONLY:
        Single guild owned by the platform operator.  Sees everything
        including unfinished work.
    DEVELOPMENT:
        Local dev environments.  Behavior identical to
        OWNER_GUILD_ONLY at runtime.
    """

    PRODUCTION = "production"
    BETA = "beta"
    CANARY = "canary"
    OWNER_GUILD_ONLY = "owner_guild_only"
    DEVELOPMENT = "development"


@dataclass(frozen=True)
class RolloutPolicy:
    """Staged rollout description for a :class:`FeatureFlag`.

    Fields:

    staged_guilds:
        Explicit guild IDs that have the flag enabled regardless of
        ``percentage_rollout``.
    percentage_rollout:
        Hash-based rollout percentage (0-100).  Phase 2d uses
        ``hash(guild_id) % 100 < percentage_rollout`` as the gate.
    tier_gate:
        Environment tier required to be eligible at all.  Guilds below
        this tier ignore the flag even if their ID is in
        ``staged_guilds`` or their hash falls under
        ``percentage_rollout``.
    """

    staged_guilds: tuple[int, ...] = ()
    percentage_rollout: int = 0
    tier_gate: EnvironmentTier = EnvironmentTier.PRODUCTION


@dataclass(frozen=True)
class FeatureFlag:
    """A typed declaration of a gated runtime behavior.

    Fields:

    name:
        Dotted identifier (e.g. ``"setup_wizard.enabled"``,
        ``"governance.delegation.enabled"``).
    description:
        Short description rendered by ``!platform flags``.
    default_value:
        Value returned by Phase 2d's ``is_enabled`` when no override
        applies.  Phase 2d's gate-check returns ``default_value`` for
        all flags until ``FEATURE_FLAG_PRIMARY`` is flipped.
    environment_overrides:
        Per-tier override map.  A guild's environment tier picks
        the value here before the rollout policy is consulted.
    rollout_policy:
        Optional staged-rollout description.  Consulted only when no
        environment override applies and the flag default is not used.
    owner:
        Subsystem name or platform component that owns the flag.
        Defaults to ``"platform"`` for flags declared in core modules.
    removal_target:
        Optional human-readable hint for when the flag should be
        retired (e.g. ``"Phase 7 stable"``).  Empty for permanent
        flags.
    """

    name: str
    description: str
    default_value: bool
    environment_overrides: dict[EnvironmentTier, bool] = field(default_factory=dict)
    rollout_policy: RolloutPolicy | None = None
    owner: str = "platform"
    removal_target: str = ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, FeatureFlag] = {}


def register(flag: FeatureFlag) -> None:
    """Register ``flag`` under its name.

    Re-registration is allowed (hot-reload-friendly) and logged.
    """
    if flag.name in _REGISTRY:
        logger.debug("feature_flags: re-registering flag %r", flag.name)
    _REGISTRY[flag.name] = flag


def get(name: str) -> FeatureFlag | None:
    """Return the declared flag for ``name``, or ``None``."""
    return _REGISTRY.get(name)


def all_flags() -> dict[str, FeatureFlag]:
    """Return a copy of the flag registry, keyed by name."""
    return dict(_REGISTRY)


def declared_names() -> list[str]:
    """Return all declared flag names, alphabetically sorted."""
    return sorted(_REGISTRY)


def _reset_for_tests() -> None:
    """Wipe the registry.  Tests call this in their setup/teardown fixture."""
    _REGISTRY.clear()


# ---------------------------------------------------------------------------
# Phase 1d default flag declarations
#
# These flags are declared here (not in subsystems) because they gate
# platform-level behavior introduced by the roadmap itself.  Phase 2d
# will move env-var-driven gates onto this registry; the declarations
# below sketch the shape.
# ---------------------------------------------------------------------------

# Phase 2a flag — flipped after resource runtime + selector refactor verified.
RESOURCES_UNIFIED = FeatureFlag(
    name="resources.unified",
    description="Selectors consume core/resources/ as the canonical discovery layer.",
    default_value=False,
    owner="platform",
    removal_target="Phase 2a stable",
)

# Phase 2b flag — flipped after binding backfill verifies on production guilds.
BINDINGS_PRIMARY = FeatureFlag(
    name="bindings.primary",
    description=(
        "subsystem_bindings is the primary source of bound channel/role values; "
        "legacy raw-id settings KV becomes read-only fallback."
    ),
    default_value=False,
    owner="platform",
    removal_target="Phase 2b stable",
)

# Phase 2c flag — flipped after participation tables verify on owner guild.
PARTICIPATION_ENABLED = FeatureFlag(
    name="participation.enabled",
    description="Per-user participation runtime (user_* tables) is live.",
    default_value=False,
    owner="platform",
    removal_target="Phase 2c stable",
)

# Phase 2d meta-flag — bootstrapped via env var until itself flipped.
FEATURE_FLAG_PRIMARY = FeatureFlag(
    name="feature_flag.primary",
    description=(
        "Feature flag runtime (Phase 2d) is authoritative for gate "
        "evaluation; env vars are back-compat fallback only."
    ),
    default_value=False,
    owner="platform",
    removal_target="Phase 2d stable",
)


def _register_builtins() -> None:
    """Register Phase 1d platform-level flags at import time."""
    register(RESOURCES_UNIFIED)
    register(BINDINGS_PRIMARY)
    register(PARTICIPATION_ENABLED)
    register(FEATURE_FLAG_PRIMARY)


_register_builtins()


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _feature_flags_snapshot() -> dict[str, Any]:
    """Snapshot provider for ``!platform flags``.

    Phase 1d returns declarations only.  Phase 2d will extend the
    snapshot with current stored values, environment-tier resolution,
    and rollout-decision counts.
    """
    flags = all_flags()
    return {
        "declared_total": len(flags),
        "by_owner": _flags_by_owner(flags),
        "by_name": {
            name: {
                "description": flag.description,
                "default_value": flag.default_value,
                "owner": flag.owner,
                "removal_target": flag.removal_target,
                "tier_gate": (
                    flag.rollout_policy.tier_gate.value
                    if flag.rollout_policy
                    else "none"
                ),
            }
            for name, flag in sorted(flags.items())
        },
    }


def _flags_by_owner(flags: dict[str, FeatureFlag]) -> dict[str, int]:
    by_owner: dict[str, int] = {}
    for flag in flags.values():
        by_owner[flag.owner] = by_owner.get(flag.owner, 0) + 1
    return dict(sorted(by_owner.items()))


def _register_diagnostics_providers() -> None:
    from services import diagnostics_service

    diagnostics_service.register("feature_flags", _feature_flags_snapshot)


_register_diagnostics_providers()


__all__ = [
    "BINDINGS_PRIMARY",
    "EnvironmentTier",
    "FEATURE_FLAG_PRIMARY",
    "FeatureFlag",
    "PARTICIPATION_ENABLED",
    "RESOURCES_UNIFIED",
    "RolloutPolicy",
    "all_flags",
    "declared_names",
    "get",
    "register",
]
