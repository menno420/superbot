"""AI configuration projection — operator-facing read model.

Single read-orchestration layer that every operator-facing AI surface
(``!ai status``, ``!ai policy``, ``!ai memory``, ``!ai support-report``,
the AI panel, the behavior preview, ...) reads from. Composes existing
services / repositories into one :class:`AIConfigSnapshot`. Does NOT
duplicate SQL, resolver rules, memory semantics, diagnostics logic, or
audit formatting — every field maps to a known existing source.

**Non-mutating invariant.** This module is read orchestration only. It
must not mutate settings, project legacy scalars, append memory, write
audit rows, invalidate resolver cache, bump policy generations, or call
AI providers. The pin-test
``tests/unit/services/test_ai_readonly_invariants.py`` enforces this by
AST scan; future contributors must keep it green.

Snapshot shape (see :class:`AIConfigSnapshot`):

* ``policy``       — ``ai_guild_policy`` row + override counts.
* ``memory``       — memory window + scan + in-process cache stats.
* ``provider``     — gateway diagnostics (no provider call).
* ``projection``   — legacy-scalar vs typed-policy drift.
* ``instruction``  — active guild instruction profile id + name.
* ``audit``        — latest decision row + per-decision counts.
* ``readiness_summary`` — optional one-line health string. The full
  report lives in :mod:`services.ai_readiness_service`.

Every field tolerates unknown / missing data using ``None`` or ``"—"``
so renderers never raise on a partially-populated snapshot.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from services import (
    ai_conversation_service,
    ai_decision_audit_service,
    ai_diagnostics_service,
    ai_memory_service,
    ai_policy_mutation,
)
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_config_projection")


_MEMORY_RAW_SCALAR_KEYS: tuple[str, ...] = (
    "ai_memory_window_minutes",
    "ai_memory_channel_scan_enabled",
    "ai_guild_instruction_profile",
)


# ---------------------------------------------------------------------------
# Sub-snapshot dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicySnapshot:
    """The ``ai_guild_policy`` row plus override counts.

    ``guild_id`` is always populated. Every other field is ``None`` when
    the typed row has not been written yet (the guild has never enabled
    AI through the settings UI). Override counts default to ``0``.
    """

    guild_id: int
    enabled: bool | None = None
    natural_language_enabled: bool | None = None
    default_provider: str | None = None
    default_model: str | None = None
    minimum_level_default: int | None = None
    cooldown_seconds: int | None = None
    fresh_user_mention_allowance: int | None = None
    guild_instruction_profile_id: int | None = None
    generation: int | None = None
    channel_override_count: int = 0
    category_override_count: int = 0
    role_override_count: int = 0


@dataclass(frozen=True)
class MemorySnapshot:
    """Memory window/scan settings + in-process cache stats.

    ``window_minutes`` is the validated value from
    :func:`ai_memory_service.read_memory_settings` (clamped to the
    allowed set). ``min_floor_turns`` mirrors
    :data:`ai_conversation_service.MIN_FLOOR_TURNS` so renderers can
    explain the "Minimal" mode.

    ``cached_channel_count`` and ``cached_total_turns`` are
    **process-wide** — the conversation buffer is shared across all
    guilds in the LRU cap. ``guild_channel_count`` and
    ``guild_total_turns`` count only this guild's buffers.
    """

    window_minutes: int
    scan_enabled: bool
    cached_channel_count: int
    cached_total_turns: int
    per_channel_cap: int
    channel_lru_cap: int
    min_floor_turns: int
    guild_channel_count: int = 0
    guild_total_turns: int = 0


@dataclass(frozen=True)
class ProviderSnapshot:
    """Gateway diagnostics — provider/model + counters. No provider call."""

    enabled: bool
    default_provider: str | None
    setup_advisor_provider: str | None
    provider_active: str | None
    degraded: bool
    last_error_type: str | None
    last_fallback_reason: str | None
    requests_observed: int
    failures_observed: int
    redaction_enabled: bool


@dataclass(frozen=True)
class ProjectionFieldStatus:
    """One legacy-scalar / typed-policy pair.

    ``drift`` is True when the legacy KV value disagrees with the typed
    column after coercion. ``None`` typed value means the typed row has
    not been written yet — that is NOT drift on its own; ``drift`` is
    only True when both sides are populated AND disagree.
    """

    legacy_key: str
    policy_field: str
    legacy_value: Any
    typed_value: Any
    drift: bool
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectionSnapshot:
    """Drift status for every projected legacy scalar + raw-scalar list.

    ``fields`` covers every entry in
    :func:`ai_policy_mutation.projectable_keys`. ``raw_scalars`` is the
    explicit "not projected" list with the legacy values for visibility;
    these settings live as raw scalars by design (memory settings) or
    are managed elsewhere (instruction profile body).
    """

    fields: tuple[ProjectionFieldStatus, ...] = ()
    raw_scalars: dict[str, Any] = field(default_factory=dict)
    drift_count: int = 0

    @property
    def drift(self) -> bool:
        """True when at least one projected field shows drift."""
        return self.drift_count > 0


@dataclass(frozen=True)
class InstructionSnapshot:
    """Active guild instruction profile, if one is bound."""

    profile_id: int | None = None
    profile_name: str | None = None
    profile_scope: str | None = None
    profile_is_preset: bool | None = None


@dataclass(frozen=True)
class AuditSnapshot:
    """Latest decision row + per-decision counts over the recent window."""

    latest: dict[str, Any] | None = None
    recent_total: int = 0
    by_decision: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class AIConfigSnapshot:
    """The operator-facing read model.

    Composed from existing services. Every field is safe to read on a
    partially-configured guild (defaults to ``None``, ``0``, or ``"—"``
    so renderers never raise).
    """

    guild_id: int
    policy: PolicySnapshot
    memory: MemorySnapshot
    provider: ProviderSnapshot
    projection: ProjectionSnapshot
    instruction: InstructionSnapshot
    audit: AuditSnapshot
    readiness_summary: str | None = None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def build_snapshot(
    guild_id: int,
    *,
    bot: Any = None,
    audit_window: int = 50,
    readiness_summary: str | None = None,
) -> AIConfigSnapshot:
    """Build the operator-facing snapshot for ``guild_id``.

    Pure orchestration: every sub-field is sourced from an existing
    service/repository (see module docstring). ``bot`` is accepted for
    future extensions but currently unused — the readiness check that
    needs a bot reference lives in :mod:`services.ai_readiness_service`.

    ``audit_window`` caps how many recent audit rows feed
    :class:`AuditSnapshot.by_decision`; defaults to 50, matching the
    existing ``ai_decision_audit_service.query`` default.

    ``readiness_summary`` is opaque to this service — callers that
    already computed a readiness report can pass its summary line
    through so a single render call has everything it needs without
    re-scanning. Defaults to ``None``; the snapshot stays valid.
    """
    policy_snapshot = await _build_policy_snapshot(guild_id)
    memory_snapshot = await _build_memory_snapshot(guild_id)
    provider_snapshot = _build_provider_snapshot()
    projection_snapshot = await _build_projection_snapshot(guild_id, policy_snapshot)
    instruction_snapshot = await _build_instruction_snapshot(policy_snapshot)
    audit_snapshot = await _build_audit_snapshot(guild_id, audit_window)
    return AIConfigSnapshot(
        guild_id=guild_id,
        policy=policy_snapshot,
        memory=memory_snapshot,
        provider=provider_snapshot,
        projection=projection_snapshot,
        instruction=instruction_snapshot,
        audit=audit_snapshot,
        readiness_summary=readiness_summary,
    )


# ---------------------------------------------------------------------------
# Sub-builders
# ---------------------------------------------------------------------------


async def _build_policy_snapshot(guild_id: int) -> PolicySnapshot:
    """Read ``ai_guild_policy`` + override counts. Safe on missing row."""
    try:
        policy = await ai_db.get_guild_policy(guild_id)
    except Exception:
        logger.exception(
            "ai_config_projection: get_guild_policy failed for guild=%d",
            guild_id,
        )
        return PolicySnapshot(guild_id=guild_id)

    channel_count = 0
    category_count = 0
    role_count = 0
    try:
        channel_count = len(await ai_db.list_channel_policies(guild_id))
        category_count = len(await ai_db.list_category_policies(guild_id))
        role_count = len(await ai_db.list_role_policies(guild_id))
    except Exception:
        logger.exception(
            "ai_config_projection: override-count read failed for guild=%d",
            guild_id,
        )

    if not policy:
        return PolicySnapshot(
            guild_id=guild_id,
            channel_override_count=channel_count,
            category_override_count=category_count,
            role_override_count=role_count,
        )

    return PolicySnapshot(
        guild_id=guild_id,
        enabled=bool(policy.get("enabled")),
        natural_language_enabled=bool(policy.get("natural_language_enabled")),
        default_provider=policy.get("default_provider"),
        default_model=policy.get("default_model") or None,
        minimum_level_default=policy.get("minimum_level_default"),
        cooldown_seconds=policy.get("cooldown_seconds"),
        fresh_user_mention_allowance=policy.get("fresh_user_mention_allowance"),
        guild_instruction_profile_id=policy.get("guild_instruction_profile_id"),
        generation=policy.get("generation"),
        channel_override_count=channel_count,
        category_override_count=category_count,
        role_override_count=role_count,
    )


async def _build_memory_snapshot(guild_id: int) -> MemorySnapshot:
    """Read memory settings + cache stats. Safe on settings DB failure."""
    try:
        window, scan_enabled = await ai_memory_service.read_memory_settings(guild_id)
    except Exception:
        logger.exception(
            "ai_config_projection: read_memory_settings failed for guild=%d",
            guild_id,
        )
        window, scan_enabled = 0, False
    stats = ai_conversation_service.stats()
    try:
        per_guild = ai_conversation_service.channel_stats(guild_id)
    except Exception:
        logger.exception(
            "ai_config_projection: channel_stats failed for guild=%d",
            guild_id,
        )
        per_guild = {}
    return MemorySnapshot(
        window_minutes=int(window),
        scan_enabled=bool(scan_enabled),
        cached_channel_count=int(stats.channel_count),
        cached_total_turns=int(stats.total_turns),
        per_channel_cap=int(stats.per_channel_cap),
        channel_lru_cap=int(stats.channel_lru_cap),
        min_floor_turns=int(ai_conversation_service.MIN_FLOOR_TURNS),
        guild_channel_count=len(per_guild),
        guild_total_turns=sum(per_guild.values()),
    )


def _build_provider_snapshot() -> ProviderSnapshot:
    """Synthesise from the diagnostics snapshot. No provider call."""
    snap = ai_diagnostics_service.snapshot_for_cog()
    return ProviderSnapshot(
        enabled=bool(snap.get("enabled")),
        default_provider=_str_or_none(snap.get("default_provider")),
        setup_advisor_provider=_str_or_none(snap.get("setup_advisor_provider")),
        provider_active=_str_or_none(snap.get("provider_active")),
        degraded=bool(snap.get("degraded")),
        last_error_type=_str_or_none(snap.get("last_error_type")),
        last_fallback_reason=_str_or_none(snap.get("last_fallback_reason")),
        requests_observed=int(snap.get("requests_observed") or 0),
        failures_observed=int(snap.get("failures_observed") or 0),
        redaction_enabled=bool(snap.get("redaction_enabled")),
    )


async def _build_projection_snapshot(
    guild_id: int,
    policy: PolicySnapshot,
) -> ProjectionSnapshot:
    """Compute drift for every projected legacy scalar.

    Each entry compares the freshly-resolved legacy KV value with the
    typed-policy column value. Drift only when both sides are populated
    AND disagree after coercion. A missing typed row is reported with
    ``typed_value=None, drift=False`` (no projection has happened yet
    rather than an inconsistency between sides).
    """
    from services import settings_resolution

    fields: list[ProjectionFieldStatus] = []
    drift_count = 0
    try:
        projectable = ai_policy_mutation.projectable_keys()
    except Exception:
        logger.exception("ai_config_projection: projectable_keys() failed")
        projectable = frozenset()

    legacy_to_field = {
        "ai_enabled": ("enabled", policy.enabled),
        "ai_natural_language_enabled": (
            "natural_language_enabled",
            policy.natural_language_enabled,
        ),
        "ai_default_provider": ("default_provider", policy.default_provider),
        "ai_default_model": ("default_model", policy.default_model),
        "ai_minimum_level_default": (
            "minimum_level_default",
            policy.minimum_level_default,
        ),
        "ai_cooldown_seconds": ("cooldown_seconds", policy.cooldown_seconds),
        "ai_fresh_user_mention_allowance": (
            "fresh_user_mention_allowance",
            policy.fresh_user_mention_allowance,
        ),
    }

    for legacy_key in sorted(projectable):
        policy_field, typed_value = legacy_to_field.get(
            legacy_key,
            (legacy_key, None),
        )
        try:
            resolution = await settings_resolution.resolve_setting(
                guild_id,
                "ai",
                legacy_key,
            )
        except Exception as exc:
            fields.append(
                ProjectionFieldStatus(
                    legacy_key=legacy_key,
                    policy_field=policy_field,
                    legacy_value=None,
                    typed_value=typed_value,
                    drift=False,
                    diagnostics=(f"resolve_setting failed: {type(exc).__name__}",),
                ),
            )
            continue
        legacy_value = resolution.value if resolution is not None else None
        diagnostics: tuple[str, ...] = ()
        if resolution is not None and not resolution.valid:
            diagnostics = resolution.diagnostics
        drift = (
            typed_value is not None
            and legacy_value is not None
            and _normalize_for_compare(legacy_value)
            != _normalize_for_compare(typed_value)
        )
        if drift:
            drift_count += 1
        fields.append(
            ProjectionFieldStatus(
                legacy_key=legacy_key,
                policy_field=policy_field,
                legacy_value=legacy_value,
                typed_value=typed_value,
                drift=drift,
                diagnostics=diagnostics,
            ),
        )

    raw_scalars: dict[str, Any] = {}
    for legacy_key in _MEMORY_RAW_SCALAR_KEYS:
        try:
            resolution = await settings_resolution.resolve_setting(
                guild_id,
                "ai",
                legacy_key,
            )
        except Exception:
            raw_scalars[legacy_key] = None
            continue
        raw_scalars[legacy_key] = resolution.value if resolution is not None else None

    return ProjectionSnapshot(
        fields=tuple(fields),
        raw_scalars=raw_scalars,
        drift_count=drift_count,
    )


async def _build_instruction_snapshot(
    policy: PolicySnapshot,
) -> InstructionSnapshot:
    """Resolve the bound instruction profile to id + name + scope."""
    profile_id = policy.guild_instruction_profile_id
    if not profile_id:
        return InstructionSnapshot()
    try:
        row = await ai_db.get_instruction_profile(int(profile_id))
    except Exception:
        logger.exception(
            "ai_config_projection: get_instruction_profile failed for id=%s",
            profile_id,
        )
        return InstructionSnapshot(profile_id=int(profile_id))
    if not row:
        return InstructionSnapshot(profile_id=int(profile_id))
    return InstructionSnapshot(
        profile_id=int(profile_id),
        profile_name=row.get("name"),
        profile_scope=row.get("scope"),
        profile_is_preset=bool(row.get("is_preset")),
    )


async def _build_audit_snapshot(guild_id: int, window: int) -> AuditSnapshot:
    """Read the latest ``window`` audit rows; tally per-decision counts."""
    try:
        rows = await ai_decision_audit_service.query(
            guild_id,
            limit=max(1, int(window)),
        )
    except Exception:
        logger.exception(
            "ai_config_projection: audit query failed for guild=%d",
            guild_id,
        )
        return AuditSnapshot()

    if not rows:
        return AuditSnapshot()

    by_decision: dict[str, int] = {}
    for row in rows:
        decision = str(row.get("decision") or "unknown")
        by_decision[decision] = by_decision.get(decision, 0) + 1

    return AuditSnapshot(
        latest=rows[0],
        recent_total=len(rows),
        by_decision=by_decision,
    )


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _str_or_none(value: Any) -> str | None:
    """Return ``None`` for empty / None-ish; otherwise ``str(value)``."""
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _normalize_for_compare(value: Any) -> Any:
    """Best-effort normalisation for the drift comparison.

    Discord-side legacy KV values are strings; typed-policy values are
    typed (bool, int, str). The compare needs to tolerate that without
    becoming a coercion service. Booleans collapse to lowercased
    "true"/"false"; ints/floats compare numerically when both sides
    coerce; otherwise both sides are stringified.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return str(value).strip().lower()


__all__ = [
    "AIConfigSnapshot",
    "AuditSnapshot",
    "InstructionSnapshot",
    "MemorySnapshot",
    "PolicySnapshot",
    "ProjectionFieldStatus",
    "ProjectionSnapshot",
    "ProviderSnapshot",
    "build_snapshot",
]
