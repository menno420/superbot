"""Central read-source arbitration — Phase 2 PR-4.

The seam between subsystems and "legacy settings vs typed bindings".
Every config read for a migrated key flows through :func:`read_config`,
which consults the feature flag evaluator to decide whether to serve
the binding or the legacy setting, and returns a typed
:class:`ConfigReadResult` that carries the full provenance.

Why one central helper:

* Per-cog branching on ``is_enabled("bindings.primary", ...)`` would
  scatter the transition logic and make rollback a per-cog change.
  Collapsing it into one helper means the canary flip (PR-7) and the
  eventual production flip are single-line changes in one place.
* Provenance (``source``, ``binding_status``, ``flag_state``,
  ``diagnostics``) is essential for setup-wizard previews, migration
  debugging, and the ``!platform consistency`` view that PR-10 will
  unify.

Return value typing — read carefully:

* The **binding** path returns ``BindingValue.target_id``
  (``int | None``).  Binding rows store typed snowflakes for
  channel/role/etc.
* The **legacy** and **fallback** paths return the raw legacy string
  (``str``) from ``guild_settings``.  This is intentional — the
  legacy KV table stores everything as strings.
* PR-7's per-subsystem wrappers (e.g. ``get_xp_announce_channel``)
  will coerce ``str`` → ``int`` (or whatever the binding kind
  requires) so callers receive a uniform type.  Callers of
  :func:`read_config` directly MUST handle both shapes (or wait for
  the per-subsystem wrappers in PR-7).

Source semantics (used by ``!platform consistency``):

* ``source='legacy'`` — value came from legacy KV.  Flag was OFF.
* ``source='binding'`` — value came from a bound subsystem_bindings
  row.  Flag was ON and the binding was BOUND.
* ``source='fallback'`` — flag ON but binding not BOUND; legacy
  fallback supplied a non-empty value.
* ``source='missing'`` — neither side produced a value.  Returned
  whenever the resolved value is ``None``, regardless of flag state;
  ``flag_state`` and ``binding_status`` carry the distinguishing
  context.  This makes "how many of my guilds have neither legacy
  nor binding configured?" a single counter query.

Binding-kind verification (PR-4 enhancement):

* When ``binding_kind`` is provided, ``read_config`` verifies that the
  resolved binding's kind matches.  A mismatch (schema drift) is
  treated as if the binding were INVALID — the result short-circuits
  to fallback / missing and ``diagnostics`` records the drift.  This
  surfaces wrong-kind bindings early instead of silently returning
  the wrong shape of value.

Hard rules:

* **No cog branches directly on ``is_enabled("bindings.primary", ...)``.**
  Only this module is allowed to.  An AST scan will pin this once
  there are real callers (the scan is deferred until PR-7's
  read-site swaps so there is something to enforce against).
* This module does NOT mutate state.  Reads only.
* This module does NOT cache; it leans on the binding and feature-flag
  layers' caches.  Adding a third cache here would multiply
  invalidation paths for no benefit.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger("bot.config_arbitration")

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

Source = Literal["legacy", "binding", "fallback", "missing"]
BindingStatus = Literal["bound", "unresolved", "missing", "invalid", "n/a"]
FlagState = Literal["on", "off", "n/a"]


@dataclass(frozen=True)
class ConfigReadResult:
    """Typed snapshot of a single arbitrated config read.

    Fields:

    value:
        The resolved value (typically an ``int`` for channel/role IDs,
        or ``str`` for free-form settings, or ``None`` when missing).
    source:
        Where ``value`` came from in the arbitration ladder.
    binding_status:
        Binding-side status if the binding was consulted.  ``n/a`` when
        flag was OFF (binding never consulted).
    flag_state:
        Effective state of ``bindings.primary`` for this guild.
    diagnostics:
        Free-form short strings explaining notable transitions
        (e.g. ``"binding MISSING, fell back to legacy"``).  Surfaced in
        ``!platform consistency`` in PR-10.
    """

    value: Any
    source: Source
    binding_status: BindingStatus
    flag_state: FlagState
    diagnostics: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Counters — used by the diagnostics provider
# ---------------------------------------------------------------------------

# Tallied per-call so the consistency view can show "fallback rate ≠ 0
# means a canary guild has a binding that's MISSING or INVALID".  Three
# parallel dimensions:
#   * by_source: where the value actually came from
#   * by_binding_status: the binding row's last-known status
#   * by_flag_state: the feature-flag evaluator's decision for this guild
_BY_SOURCE: dict[str, int] = {"legacy": 0, "binding": 0, "fallback": 0, "missing": 0}
_BY_BINDING_STATUS: dict[str, int] = {
    "bound": 0,
    "unresolved": 0,
    "missing": 0,
    "invalid": 0,
    "n/a": 0,
}
_BY_FLAG_STATE: dict[str, int] = {"on": 0, "off": 0, "n/a": 0}
_CALLS_TOTAL = 0


def _bump_counters(result: ConfigReadResult) -> None:
    global _CALLS_TOTAL
    _CALLS_TOTAL += 1
    _BY_SOURCE[result.source] = _BY_SOURCE.get(result.source, 0) + 1
    _BY_BINDING_STATUS[result.binding_status] = (
        _BY_BINDING_STATUS.get(result.binding_status, 0) + 1
    )
    _BY_FLAG_STATE[result.flag_state] = _BY_FLAG_STATE.get(result.flag_state, 0) + 1


def _reset_counters_for_tests() -> None:
    """Test helper — zero all counters and clear attribution."""
    global _CALLS_TOTAL
    _CALLS_TOTAL = 0
    for d in (_BY_SOURCE, _BY_BINDING_STATUS, _BY_FLAG_STATE):
        for k in list(d):
            d[k] = 0
    _FALLBACK_ATTRIBUTION.clear()


def counters_snapshot() -> dict[str, Any]:
    """Snapshot of the arbitration counters; called by the diag provider."""
    return {
        "calls_total": _CALLS_TOTAL,
        "by_source": dict(_BY_SOURCE),
        "by_binding_status": dict(_BY_BINDING_STATUS),
        "by_flag_state": dict(_BY_FLAG_STATE),
    }


# ---------------------------------------------------------------------------
# Fallback attribution — names *which* key degraded to legacy (PR1)
# ---------------------------------------------------------------------------
#
# The counters above answer "how many reads fell back?"; they cannot
# answer "which subsystem / binding / legacy key fell back?".  This map
# closes that gap for ``!platform consistency`` so an operator can act on
# a non-zero fallback count instead of guessing.
#
# Privacy (hard rule — see docs/setup-platform/setup_wizard_finalization_plan.md §D6):
# we store ONLY stable internal identifiers (guild_id, subsystem,
# binding_name, legacy_key, source, flag_state, binding_status, and a
# UTC timestamp).  We never store the resolved value, channel/role/user
# names, or any free-form content.
#
# Cardinality: keyed by (guild_id, subsystem, binding_name) so a noisy
# guild re-reading the same key collapses to ONE entry (its most recent
# state) rather than flooding the map.  The map is hard-capped at
# ``_ATTRIBUTION_MAX``; when full, the oldest entry by ``recorded_at`` is
# evicted so it can never grow without bound.

_ATTRIBUTION_MAX = 256


@dataclass(frozen=True)
class FallbackRecord:
    """One redacted attribution entry for a non-clean arbitration read."""

    guild_id: int
    subsystem: str
    binding_name: str
    legacy_key: str
    source: Source
    flag_state: FlagState
    binding_status: BindingStatus
    recorded_at: str  # ISO-8601 UTC, second precision


_FALLBACK_ATTRIBUTION: dict[tuple[int, str, str], FallbackRecord] = {}


def _record_attribution(
    result: ConfigReadResult,
    guild_id: int,
    subsystem: str,
    binding_name: str,
    legacy_key: str,
) -> None:
    """Record a redacted attribution entry for degrading reads.

    Only ``source='fallback'`` (flag ON, binding not bound, legacy
    supplied) and ``source='missing'`` while the flag is ON (nothing
    configured under the new regime) are recorded — these are the
    actionable migration signals.  ``legacy`` / ``binding`` (clean) and
    ``missing`` while the flag is OFF (an ordinary unconfigured optional
    setting) are ignored to keep the map focused and small.
    """
    record_it = result.source == "fallback" or (
        result.source == "missing" and result.flag_state == "on"
    )
    if not record_it:
        return
    key = (guild_id, subsystem, binding_name)
    # Evict the oldest entry when introducing a *new* key at capacity.
    if (
        key not in _FALLBACK_ATTRIBUTION
        and len(_FALLBACK_ATTRIBUTION) >= _ATTRIBUTION_MAX
    ):
        oldest = min(
            _FALLBACK_ATTRIBUTION,
            key=lambda k: _FALLBACK_ATTRIBUTION[k].recorded_at,
        )
        _FALLBACK_ATTRIBUTION.pop(oldest, None)
    _FALLBACK_ATTRIBUTION[key] = FallbackRecord(
        guild_id=guild_id,
        subsystem=subsystem,
        binding_name=binding_name,
        legacy_key=legacy_key,
        source=result.source,
        flag_state=result.flag_state,
        binding_status=result.binding_status,
        recorded_at=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
    )


def attribution_snapshot(limit: int = 25) -> list[dict[str, Any]]:
    """Most-recent-first redacted attribution entries (capped at ``limit``)."""
    records = sorted(
        _FALLBACK_ATTRIBUTION.values(),
        key=lambda r: r.recorded_at,
        reverse=True,
    )
    return [
        {
            "guild_id": r.guild_id,
            "subsystem": r.subsystem,
            "binding_name": r.binding_name,
            "legacy_key": r.legacy_key,
            "source": r.source,
            "flag_state": r.flag_state,
            "binding_status": r.binding_status,
            "recorded_at": r.recorded_at,
        }
        for r in records[:limit]
    ]


def _finalize(
    result: ConfigReadResult,
    guild_id: int,
    subsystem: str,
    binding_name: str,
    legacy_key: str,
) -> ConfigReadResult:
    """Bump counters + record attribution, then return ``result``.

    A single tail-call for every ``read_config`` return path so the
    diagnostics side effects can never be forgotten when a new branch
    is added.
    """
    _bump_counters(result)
    _record_attribution(result, guild_id, subsystem, binding_name, legacy_key)
    return result


# ---------------------------------------------------------------------------
# read_config — the central arbiter
# ---------------------------------------------------------------------------


async def read_config(
    guild_id: int,
    subsystem: str,
    binding_name: str,
    legacy_key: str,
    *,
    binding_kind: str | None = None,
    pointer_retired: bool = False,
) -> ConfigReadResult:
    """Resolve a config value via the bindings → legacy ladder.

    Resolution:

    1. Decide whether the binding is primary for this read:
       - ``pointer_retired=True`` → binding is **always** primary,
         regardless of the global ``bindings.primary`` canary flag.  A
         retired pointer (its editable scalar ``SettingSpec`` is gone —
         P0-3 convergence) has *completed* its transition: the binding
         is its only write surface, so the read must consult the
         binding even before the global flag is flipped.  This is what
         lets the retirement deploy safely without a coordinated
         production flag flip; the global flag still governs in-transition
         keys (e.g. the governance role pointers).
       - Otherwise consult ``is_enabled("bindings.primary", guild_id)``:
         **OFF** → read legacy (``source='legacy'`` / ``'missing'``);
         **ON** → fall through to step 2.
    2. Read the binding via :func:`core.runtime.bindings.get_binding`.
       - If ``status == BOUND`` and a target is present AND (when
         ``binding_kind`` was supplied) the binding's declared kind
         matches → return ``target_id`` with ``source='binding'``.
       - If kinds mismatch → treat as INVALID; record a diagnostic
         and fall through to fallback.
       - Else → fall through to step 3.
    3. Read legacy as a fallback.  ``source='fallback'`` if legacy
       supplies a value, ``source='missing'`` if not.  For a retired
       pointer this fallback is the rollback path: a guild whose value
       was never migrated to a binding still reads its legacy KV.

    Failure handling:

    * If ``is_enabled`` raises, treat as flag OFF.  Logged.
    * If the binding read raises, log and fall through to legacy.
    * Legacy read failures propagate (the legacy DB layer is allowed
      to surface its own errors — arbitration only catches binding /
      flag failures because those are the new code).
    """
    # Local imports to keep this file out of any module-load cycles.
    from core.runtime import bindings as bindings_runtime
    from core.runtime import feature_flags
    from utils.db import settings as settings_db

    diagnostics: list[str] = []

    # Step 1: decide whether the binding is primary.  A retired pointer
    # forces binding-primary (the flag governs only in-transition keys);
    # everything else consults the global canary flag.
    if pointer_retired:
        primary_on = True
        diagnostics.append("binding primary forced (retired pointer)")
    else:
        try:
            primary_on = await feature_flags.is_enabled(
                "bindings.primary",
                guild_id,
            )
        except Exception as exc:  # noqa: BLE001 — arbitration must not raise
            logger.warning(
                "config_arbitration: is_enabled raised for guild=%d (%r); "
                "treating bindings.primary as OFF",
                guild_id,
                exc,
            )
            primary_on = False
            diagnostics.append(f"is_enabled raised: {type(exc).__name__}")

    if not primary_on:
        legacy_value = await _read_legacy(settings_db, guild_id, legacy_key)
        # source='missing' when the resolved value is None, regardless of
        # which side we consulted — this makes the !platform consistency
        # "how many guilds have nothing configured?" query a single
        # counter read.
        source: Source = "missing" if legacy_value is None else "legacy"
        result = ConfigReadResult(
            value=legacy_value,
            source=source,
            binding_status="n/a",
            flag_state="off",
            diagnostics=diagnostics,
        )
        return _finalize(result, guild_id, subsystem, binding_name, legacy_key)

    # Step 2: binding read.
    binding_status: BindingStatus = "n/a"
    try:
        bv = await bindings_runtime.get_binding(guild_id, subsystem, binding_name)
        binding_status = bv.status.value  # type: ignore[assignment]
        # Verify kind matches if the caller declared an expected kind.
        # Schema drift here is rare but high-impact (a "channel" caller
        # would otherwise get a role snowflake) so we surface it
        # explicitly rather than silently returning the wrong shape.
        kind_mismatch = False
        if binding_kind is not None and bv.kind.value != binding_kind:
            kind_mismatch = True
            diagnostics.append(
                f"binding kind drift: expected={binding_kind} actual={bv.kind.value}",
            )
            logger.warning(
                "config_arbitration: binding kind drift for "
                "guild=%d subsystem=%r binding=%r — expected=%s actual=%s",
                guild_id,
                subsystem,
                binding_name,
                binding_kind,
                bv.kind.value,
            )
        if bv.is_bound and bv.target_id is not None and not kind_mismatch:
            result = ConfigReadResult(
                value=bv.target_id,
                source="binding",
                binding_status=binding_status,
                flag_state="on",
                diagnostics=diagnostics,
            )
            return _finalize(result, guild_id, subsystem, binding_name, legacy_key)
        if not kind_mismatch:
            diagnostics.append(f"binding not bound (status={binding_status})")
    except Exception as exc:  # noqa: BLE001 — arbitration must not raise
        logger.warning(
            "config_arbitration: get_binding raised for "
            "guild=%d subsystem=%r binding=%r (%r); falling back to legacy",
            guild_id,
            subsystem,
            binding_name,
            exc,
        )
        diagnostics.append(f"get_binding raised: {type(exc).__name__}")

    # Step 3: fallback to legacy.
    legacy_value = await _read_legacy(settings_db, guild_id, legacy_key)
    if legacy_value is None:
        result = ConfigReadResult(
            value=None,
            source="missing",
            binding_status=binding_status,
            flag_state="on",
            diagnostics=diagnostics,
        )
    else:
        result = ConfigReadResult(
            value=legacy_value,
            source="fallback",
            binding_status=binding_status,
            flag_state="on",
            diagnostics=diagnostics,
        )
    return _finalize(result, guild_id, subsystem, binding_name, legacy_key)


async def _read_legacy(settings_db, guild_id: int, legacy_key: str) -> Any | None:
    """Best-effort legacy read; returns ``None`` for missing/empty.

    The legacy KV table stores everything as strings; this function
    returns the raw string (or ``None`` for an empty/missing row).
    PR-7's per-subsystem wrappers will coerce ``str`` → typed values
    so callers do not have to know the storage format.
    """
    raw = await settings_db.get_setting(guild_id, legacy_key, default="")
    if not raw:
        return None
    return raw


# ---------------------------------------------------------------------------
# Type-coercion helpers for per-subsystem accessors
# ---------------------------------------------------------------------------
#
# ``read_config`` returns ``int|None`` from the binding path and
# ``str|None`` from the legacy path.  The per-subsystem accessors
# below normalize to a single shape (matching what existing callers
# expect) so cog read-sites don't have to branch on
# ``isinstance(result.value, int)``.


def _coerce_to_int(result: ConfigReadResult) -> ConfigReadResult:
    """Return a new ``ConfigReadResult`` with ``value`` normalized to ``int|None``.

    A legacy string that doesn't parse as an int is converted to
    ``None`` and recorded in ``diagnostics`` — the caller treats it
    as "missing" rather than crashing on the type mismatch.
    """
    value = result.value
    if value is None:
        return result
    if isinstance(value, int):
        return result
    if isinstance(value, str):
        try:
            return ConfigReadResult(
                value=int(value),
                source=result.source,
                binding_status=result.binding_status,
                flag_state=result.flag_state,
                diagnostics=result.diagnostics,
            )
        except ValueError:
            return ConfigReadResult(
                value=None,
                source="missing",
                binding_status=result.binding_status,
                flag_state=result.flag_state,
                diagnostics=[
                    *result.diagnostics,
                    f"legacy value {value!r} could not be parsed as int",
                ],
            )
    # Unknown type — coerce to None.
    return ConfigReadResult(
        value=None,
        source="missing",
        binding_status=result.binding_status,
        flag_state=result.flag_state,
        diagnostics=[
            *result.diagnostics,
            f"unexpected value type {type(value).__name__}",
        ],
    )


def _coerce_to_str(result: ConfigReadResult) -> ConfigReadResult:
    """Return a new ``ConfigReadResult`` with ``value`` normalized to ``str|None``.

    A legacy empty string is already filtered to ``None`` by
    :func:`_read_legacy`, so this helper only needs to stringify
    ints from the binding path.
    """
    value = result.value
    if value is None or isinstance(value, str):
        return result
    return ConfigReadResult(
        value=str(value),
        source=result.source,
        binding_status=result.binding_status,
        flag_state=result.flag_state,
        diagnostics=result.diagnostics,
    )


# ---------------------------------------------------------------------------
# Per-subsystem convenience accessors (PR-7).
#
# These are the ONLY legitimate read sites for migrated keys in cog/
# service/governance code.  Direct calls to
# ``is_enabled("bindings.primary", ...)`` outside this module are
# forbidden by ``tests/unit/invariants/test_no_direct_bindings_primary_branch.py``.


async def get_xp_announce_channel(guild_id: int) -> ConfigReadResult:
    """Resolve the XP announce channel via the arbitration ladder.

    Return shape: ``ConfigReadResult.value`` is ``str|None`` (matches
    the existing ``XpConfig.announce_channel`` shape).  A binding-side
    snowflake int is stringified; an unparseable legacy value is
    returned as the raw string.

    **Retired pointer (P0-3 arc PR 2):** the editable ``xp_announce_channel``
    scalar ``SettingSpec`` was retired; the ``xp.announce_channel`` binding
    is the only write surface, so this read is binding-first regardless of
    the global ``bindings.primary`` flag (legacy KV remains the rollback
    fallback).
    """
    result = await read_config(
        guild_id=guild_id,
        subsystem="xp",
        binding_name="announce_channel",
        legacy_key="xp_announce_channel",
        binding_kind="channel",
        pointer_retired=True,
    )
    return _coerce_to_str(result)


async def get_economy_log_channel(guild_id: int) -> ConfigReadResult:
    """Resolve the economy log channel; value normalized to ``int|None``.

    Consumers (``utils.helpers.post_log_embed``) then do
    ``guild.get_channel(value)``.  An unparseable legacy value becomes
    ``None`` with a diagnostic explaining the parse failure.

    **Retired pointer (P0-3 arc PR 2):** the editable ``economy_log_channel``
    scalar ``SettingSpec`` was retired; the ``economy.log_channel`` binding
    is the only write surface, so this read is binding-first regardless of
    the global ``bindings.primary`` flag (legacy KV remains the rollback
    fallback).
    """
    result = await read_config(
        guild_id=guild_id,
        subsystem="economy",
        binding_name="log_channel",
        legacy_key="economy_log_channel",
        binding_kind="channel",
        pointer_retired=True,
    )
    return _coerce_to_int(result)


async def get_trusted_tier_role(guild_id: int) -> ConfigReadResult:
    """Resolve the governance trusted-tier role; value normalized to ``int|None``.

    Consumers (``governance.resolver._resolve_member_tier``) check
    membership of this role id against ``ctx.role_ids``.
    """
    result = await read_config(
        guild_id=guild_id,
        subsystem="governance",
        binding_name="trusted_role",
        legacy_key="trusted_tier_role_id",
        binding_kind="role",
    )
    return _coerce_to_int(result)


async def get_moderator_tier_role(guild_id: int) -> ConfigReadResult:
    """Resolve the governance moderator-tier role; value normalized to ``int|None``.

    Symmetric to :func:`get_trusted_tier_role`.  Consumers
    (``governance.resolver._resolve_member_tier``) check membership of this
    role id against ``ctx.role_ids`` and, when matched, grant the member the
    ``moderator`` tier so they may use moderation actions without holding the
    corresponding Discord permissions (capability-native authority, ADR-008).
    """
    result = await read_config(
        guild_id=guild_id,
        subsystem="governance",
        binding_name="moderator_role",
        legacy_key="moderator_tier_role_id",
        binding_kind="role",
    )
    return _coerce_to_int(result)


# ---------------------------------------------------------------------------
# Diagnostics provider registration (registers at import time)
# ---------------------------------------------------------------------------


def _consistency_snapshot() -> dict[str, Any]:
    """Snapshot for ``!platform consistency``.

    ``arbitration`` carries the aggregate counters; ``attribution``
    carries the bounded, redacted per-key fallback list so the
    consistency view can name *which* key degraded to legacy.
    """
    return {
        "arbitration": counters_snapshot(),
        "attribution": attribution_snapshot(),
    }


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("config_arbitration", _consistency_snapshot)


_register_diagnostics()


__all__ = [
    "ConfigReadResult",
    "FallbackRecord",
    "attribution_snapshot",
    "counters_snapshot",
    "get_economy_log_channel",
    "get_moderator_tier_role",
    "get_trusted_tier_role",
    "get_xp_announce_channel",
    "read_config",
]
