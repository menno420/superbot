"""Feature flag declarations + runtime evaluator (Phase 1d + Phase 2d PR-2).

This module owns:

* The **declaration** types — :class:`FeatureFlag`,
  :class:`EnvironmentTier`, :class:`RolloutPolicy` (Phase 1d).  These
  let subsystems register flags during ``cog_load``.
* The **runtime evaluator** — :func:`is_enabled` (Phase 2d, PR-2).
  Resolves a flag's effective value for a given guild by consulting,
  in order: emergency env override → ``feature_flag.primary`` gate →
  per-guild DB override → global DB override → environment-tier policy
  → deterministic rollout hash → declared default.

The mutation pipeline (:class:`services.rollout_mutation.RolloutMutationPipeline`)
and the event-driven cache invalidation ship in PR-3.  Until then the
evaluator's cache uses TTL as the only invalidation primitive; callers
may also invoke :func:`clear_cache` explicitly.

Bootstrap policy (intentional ordering):

1. ``SUPERBOT_FF_<FLAG>=on|off`` env override wins for ANY flag.
   This is the permanent platform-owner escape hatch.
2. ``feature_flag.primary`` is the meta-flag.  When OFF, the evaluator
   returns each flag's declared default and the DB is never consulted.
   ``feature_flag.primary`` itself is resolved by env + declaration ONLY
   — its value is never read from the DB.  This protects the bootstrap
   path while the runtime is being proven on a deployment.
3. When ``feature_flag.primary`` is ON, the DB-backed resolution runs.
4. Any DB error during resolution falls back to the declared default
   and emits the ``feature_flag.bootstrap_fallback`` metric — never
   raises.

Public surface:

* :class:`EnvironmentTier`, :class:`RolloutPolicy`, :class:`FeatureFlag`
* ``FeatureFlagRegistry`` operations: ``register``, ``get``,
  ``all_flags``
* :func:`is_enabled` (Phase 2d evaluator)
* :func:`clear_cache` (manual invalidation; PR-3 adds event-driven)
* :func:`resolve_with_provenance` (used by diagnostics; returns the
  decision and the source it came from)
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

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
    audience:
        ``"operator"`` for flags an operator is meant to toggle;
        ``"internal"`` (default) for migration / kill-switch gates that
        are platform-internal.  Drives the operator/internal split in
        ``!platform flags`` and is surfaced in the flag-detail view.
    db_editable:
        ``False`` for flags whose per-guild DB override the evaluator
        ignores (e.g. the env-only ``feature_flag.primary`` meta-flag).
        The flag-manager UI refuses to write overrides for these so it
        never offers a no-op control.
    label:
        Optional plain-language operator-facing name.  Falls back to the
        dotted ``name`` when empty.  Display-only — the ``name`` stays
        the stable key used for storage, env vars, and audit.
    """

    name: str
    description: str
    default_value: bool
    environment_overrides: dict[EnvironmentTier, bool] = field(default_factory=dict)
    rollout_policy: RolloutPolicy | None = None
    owner: str = "platform"
    removal_target: str = ""
    audience: Literal["operator", "internal"] = "internal"
    db_editable: bool = True
    label: str = ""


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
    """Wipe the registry + cache + metrics.

    Tests call this in their setup/teardown fixture so per-test state
    cannot leak via the module-level dicts / counters.
    """
    _REGISTRY.clear()
    _CACHE.clear()
    global _BOOTSTRAP_FALLBACK_COUNT
    _BOOTSTRAP_FALLBACK_COUNT = 0


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
    label="Unified resource discovery (internal rollout gate)",
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
    label="Bindings as primary source (internal rollout gate)",
)

# Phase 2c flag — flipped after participation tables verify on owner guild.
PARTICIPATION_ENABLED = FeatureFlag(
    name="participation.enabled",
    description="Per-user participation runtime (user_* tables) is live.",
    default_value=False,
    owner="platform",
    removal_target="Phase 2c stable",
    label="Participation runtime (internal rollout gate)",
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
    # Env-only meta-flag: the evaluator never reads a DB override for it
    # (see resolve_with_provenance), so the editor must not offer one.
    db_editable=False,
    label="Feature-flag runtime gate (env-only, internal)",
)

# S4 flag — kill-switch infrastructure for future Settings Manager UI
# (S5+) consumers of :class:`services.settings_mutation.SettingsMutationPipeline`.
# The pipeline itself does NOT consult this flag — it writes whenever
# it is called.  Mirrors how BINDINGS_PRIMARY is declared centrally
# but only :mod:`core.runtime.config_arbitration` consumes it.
SETTINGS_MUTATION_PRIMARY = FeatureFlag(
    name="settings.mutation.primary",
    description=(
        "services.settings_mutation.SettingsMutationPipeline is the primary "
        "write path for scalar SettingSpec values; future S5+ UI consumers "
        "gate their routing on this flag.  The pipeline itself does not "
        "consult the flag — its existence alone changes no behaviour."
    ),
    default_value=False,
    owner="platform",
    removal_target="S5+ stable",
    label="Settings mutation pipeline primary (internal kill-switch)",
)

# S4.5 flag — kill-switch infrastructure for future ResourceProvisioning
# UI (S7+ logging-create flow, S10 per-subsystem setup packs) consumers
# of :class:`services.resource_provisioning.ResourceProvisioningPipeline`.
# The pipeline itself does NOT consult this flag — it provisions
# whenever explicitly invoked.  Mirrors the SETTINGS_MUTATION_PRIMARY
# pattern.
RESOURCE_PROVISIONING_PRIMARY = FeatureFlag(
    name="resource_provisioning.primary",
    description=(
        "services.resource_provisioning.ResourceProvisioningPipeline is the "
        "primary creator/binder of Discord resources (channels/roles/"
        "categories); future S7+/S10 UI consumers gate their routing on "
        "this flag.  The pipeline itself does not consult the flag — its "
        "existence alone changes no behaviour."
    ),
    default_value=False,
    owner="platform",
    removal_target="S10+ stable",
    label="Resource provisioning pipeline primary (internal kill-switch)",
)

# S5 flag — gates the user-facing Settings Manager cog (!settings).
# The cog ALWAYS loads and registers in SUBSYSTEMS so help/admin/menu
# discoverability stays stable; the flag gates the runtime *behaviour*
# of the !settings command and the build_help_menu_view hook so
# operators can disable the cog without breaking the registry.
#
# PR #8 flipped the default to ON now that PR #5/#6 routed XP and
# Economy log-channel writes through SettingsMutationPipeline (closing
# the audit gap) and PR #7 added channel/role/numeric-presets input
# modes (closing the input-coverage gap).  The kill-switch path is
# unchanged: operators flip OFF either via the
# ``SUPERBOT_FF_SETTINGS__MANAGER_COG__ENABLED=off`` env override or
# the future ``!platform flags set …`` command.  When OFF, the cog
# still loads (registry stability) but ``!settings`` returns the
# disabled embed.
SETTINGS_MANAGER_COG_ENABLED = FeatureFlag(
    name="settings.manager_cog.enabled",
    description=(
        "Gates the runtime behaviour of the user-facing Settings Manager "
        "cog (!settings) introduced in S5.  Default ON since PR #8 — the "
        "cog opens the Settings hub for administrators by default.  "
        "Operators can kill-switch it OFF via the "
        "SUPERBOT_FF_SETTINGS__MANAGER_COG__ENABLED=off env override or the "
        "(future) !platform flags command; when OFF the cog returns a "
        "clearly-worded 'disabled' embed instead."
    ),
    default_value=True,
    owner="platform",
    removal_target="S11 stable",
    audience="operator",
    label="Settings menu (!settings)",
)


YOUTUBE_CONTEXT_ENABLED = FeatureFlag(
    name="youtube.context.enabled",
    description=(
        "Enable YouTube URL metadata/transcript context for AI responses. "
        "When ON the AI pipeline fetches video metadata and transcript "
        "excerpts and includes them as grounded facts. "
        "Env override: SUPERBOT_FF_YOUTUBE_CONTEXT_ENABLED=on. "
        "Requires YOUTUBE_API_KEY to be set; if missing the flag is "
        "effectively off even when enabled here."
    ),
    default_value=False,
    owner="ai",
    audience="operator",
    label="YouTube context for AI replies",
)


def _register_builtins() -> None:
    """Register Phase 1d platform-level flags at import time."""
    register(RESOURCES_UNIFIED)
    register(BINDINGS_PRIMARY)
    register(PARTICIPATION_ENABLED)
    register(FEATURE_FLAG_PRIMARY)
    register(SETTINGS_MUTATION_PRIMARY)
    register(RESOURCE_PROVISIONING_PRIMARY)
    register(SETTINGS_MANAGER_COG_ENABLED)
    register(YOUTUBE_CONTEXT_ENABLED)


_register_builtins()


# ---------------------------------------------------------------------------
# Phase 2d evaluator — is_enabled + cache + bootstrap policy
# ---------------------------------------------------------------------------

# Sources that can deliver a resolved value, surfaced via diagnostics so
# operators see exactly why the evaluator returned what it did.
_SOURCE_ENV = "env"
_SOURCE_BOOTSTRAP_FALLBACK = "bootstrap_fallback"  # DB unreachable or off
_SOURCE_DB_GUILD = "db_guild"
_SOURCE_DB_GLOBAL = "db_global"
_SOURCE_TIER = "tier"
_SOURCE_ROLLOUT = "rollout"
_SOURCE_DEFAULT = "default"

# Cache TTL.  PR-3 adds event-driven invalidation; until then TTL is
# the only invalidation primitive aside from explicit clear_cache.
# Five minutes balances "operator DB change reflected without restart"
# against hot-path read pressure (every interaction hits is_enabled).
_CACHE_TTL_SECS = 300.0

# Cache value: (resolved_bool, source_string, expires_at_monotonic).
_CACHE: dict[tuple[str, int | None], tuple[bool, str, float]] = {}

# Metric counter for fallback rate.  Hooked into services.metrics in a
# follow-up PR; until then this is the in-process visible counter that
# tests can assert on.
_BOOTSTRAP_FALLBACK_COUNT = 0


def _env_override_key(flag_name: str) -> str:
    """Translate a dotted flag name into a SUPERBOT_FF_<NAME> env var."""
    return "SUPERBOT_FF_" + flag_name.replace(".", "_").upper()


def _env_override(flag_name: str) -> bool | None:
    """Return ``True`` / ``False`` for an env override, else ``None``.

    Accepts the same truthy/falsy literals as the rest of the codebase
    (``true``, ``yes``, ``on``, ``1`` vs. ``false``, ``no``, ``off``,
    ``0``).  Unknown values are ignored (treated as "no override").
    """
    raw = os.environ.get(_env_override_key(flag_name))
    if raw is None:
        return None
    lower = raw.strip().lower()
    if lower in ("true", "yes", "on", "1"):
        return True
    if lower in ("false", "no", "off", "0"):
        return False
    logger.warning(
        "feature_flags: env %s=%r is not a recognized boolean — ignoring",
        _env_override_key(flag_name),
        raw,
    )
    return None


def _rollout_bucket(flag_name: str, guild_id: int) -> int:
    """Deterministic 0..99 bucket for ``(flag, guild)``.

    Stdlib-only (``hashlib.sha256``); no new dependency.  Stable across
    Python versions and processes — the same pair always lands in the
    same bucket.
    """
    digest = hashlib.sha256(f"{flag_name}:{guild_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % 100


def _normalize_state(state: str) -> str:
    """Lowercase + strip; protects against operator typos in DB rows."""
    return state.strip().lower() if state else ""


def _state_to_decision(
    state: str,
    *,
    flag: FeatureFlag,
    guild_tier: str | None,
) -> bool:
    """Turn a stored ``state`` string into a boolean.

    ``on``/``off`` are hard overrides.  Tier names
    (``owner``/``canary``/``beta``/``production``) mean "enabled if the
    guild's environment_tier is at or above this level".  Unknown
    strings fall back to the declared default and log a WARNING.
    """
    normalized = _normalize_state(state)
    if normalized == "on":
        return True
    if normalized == "off":
        return False
    if normalized in ("owner", "canary", "beta", "production"):
        return _tier_meets(guild_tier, normalized)
    logger.warning(
        "feature_flags: unknown stored state %r for %r — using default",
        state,
        flag.name,
    )
    return flag.default_value


# Tier ordering — lower index = more restricted exposure.  A guild
# whose tier is "owner_guild_only" sees flags gated at "owner" or
# below; a "canary" guild sees "canary" + "beta" + "production"; etc.
_TIER_ORDER = {
    "owner_guild_only": 0,
    "development": 0,
    "owner": 0,
    "canary": 1,
    "beta": 2,
    "production": 3,
}


def _tier_meets(guild_tier: str | None, required: str) -> bool:
    """``True`` when ``guild_tier`` is at-or-above ``required``."""
    guild_level = _TIER_ORDER.get((guild_tier or "production").lower(), 3)
    required_level = _TIER_ORDER.get(required.lower(), 3)
    return guild_level <= required_level


@dataclass(frozen=True)
class _Decision:
    """Internal: the evaluator's result + the source it came from."""

    value: bool
    source: str


async def _resolve_from_db(
    flag: FeatureFlag,
    guild_id: int | None,
) -> _Decision:
    """DB-backed resolution.  Caller has already passed bootstrap gates."""
    # Local imports to keep cycle-sensitive cycles unaffected.
    from utils.db import environment_tiers as et_db
    from utils.db import feature_flag_state as ff_db

    # Per-guild override beats everything else in the DB layer.
    if guild_id is not None:
        guild_row = await ff_db.get_guild_override(flag.name, guild_id)
        if guild_row is not None:
            guild_tier = await et_db.get_tier(guild_id)
            value = _state_to_decision(
                guild_row["state"],
                flag=flag,
                guild_tier=guild_tier,
            )
            return _Decision(value, _SOURCE_DB_GUILD)

    # Global override.
    global_row = await ff_db.get_global_override(flag.name)
    if global_row is not None:
        guild_tier = await et_db.get_tier(guild_id) if guild_id is not None else None
        value = _state_to_decision(
            global_row["state"],
            flag=flag,
            guild_tier=guild_tier,
        )
        normalized = _normalize_state(global_row["state"])
        # Resolution rules for global overrides (intentional):
        #   * 'on'  → hard enable, short-circuit True.
        #   * 'off' → hard disable, short-circuit False.  This makes
        #             rollback safe: setting the global row to 'off'
        #             immediately disables the flag for every guild
        #             that does not carry a per-guild override.
        #   * tier name (canary/beta/production/owner) + matching guild
        #             tier → True via tier match.
        #   * tier name + non-matching guild tier → the global row is
        #             non-binding for this guild; fall through to the
        #             declared rollout policy.  The staged rollout may
        #             still grant access via staged_guilds or rollout
        #             percentage.
        if normalized in ("on", "off"):
            return _Decision(value, _SOURCE_DB_GLOBAL)
        if value:
            return _Decision(True, _SOURCE_DB_GLOBAL)
        # Non-matching tier name: do not short-circuit; rollout may grant.

    # Declared rollout policy.
    if flag.rollout_policy is not None and guild_id is not None:
        policy = flag.rollout_policy
        guild_tier = await et_db.get_tier(guild_id)
        if guild_id in policy.staged_guilds:
            if _tier_meets(guild_tier, policy.tier_gate.value):
                return _Decision(True, _SOURCE_TIER)
        if policy.tier_gate is not None and _tier_meets(
            guild_tier,
            policy.tier_gate.value,
        ):
            # Environment-tier override map.
            tier_enum = EnvironmentTier((guild_tier or "production").lower())
            if tier_enum in flag.environment_overrides:
                return _Decision(
                    flag.environment_overrides[tier_enum],
                    _SOURCE_TIER,
                )
            if policy.percentage_rollout > 0:
                bucket = _rollout_bucket(flag.name, guild_id)
                if bucket < policy.percentage_rollout:
                    return _Decision(True, _SOURCE_ROLLOUT)

    return _Decision(flag.default_value, _SOURCE_DEFAULT)


def _cache_get(flag_name: str, guild_id: int | None) -> _Decision | None:
    """Return a cached decision if still fresh, else ``None``."""
    entry = _CACHE.get((flag_name, guild_id))
    if entry is None:
        return None
    value, source, expires_at = entry
    if expires_at < time.monotonic():
        _CACHE.pop((flag_name, guild_id), None)
        return None
    return _Decision(value, source)


def _cache_put(flag_name: str, guild_id: int | None, decision: _Decision) -> None:
    """Store a decision with TTL."""
    _CACHE[(flag_name, guild_id)] = (
        decision.value,
        decision.source,
        time.monotonic() + _CACHE_TTL_SECS,
    )


def clear_cache(
    flag_name: str | None = None,
    guild_id: int | None = None,
) -> int:
    """Evict cached evaluator decisions.

    Until PR-3's event-driven invalidation lands, callers that mutate
    state directly (DB scripts, tests, the future RolloutMutationPipeline
    in its early form) call this to make the next ``is_enabled`` re-read.

    Filtering rules:

    * No arguments → drop every entry.
    * ``flag_name`` only → drop every guild's entry for that flag (and
      the global ``guild_id=None`` entry).
    * ``flag_name`` + ``guild_id`` → drop the single matching entry.
    * ``guild_id`` only → drop every flag's entry for that guild.

    Returns the number of entries removed.
    """
    if flag_name is None and guild_id is None:
        n = len(_CACHE)
        _CACHE.clear()
        return n
    to_drop = []
    for key in _CACHE:
        key_flag, key_guild = key
        if flag_name is not None and key_flag != flag_name:
            continue
        if guild_id is not None and key_guild != guild_id:
            continue
        to_drop.append(key)
    for key in to_drop:
        _CACHE.pop(key, None)
    return len(to_drop)


def _record_bootstrap_fallback() -> None:
    """Increment the in-process bootstrap fallback counter.

    A real Prometheus metric is wired in a follow-up PR; until then
    this counter is the test-observable signal.
    """
    global _BOOTSTRAP_FALLBACK_COUNT
    _BOOTSTRAP_FALLBACK_COUNT += 1


def bootstrap_fallback_count() -> int:
    """Return how many times the DB-unreachable fallback has fired."""
    return _BOOTSTRAP_FALLBACK_COUNT


def _reset_metrics_for_tests() -> None:
    """Test helper — reset the bootstrap fallback counter."""
    global _BOOTSTRAP_FALLBACK_COUNT
    _BOOTSTRAP_FALLBACK_COUNT = 0


async def resolve_with_provenance(
    flag_name: str,
    guild_id: int | None = None,
) -> _Decision:
    """Resolve a flag and return both the value and the source.

    Used by diagnostics so ``!platform flags`` can render the source
    column.  Internal — tests are welcome to call it but production
    callers should prefer :func:`is_enabled`.

    Resolution order (see module docstring for rationale):

    1. ``SUPERBOT_FF_<FLAG>`` env override (always wins).
    2. ``feature_flag.primary`` gate — if OFF, return declared default
       and bypass DB entirely.  Evaluating ``feature_flag.primary``
       itself bypasses the DB step too.
    3. Cache lookup.
    4. DB resolution (per-guild → global → tier → rollout → default).
    5. DB error → declared default + bootstrap-fallback metric.
    """
    # Step 1: env override
    env = _env_override(flag_name)
    if env is not None:
        return _Decision(env, _SOURCE_ENV)

    flag = _REGISTRY.get(flag_name)
    if flag is None:
        logger.warning(
            "feature_flags: is_enabled called for undeclared flag %r",
            flag_name,
        )
        return _Decision(False, _SOURCE_DEFAULT)

    # Step 2: feature_flag.primary gate.
    if flag_name == FEATURE_FLAG_PRIMARY.name:
        # Meta-flag: env-or-default only, never DB.
        return _Decision(flag.default_value, _SOURCE_DEFAULT)
    primary = await resolve_with_provenance(FEATURE_FLAG_PRIMARY.name, guild_id)
    if not primary.value:
        return _Decision(flag.default_value, _SOURCE_DEFAULT)

    # Step 3: cache
    cached = _cache_get(flag_name, guild_id)
    if cached is not None:
        return cached

    # Step 4 / 5: DB resolution with fallback
    try:
        decision = await _resolve_from_db(flag, guild_id)
    except Exception as exc:
        logger.warning(
            "feature_flags: DB unreachable for %r (guild=%r) — using default: %s",
            flag_name,
            guild_id,
            exc,
        )
        _record_bootstrap_fallback()
        decision = _Decision(flag.default_value, _SOURCE_BOOTSTRAP_FALLBACK)

    _cache_put(flag_name, guild_id, decision)
    return decision


async def is_enabled(flag_name: str, guild_id: int | None = None) -> bool:
    """Phase 2d evaluator entry point.

    Returns the effective boolean for ``flag_name`` in ``guild_id``'s
    context.  Resolution order, cache semantics, and the bootstrap
    fallback policy are documented on :func:`resolve_with_provenance`
    and at the top of this module.
    """
    decision = await resolve_with_provenance(flag_name, guild_id)
    return decision.value


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _feature_flags_snapshot() -> dict[str, Any]:
    """Snapshot provider for ``!platform flags``.

    Phase 2d (PR-2) extends the snapshot with cache size, fallback
    counter, and per-flag declared values.  Effective per-flag values
    require an async call so the diagnostics view falls back to
    declared defaults here; ``cogs/diagnostic_cog.py::flags`` does the
    per-flag async resolution and renders the source column.
    """
    flags = all_flags()
    return {
        "declared_total": len(flags),
        "by_owner": _flags_by_owner(flags),
        "by_audience": _flags_by_audience(flags),
        "cache_size": len(_CACHE),
        "bootstrap_fallback_count": _BOOTSTRAP_FALLBACK_COUNT,
        "by_name": {
            name: {
                "description": flag.description,
                "default_value": flag.default_value,
                "owner": flag.owner,
                "removal_target": flag.removal_target,
                "audience": flag.audience,
                "db_editable": flag.db_editable,
                "label": flag.label,
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


def _flags_by_audience(flags: dict[str, FeatureFlag]) -> dict[str, int]:
    by_audience: dict[str, int] = {}
    for flag in flags.values():
        by_audience[flag.audience] = by_audience.get(flag.audience, 0) + 1
    return dict(sorted(by_audience.items()))


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
    "RESOURCE_PROVISIONING_PRIMARY",
    "RESOURCES_UNIFIED",
    "RolloutPolicy",
    "SETTINGS_MANAGER_COG_ENABLED",
    "SETTINGS_MUTATION_PRIMARY",
    "all_flags",
    "bootstrap_fallback_count",
    "clear_cache",
    "declared_names",
    "get",
    "is_enabled",
    "register",
    "resolve_with_provenance",
]
