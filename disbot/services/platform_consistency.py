"""Unified platform consistency & readiness diagnostics — Phase 2 PR-10.

Pure-read collection service.  Reuses existing diagnostics providers
and DB accessors; never mutates.  Each section collector catches its
own exceptions and converts unknown failures into a FATAL section
result so one broken collector cannot blank the report.

Cross-module imports go **function-local** inside each collector to
avoid re-entering partially-loaded ``core.runtime`` modules.  The
companion regression test
``tests/unit/runtime/test_consistency_import_cycle.py`` pins this
discipline at module scope.

Severity contract (binding):

* ``CLEAN``    — section is healthy.
* ``WARNING``  — drift, failed optional provider, missing/broken
  *configured* resource, or recoverable degradation.  Also used for
  the Setup readiness roadmap section, which is marked
  ``informational=True`` so the embed can label it as roadmap-only.
* ``FATAL``    — core unreadable / required surface broken.  Reserved
  for things that block safe rollout (core DB table query raises,
  identity contract emits a ``fatal``-tier finding).
* ``SKIPPED``  — not applicable / no context / no data
  (``guild is None``, optional table absent because its migration has
  not been applied yet, provider not registered).

Overall-status promotion:

* any ``FATAL``                       → ``FATAL``
* else any ``WARNING``                → ``WARNING``
* else if every runtime section is ``SKIPPED`` → ``SKIPPED``
* else                                → ``CLEAN``

Informational sections never promote ``overall_status``.

Public surface:

    SectionStatus               — enum
    SectionResult               — frozen dataclass per section
    ConsistencyReport           — frozen dataclass: sections + overall_status
    SETUP_READINESS_BLOCKERS    — tuple of roadmap blocker identifiers
    collect_report(*, bot, guild) — async orchestrator
"""

from __future__ import annotations

import datetime
import logging
import os
import re
from collections.abc import Awaitable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("bot.platform_consistency")


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class SectionStatus(str, Enum):
    CLEAN = "clean"
    WARNING = "warning"
    FATAL = "fatal"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class SectionResult:
    name: str
    status: SectionStatus
    summary: str
    details: tuple[str, ...] = ()
    suggested_actions: tuple[str, ...] = ()
    informational: bool = False


@dataclass(frozen=True)
class ConsistencyReport:
    sections: tuple[SectionResult, ...]
    generated_at: datetime.datetime

    @property
    def overall_status(self) -> SectionStatus:
        runtime = tuple(s for s in self.sections if not s.informational)
        if not runtime:
            return SectionStatus.SKIPPED
        statuses = {s.status for s in runtime}
        if SectionStatus.FATAL in statuses:
            return SectionStatus.FATAL
        if SectionStatus.WARNING in statuses:
            return SectionStatus.WARNING
        if statuses == {SectionStatus.SKIPPED}:
            return SectionStatus.SKIPPED
        return SectionStatus.CLEAN


SETUP_READINESS_BLOCKERS: tuple[str, ...] = (
    "command_surface_ledger",
    "panel_registry",
    "settings_registry",
    "settings_mutation_pipeline",
    "governance_trusted_role_schema",
    "role_service_extraction",
    "cleanup_policy_extraction",
    "logging_settings_integration",
    "slash_panel_entrypoints",
    "setup_wizard_readiness_bridge",
    "setup_wizard",
)


# ---------------------------------------------------------------------------
# Filesystem migration discovery
# ---------------------------------------------------------------------------

# Two dirname() calls from disbot/services/platform_consistency.py →
# disbot/, then join "migrations" → disbot/migrations.  Same root the
# migration runner uses (utils/db/migrations.py:25).
_MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "migrations",
)
_MIGRATION_FILE_RE = re.compile(r"^(\d{3,})_.+\.sql$")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def collect_report(
    *,
    bot: object | None = None,
    guild: object | None = None,
) -> ConsistencyReport:
    """Collect every section and return a single immutable report.

    The orchestrator runs each collector under ``try/except``; an
    unexpected raise becomes a ``FATAL`` ``SectionResult`` so one
    broken collector never blanks the report.

    Keyword-only ``bot`` / ``guild`` make the API explicit at the
    callsite (the DiagnosticCog passes ``ctx.guild``; tests can pass
    ``None`` to exercise the SKIPPED paths).
    """
    collectors: tuple[tuple[str, Awaitable[SectionResult]], ...] = (
        ("Identity contract", _collect_identity_contract(bot)),
        ("Feature flags", _collect_feature_flags()),
        ("Rollout / audit", _collect_rollout_audit()),
        ("Bindings", _collect_bindings(guild)),
        ("Binding backfill", _collect_binding_backfill()),
        ("Config arbitration", _collect_config_arbitration()),
        ("Participation", _collect_participation()),
        ("Migrations", _collect_migrations()),
        ("Runtime providers", _collect_runtime_providers()),
        ("Setup readiness", _collect_setup_readiness()),
    )
    sections: list[SectionResult] = []
    for label, coro in collectors:
        try:
            result = await coro
        except Exception as exc:  # noqa: BLE001 — fail-safe orchestrator
            logger.warning(
                "platform_consistency: collector %r raised %s",
                label,
                exc,
                exc_info=True,
            )
            result = SectionResult(
                name=label,
                status=SectionStatus.FATAL,
                summary=f"collector raised {type(exc).__name__}",
                details=(str(exc)[:200],),
            )
        sections.append(result)
    return ConsistencyReport(
        sections=tuple(sections),
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )


# ---------------------------------------------------------------------------
# Section collectors
# ---------------------------------------------------------------------------


async def _collect_identity_contract(bot: object | None) -> SectionResult:
    """Section 1: SUBSYSTEMS vs commands vs persistent views vs prefixes."""
    name = "Identity contract"
    if bot is None:
        return SectionResult(
            name=name,
            status=SectionStatus.SKIPPED,
            summary="No bot context — invoked without a live bot.",
        )
    try:
        # Function-local: utils.subsystem_registry transitively touches
        # core.runtime, so importing at module scope would violate the
        # cycle-sensitive contract pinned by
        # tests/unit/runtime/test_consistency_import_cycle.py.
        from utils.subsystem_registry import (
            IDENTITY_FINDING_TIER,
            validate_identity_contract,
        )

        findings = await validate_identity_contract(bot)
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.FATAL,
            summary=f"validator raised {type(exc).__name__}",
            details=(str(exc)[:200],),
            suggested_actions=(
                "Inspect bot logs for the identity-contract validator stack trace.",
            ),
        )

    total = sum(len(items) for items in findings.values())
    if total == 0:
        return SectionResult(
            name=name,
            status=SectionStatus.CLEAN,
            summary="No identity-contract findings.",
        )

    fatal_kinds: list[str] = []
    warn_kinds: list[str] = []
    for kind, items in findings.items():
        if not items:
            continue
        tier = IDENTITY_FINDING_TIER.get(kind, "fatal")
        if tier == "fatal":
            fatal_kinds.append(f"{kind}={len(items)}")
        else:
            warn_kinds.append(f"{kind}={len(items)}")

    if fatal_kinds:
        return SectionResult(
            name=name,
            status=SectionStatus.FATAL,
            summary=f"{len(fatal_kinds)} fatal-tier finding kind(s).",
            details=tuple(fatal_kinds + warn_kinds)[:8],
            suggested_actions=("Run `!platform identity` to see per-kind detail.",),
        )
    return SectionResult(
        name=name,
        status=SectionStatus.WARNING,
        summary=f"{total} non-fatal identity finding(s).",
        details=tuple(warn_kinds)[:8],
        suggested_actions=("Run `!platform identity --fix` to auto-heal.",),
    )


async def _collect_feature_flags() -> SectionResult:
    """Section 2: declared flags resolvable; evaluator healthy."""
    name = "Feature flags"
    try:
        from core.runtime import feature_flags

        flags = feature_flags.all_flags()
        if not flags:
            return SectionResult(
                name=name,
                status=SectionStatus.SKIPPED,
                summary="No flags declared (pre-bootstrap).",
            )
        # Resolve each declared flag at the global scope (guild_id=None).
        # A raise here signals deep evaluator breakage and is FATAL.
        for flag_name in sorted(flags):
            await feature_flags.resolve_with_provenance(flag_name, None)
        fallback = feature_flags.bootstrap_fallback_count()
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.FATAL,
            summary=f"evaluator raised {type(exc).__name__}",
            details=(str(exc)[:200],),
        )

    if fallback > 0:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=(
                f"{len(flags)} flag(s) declared; bootstrap fallback "
                f"count = {fallback} (DB unreachable at some point)."
            ),
            details=(
                "All flag reads since the last fallback fall back to the "
                "declared default until the next successful DB resolve.",
            ),
            suggested_actions=(
                "Verify DATABASE_URL reachability and re-run `!platform flags`.",
            ),
        )
    return SectionResult(
        name=name,
        status=SectionStatus.CLEAN,
        summary=f"{len(flags)} flag(s) declared; evaluator healthy.",
    )


async def _collect_rollout_audit() -> SectionResult:
    """Section 3: feature_flag_audit table reachable if migration exists."""
    name = "Rollout / audit"
    try:
        from utils.db import pool

        oid = await pool.get().fetchval(
            "SELECT to_regclass('feature_flag_audit')",
        )
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=f"audit-table probe raised {type(exc).__name__}",
            details=(str(exc)[:200],),
        )

    if oid is None:
        return SectionResult(
            name=name,
            status=SectionStatus.SKIPPED,
            summary="`feature_flag_audit` absent (migration 025 not applied).",
        )

    try:
        from utils.db import pool

        count = await pool.get().fetchval(
            "SELECT COUNT(*) FROM feature_flag_audit",
        )
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=(f"audit table present but COUNT(*) raised {type(exc).__name__}"),
            details=(str(exc)[:200],),
        )

    return SectionResult(
        name=name,
        status=SectionStatus.CLEAN,
        summary=f"audit table reachable; {int(count or 0)} row(s).",
    )


async def _collect_bindings(guild: object | None) -> SectionResult:
    """Section 4: subsystem_bindings reachable; broken-configured rows."""
    name = "Bindings"
    if guild is None:
        return SectionResult(
            name=name,
            status=SectionStatus.SKIPPED,
            summary="No guild context (DM invocation).",
        )
    guild_id = getattr(guild, "id", None)
    if guild_id is None:
        return SectionResult(
            name=name,
            status=SectionStatus.SKIPPED,
            summary="Guild context missing .id attribute.",
        )

    try:
        from utils.db import bindings as bindings_db

        histogram = await bindings_db.count_by_status(int(guild_id))
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.FATAL,
            summary=(
                f"count_by_status raised {type(exc).__name__} — "
                "subsystem_bindings table may be missing."
            ),
            details=(str(exc)[:200],),
        )

    missing = int(histogram.get("missing", 0))
    invalid = int(histogram.get("invalid", 0))
    unresolved = int(histogram.get("unresolved", 0))
    bound = int(histogram.get("bound", 0))
    total = sum(histogram.values())

    # `unresolved` is reported informationally only — current schema
    # has no metadata column separating "configured-but-not-yet-resolved"
    # from "empty slot", so v1 does not promote status from `unresolved`.
    info_line = (
        f"bound={bound} unresolved={unresolved} "
        f"missing={missing} invalid={invalid} (total={total})"
    )

    if missing or invalid:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=(
                f"{missing + invalid} configured-but-broken binding(s) in "
                f"guild {guild_id}."
            ),
            details=(
                info_line,
                "`unresolved` rows reported informationally; they may be "
                "unconfigured slots, not broken bindings.",
            ),
            suggested_actions=(
                "Run `!platform bindings` to see per-subsystem detail.",
            ),
        )
    return SectionResult(
        name=name,
        status=SectionStatus.CLEAN,
        summary=f"no broken bindings in guild {guild_id}.",
        details=(info_line,),
    )


async def _collect_binding_backfill() -> SectionResult:
    """Section 5: binding backfill checkpoints — failed / in-progress."""
    name = "Binding backfill"
    try:
        from utils.db import platform_migration_checkpoints as ck

        counts = await ck.count_by_status(name_prefix="binding_backfill")
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=(f"checkpoint count_by_status raised {type(exc).__name__}"),
            details=(str(exc)[:200],),
        )

    if not counts:
        return SectionResult(
            name=name,
            status=SectionStatus.SKIPPED,
            summary="no `binding_backfill` checkpoint rows.",
        )

    failed = int(counts.get("failed", 0))
    in_progress = int(counts.get("in_progress", 0))
    line = " · ".join(f"{k}={v}" for k, v in sorted(counts.items()))

    if failed:
        return SectionResult(
            name=name,
            status=SectionStatus.FATAL,
            summary=f"{failed} failed backfill checkpoint row(s).",
            details=(line,),
            suggested_actions=(
                "Run `!platform migrations` for the failed checkpoint name "
                "and inspect the bot host logs.",
            ),
        )
    if in_progress:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=f"{in_progress} backfill checkpoint(s) in_progress.",
            details=(line,),
        )
    recognised = {"complete", "dry_run_complete"}
    unknown = {k for k in counts if k not in recognised and counts[k]}
    if unknown:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=(
                "backfill checkpoint(s) in unrecognised status: "
                + ", ".join(sorted(unknown))
            ),
            details=(line,),
        )
    return SectionResult(
        name=name,
        status=SectionStatus.CLEAN,
        summary="backfill checkpoints all complete.",
        details=(line,),
    )


async def _collect_config_arbitration() -> SectionResult:
    """Section 6: config arbitration counters — provider status."""
    name = "Config arbitration"
    try:
        from services import diagnostics_service

        snap = diagnostics_service.snapshot("config_arbitration")
    except KeyError:
        return SectionResult(
            name=name,
            status=SectionStatus.SKIPPED,
            summary="`config_arbitration` provider not registered.",
        )
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=f"snapshot raised {type(exc).__name__}",
            details=(str(exc)[:200],),
        )

    if isinstance(snap, dict) and "_error" in snap:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary="arbitration provider returned _error.",
            details=(str(snap.get("_error"))[:200],),
        )

    arbitration = snap.get("arbitration") if isinstance(snap, dict) else None
    if not isinstance(arbitration, dict):
        return SectionResult(
            name=name,
            status=SectionStatus.CLEAN,
            summary="arbitration counters reachable.",
        )

    calls = int(arbitration.get("calls_total", 0))
    by_source = arbitration.get("by_source") or {}
    fallback = int(by_source.get("fallback", 0)) if isinstance(by_source, dict) else 0
    missing = int(by_source.get("missing", 0)) if isinstance(by_source, dict) else 0

    summary = f"calls_total={calls}; fallback={fallback}; missing={missing}."
    if fallback or missing:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=summary,
            details=(
                "Non-zero fallback/missing indicates the arbiter is degrading "
                "to legacy reads — investigate per `!platform flags`.",
            ),
        )
    return SectionResult(
        name=name,
        status=SectionStatus.CLEAN,
        summary=summary,
    )


async def _collect_participation() -> SectionResult:
    """Section 7: participation storage / cache / mutation / audit."""
    name = "Participation"
    try:
        from utils.db import pool

        part_oid = await pool.get().fetchval(
            "SELECT to_regclass('user_participation')",
        )
        audit_oid = await pool.get().fetchval(
            "SELECT to_regclass('user_participation_audit')",
        )
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=f"table probe raised {type(exc).__name__}",
            details=(str(exc)[:200],),
        )

    if part_oid is None and audit_oid is None:
        return SectionResult(
            name=name,
            status=SectionStatus.SKIPPED,
            summary=(
                "`user_participation` + `user_participation_audit` absent "
                "(migrations 027/028 not applied)."
            ),
        )

    # Cross-check the 4 participation events declared in
    # core.events_catalogue.KNOWN_EVENTS.
    expected_events = frozenset(
        {
            "participation.changed",
            "subscription.changed",
            "user_preference.changed",
            "user_visibility.changed",
        },
    )
    try:
        from core.events_catalogue import KNOWN_EVENTS

        missing_events = expected_events - KNOWN_EVENTS
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        missing_events = expected_events
        events_err: str | None = f"{type(exc).__name__}: {exc}"
    else:
        events_err = None

    snapshots: dict[str, object] = {}
    try:
        from services import diagnostics_service

        for provider in ("participation_schemas", "user_capability_map"):
            try:
                snapshots[provider] = diagnostics_service.snapshot(provider)
            except KeyError:
                snapshots[provider] = {"_error": "provider not registered"}
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        snapshots["__error__"] = f"{type(exc).__name__}: {exc}"

    provider_errors = [
        name
        for name, snap in snapshots.items()
        if isinstance(snap, dict) and "_error" in snap
    ]

    details = [
        f"user_participation present={bool(part_oid)} "
        f"user_participation_audit present={bool(audit_oid)}",
        f"events present={sorted(expected_events - missing_events)}",
    ]
    if missing_events:
        details.append(f"events missing={sorted(missing_events)}")
    if events_err:
        details.append(f"events catalogue error={events_err}")
    if provider_errors:
        details.append(f"provider errors={sorted(provider_errors)}")

    if missing_events or provider_errors or events_err:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=(
                f"participation surface degraded ({len(provider_errors)} "
                f"provider error(s), {len(missing_events)} missing event(s))."
            ),
            details=tuple(details)[:8],
        )
    return SectionResult(
        name=name,
        status=SectionStatus.CLEAN,
        summary="participation storage / providers / events all reachable.",
        details=tuple(details)[:4],
    )


async def _collect_migrations() -> SectionResult:
    """Section 8: filesystem migration ladder + DB-applied set."""
    name = "Migrations"

    # Authoritative source: filesystem.
    if not os.path.isdir(_MIGRATIONS_DIR):
        return SectionResult(
            name=name,
            status=SectionStatus.FATAL,
            summary=f"migrations directory missing: {_MIGRATIONS_DIR}",
        )

    fs_versions: list[int] = []
    for filename in sorted(os.listdir(_MIGRATIONS_DIR)):
        m = _MIGRATION_FILE_RE.match(filename)
        if m:
            try:
                fs_versions.append(int(m.group(1)))
            except ValueError:
                continue
    if not fs_versions:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary="no `NNN_*.sql` migration files found.",
        )

    fs_versions_sorted = sorted(fs_versions)
    highest = fs_versions_sorted[-1]
    lowest = fs_versions_sorted[0]
    expected = set(range(lowest, highest + 1))
    actual = set(fs_versions_sorted)
    gaps = sorted(expected - actual)

    # Secondary source: DB-applied set.  WARNING-only on mismatch.
    db_versions: set[int] | None = None
    db_error: str | None = None
    try:
        from utils.db import pool

        rows = await pool.get().fetch(
            "SELECT version FROM schema_migrations ORDER BY version",
        )
        db_versions = {int(r["version"]) for r in rows}
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        db_error = f"{type(exc).__name__}: {exc}"

    details = [
        f"filesystem: lowest={lowest} highest={highest} count={len(actual)}",
    ]
    if db_versions is not None:
        details.append(
            f"db-applied: count={len(db_versions)} "
            f"highest={max(db_versions) if db_versions else 0}",
        )
    if db_error:
        details.append(f"db probe error: {db_error}")

    warnings: list[str] = []
    if gaps:
        warnings.append(f"filesystem numbering gap(s): {gaps[:5]}")
    if db_versions is not None and (actual - db_versions):
        pending = sorted(actual - db_versions)
        warnings.append(f"pending DB migrations: {pending[:5]}")
    if db_error:
        warnings.append("db probe failed (filesystem still authoritative)")

    if warnings:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary="; ".join(warnings)[:200],
            details=tuple(details)[:6],
        )
    return SectionResult(
        name=name,
        status=SectionStatus.CLEAN,
        summary=f"ladder contiguous {lowest:03d} → {highest:03d}; all applied.",
        details=tuple(details)[:4],
    )


async def _collect_runtime_providers() -> SectionResult:
    """Section 9: meta-health summary of the diagnostics provider registry.

    Reports only provider counts and which (if any) returned ``_error``.
    Domain analysis lives in the dedicated sections — this section does
    not inspect provider contents.
    """
    name = "Runtime providers"
    try:
        from services import diagnostics_service

        names = diagnostics_service.registered_names()
        snap = diagnostics_service.snapshot_all()
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=f"registry walk raised {type(exc).__name__}",
            details=(str(exc)[:200],),
        )

    if not names:
        return SectionResult(
            name=name,
            status=SectionStatus.SKIPPED,
            summary="no providers registered.",
        )

    errors = sorted(n for n, v in snap.items() if isinstance(v, dict) and "_error" in v)
    if errors:
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=(f"{len(errors)}/{len(names)} provider(s) reported _error."),
            details=(f"errored: {', '.join(errors[:8])}",),
        )
    return SectionResult(
        name=name,
        status=SectionStatus.CLEAN,
        summary=f"{len(names)} provider(s) registered; all returned OK.",
    )


async def _collect_setup_readiness() -> SectionResult:
    """Section 10: roadmap blockers for the larger UX phase (informational).

    v1 returns a static list from ``SETUP_READINESS_BLOCKERS``.  Dynamic
    detection of each blocker's resolution state is deferred to a
    follow-up PR.  The section is marked ``informational=True`` so the
    embed labels it as roadmap-only and ``overall_status`` does not
    promote on it.
    """
    name = "Setup readiness"
    if not SETUP_READINESS_BLOCKERS:
        return SectionResult(
            name=name,
            status=SectionStatus.CLEAN,
            summary="No roadmap blockers.",
            informational=True,
        )
    return SectionResult(
        name=name,
        status=SectionStatus.WARNING,
        summary=(
            f"{len(SETUP_READINESS_BLOCKERS)} roadmap blocker(s) "
            "tracked (informational; not a runtime health failure)."
        ),
        details=tuple(SETUP_READINESS_BLOCKERS),
        suggested_actions=(
            "See `docs/phase-2-completion-readiness.md` for unlock order.",
        ),
        informational=True,
    )


__all__ = [
    "ConsistencyReport",
    "SETUP_READINESS_BLOCKERS",
    "SectionResult",
    "SectionStatus",
    "collect_report",
]
