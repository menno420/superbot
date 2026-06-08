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
    ReadinessKind               — enum (typed identity per section)
    READINESS_KINDS             — canonical-order tuple of every kind
    SectionResult               — frozen dataclass per section
    ConsistencyReport           — frozen dataclass: sections + overall_status
    SETUP_READINESS_BLOCKERS    — tuple of roadmap blocker identifiers
    collect_report(*, bot, guild) — async orchestrator
    iter_blocking_sections(report) — non-informational, non-CLEAN sections
"""

from __future__ import annotations

import dataclasses
import datetime
import logging
import os
import re
from collections.abc import Awaitable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger("bot.platform_consistency")


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class SectionStatus(str, Enum):
    CLEAN = "clean"
    WARNING = "warning"
    FATAL = "fatal"
    SKIPPED = "skipped"


class ReadinessKind(str, Enum):
    """Canonical typed identity for each consistency section.

    PR-01a: every section result returned by ``collect_report`` is
    stamped with one of these kinds by the orchestrator (collectors
    do not need to know about kinds — the orchestrator maps from
    the human label to the typed kind).

    ``READINESS_KINDS`` exports the canonical ordering used by the
    orchestrator and consumers; the invariant test
    ``tests/unit/invariants/test_platform_consistency_kinds.py`` pins
    every collector to a known kind.
    """

    IDENTITY_CONTRACT = "identity_contract"
    FEATURE_FLAGS = "feature_flags"
    ROLLOUT_AUDIT = "rollout_audit"
    BINDINGS = "bindings"
    BINDING_BACKFILL = "binding_backfill"
    CONFIG_ARBITRATION = "config_arbitration"
    PARTICIPATION = "participation"
    MIGRATIONS = "migrations"
    RUNTIME_PROVIDERS = "runtime_providers"
    LIFECYCLE = "lifecycle"
    SETUP_READINESS = "setup_readiness"
    WIZARD_FINALIZATION = "wizard_finalization"


# Canonical ordering — matches the orchestrator's collector tuple at
# ``collect_report``.  ``test_readiness_kinds_canonical_ordering`` pins
# this ordering so the diagnostic embed and the readiness snapshot can
# rely on a stable section order.
READINESS_KINDS: tuple[ReadinessKind, ...] = (
    ReadinessKind.IDENTITY_CONTRACT,
    ReadinessKind.FEATURE_FLAGS,
    ReadinessKind.ROLLOUT_AUDIT,
    ReadinessKind.BINDINGS,
    ReadinessKind.BINDING_BACKFILL,
    ReadinessKind.CONFIG_ARBITRATION,
    ReadinessKind.PARTICIPATION,
    ReadinessKind.MIGRATIONS,
    ReadinessKind.RUNTIME_PROVIDERS,
    ReadinessKind.LIFECYCLE,
    ReadinessKind.SETUP_READINESS,
    ReadinessKind.WIZARD_FINALIZATION,
)


# Maps the human-readable label used by the orchestrator's collector
# tuple to the typed ``ReadinessKind``.  The orchestrator stamps each
# collector's ``SectionResult.kind`` from this map after the collector
# returns, so collectors themselves never need to set ``kind``.
_LABEL_TO_KIND: dict[str, ReadinessKind] = {
    "Identity contract": ReadinessKind.IDENTITY_CONTRACT,
    "Feature flags": ReadinessKind.FEATURE_FLAGS,
    "Rollout / audit": ReadinessKind.ROLLOUT_AUDIT,
    "Bindings": ReadinessKind.BINDINGS,
    "Binding backfill": ReadinessKind.BINDING_BACKFILL,
    "Config arbitration": ReadinessKind.CONFIG_ARBITRATION,
    "Participation": ReadinessKind.PARTICIPATION,
    "Migrations": ReadinessKind.MIGRATIONS,
    "Runtime providers": ReadinessKind.RUNTIME_PROVIDERS,
    "Lifecycle": ReadinessKind.LIFECYCLE,
    "Setup readiness": ReadinessKind.SETUP_READINESS,
    "Wizard finalization": ReadinessKind.WIZARD_FINALIZATION,
}


@dataclass(frozen=True)
class SectionResult:
    name: str
    status: SectionStatus
    summary: str
    details: tuple[str, ...] = ()
    suggested_actions: tuple[str, ...] = ()
    informational: bool = False
    # PR-01a: typed identity stamped by the orchestrator after each
    # collector returns.  Optional only so collectors can construct
    # ``SectionResult`` without knowing the kind; the orchestrator
    # guarantees every section in a collected report has a non-None
    # kind.  Consumers that build sections outside ``collect_report``
    # (e.g. unit tests) may leave it as ``None``.
    kind: ReadinessKind | None = None


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


# PR-03: derived from the dynamic ``services.setup_blockers.BLOCKERS``
# registry so the bare-string contract is preserved for backwards-
# compatible callers (e.g. the doc test) while the actual resolution
# state is computed dynamically from cached foundation state.  See
# ``services/setup_blockers.py`` for the registry, status providers,
# and ownership metadata.
def _setup_readiness_blocker_ids() -> tuple[str, ...]:
    # Function-local import keeps this module's import graph
    # unchanged (setup_blockers itself only imports stdlib at module
    # scope; each status_provider imports the runtime modules it
    # needs function-locally).
    from services import setup_blockers

    return setup_blockers.blocker_ids()


SETUP_READINESS_BLOCKERS: tuple[str, ...] = _setup_readiness_blocker_ids()


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
        ("Lifecycle", _collect_lifecycle()),
        ("Setup readiness", _collect_setup_readiness()),
        ("Wizard finalization", _collect_wizard_finalization()),
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
        # PR-01a: stamp the canonical readiness kind from the label.
        # Collectors construct SectionResult without knowing the kind;
        # the orchestrator is the single place where the human label
        # is translated into the typed ``ReadinessKind``.
        if result.kind is None:
            result = dataclasses.replace(result, kind=_LABEL_TO_KIND[label])
        sections.append(result)
    report = ConsistencyReport(
        sections=tuple(sections),
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    # PR-01b: cache the most recent report so the sync readiness
    # snapshot can include its overall status + blocking section
    # summary without re-entering this async collector.  Consumers
    # that need a fresh report still call ``collect_report`` directly.
    global _LAST_REPORT
    _LAST_REPORT = report
    return report


# PR-01b: in-process cache of the most recent ``ConsistencyReport``.
# Populated at the end of every ``collect_report`` call so the sync
# ``build_readiness_snapshot`` can read it without awaiting.  ``None``
# until the first call.
_LAST_REPORT: ConsistencyReport | None = None


def get_last_report() -> ConsistencyReport | None:
    """Return the most recent ``ConsistencyReport`` or ``None``.

    Sync accessor used by the readiness snapshot.  Does not trigger a
    new collection — consumers that want fresh data must call
    ``collect_report`` themselves.
    """
    return _LAST_REPORT


def iter_blocking_sections(
    report: ConsistencyReport,
) -> tuple[SectionResult, ...]:
    """Return only non-informational, non-CLEAN sections.

    PR-01a helper used by the upcoming readiness snapshot (PR-01b) and
    smoke checklist (PR-05) to surface the subset of sections that
    represent actionable signal — informational roadmap warnings
    (e.g. "Setup readiness") and CLEAN sections are filtered out.

    ``SKIPPED`` sections are included because "not applicable" can
    still be a release-relevant signal (e.g. a migration not yet
    applied that should be).  Consumers that want to filter further
    can do so on the returned tuple.
    """
    return tuple(
        s
        for s in report.sections
        if not s.informational and s.status is not SectionStatus.CLEAN
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
        # PR1: name *which* keys degraded, not just how many.  The
        # attribution list is redacted (internal IDs only) and bounded
        # by config_arbitration; absence is handled gracefully.
        attribution = snap.get("attribution") if isinstance(snap, dict) else None
        detail_lines = [
            "Non-zero fallback/missing — the arbiter is degrading to legacy "
            "reads. Offending keys:",
        ]
        if isinstance(attribution, list) and attribution:
            for rec in attribution[:4]:
                if not isinstance(rec, dict):
                    continue
                detail_lines.append(
                    f"{rec.get('subsystem')}/{rec.get('binding_name')} "
                    f"(legacy={rec.get('legacy_key')}) "
                    f"src={rec.get('source')} flag={rec.get('flag_state')} "
                    f"binding={rec.get('binding_status')}",
                )
        else:
            detail_lines.append(
                "Per-key attribution unavailable — see `!platform flags`.",
            )
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=summary,
            details=tuple(detail_lines),
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


async def _collect_lifecycle() -> SectionResult:
    """Section 10: process lifecycle phase + pending request snapshot (LP-6).

    Sync read of the in-memory :mod:`core.runtime.lifecycle` state.
    Severity map:

    * ``RUNNING``                                 → CLEAN.
    * ``STARTING``                                → CLEAN (boot in
      progress; benign).
    * ``DRAINING`` / ``SHUTTING_DOWN`` /
      ``RESTARTING`` / ``STOPPED``                → WARNING (winding
      down; commands are being rejected).
    * ``FAILED_STARTUP``                          → FATAL (startup
      raised before RUNNING; no traffic should be routed here).
    """
    name = "Lifecycle"
    try:
        from core.runtime import lifecycle
    except Exception as exc:  # noqa: BLE001 — collector is fail-safe
        return SectionResult(
            name=name,
            status=SectionStatus.WARNING,
            summary=f"lifecycle import raised {type(exc).__name__}",
            details=(str(exc)[:200],),
        )

    snapshot = lifecycle.diagnostics_snapshot()
    phase_value = str(snapshot.get("phase", "UNKNOWN"))
    pending = snapshot.get("pending")

    details_list: list[str] = [f"phase: {phase_value}"]
    if pending:
        details_list.append(
            f"pending: kind={pending['kind']!r} reason={pending['reason']!r} "
            f"actor={pending['actor']!r}",
        )
    remaining = snapshot.get("remaining_shutdown_seconds")
    if isinstance(remaining, (int, float)):
        details_list.append(f"remaining_grace_seconds: {float(remaining):.1f}")
    recent = snapshot.get("recent_events") or []
    if recent:
        details_list.append(
            f"recent_events: {len(recent)} (latest: {recent[-1]['name']!r})",
        )

    if phase_value == lifecycle.Phase.RUNNING.value:
        return SectionResult(
            name=name,
            status=SectionStatus.CLEAN,
            summary="bot is RUNNING; commands are being admitted.",
            details=tuple(details_list),
        )
    if phase_value == lifecycle.Phase.STARTING.value:
        return SectionResult(
            name=name,
            status=SectionStatus.CLEAN,
            summary="bot is STARTING; on_ready has not fired yet.",
            details=tuple(details_list),
        )
    if phase_value == lifecycle.Phase.FAILED_STARTUP.value:
        return SectionResult(
            name=name,
            status=SectionStatus.FATAL,
            summary="bot is in FAILED_STARTUP; do not route traffic here.",
            details=tuple(details_list),
            suggested_actions=(
                "Inspect startup logs for the cause; the bot must be "
                "rebooted to clear this terminal state.",
            ),
        )
    # DRAINING / SHUTTING_DOWN / RESTARTING / STOPPED — bot is winding down.
    return SectionResult(
        name=name,
        status=SectionStatus.WARNING,
        summary=(
            f"bot is {phase_value}; new commands are being rejected "
            f"by the channel guard."
        ),
        details=tuple(details_list),
    )


async def _collect_setup_readiness() -> SectionResult:
    """Section 10: roadmap blockers for the larger UX phase (informational).

    PR-03: dynamic — each blocker in
    ``services.setup_blockers.BLOCKERS`` computes its own status from
    cached in-process state.  Resolved blockers drop out of the
    details list; pending / in_progress / blocked / unknown remain
    visible.  The section is still ``informational=True`` so the
    embed labels it as roadmap-only and ``overall_status`` does not
    promote on it.

    Status providers are sync and fail-safe — a raising provider
    becomes ``"unknown"`` rather than crashing this collector.
    """
    name = "Setup readiness"
    # Function-local: setup_blockers transitively imports
    # core.runtime modules in its status providers; module-scope
    # import would violate the cycle-sensitive contract pinned by
    # test_consistency_import_cycle.py.
    from services import setup_blockers

    statuses: list[tuple[str, str]] = [
        (spec.id, setup_blockers.status_for(spec)) for spec in setup_blockers.BLOCKERS
    ]
    resolved = sum(1 for _, st in statuses if st == "resolved")
    pending = [bid for bid, st in statuses if st != "resolved"]
    total = len(statuses)

    if not pending:
        return SectionResult(
            name=name,
            status=SectionStatus.CLEAN,
            summary=(f"All {total} roadmap blocker(s) resolved."),
            informational=True,
        )

    details = tuple(f"{bid}: {st}" for bid, st in statuses)
    return SectionResult(
        name=name,
        status=SectionStatus.WARNING,
        summary=(
            f"{resolved}/{total} roadmap blocker(s) resolved "
            "(informational; not a runtime health failure)."
        ),
        details=details,
        suggested_actions=(
            "See `docs/archive/phase-2-completion-readiness.md` for unlock order.",
        ),
        informational=True,
    )


async def _collect_wizard_finalization() -> SectionResult:
    """Section 11: setup-wizard finalization progress (informational).

    Reports how far the PR1–PR3 setup-wizard finalization tranche
    (``docs/setup-platform/setup_wizard_finalization_plan.md``) has landed so progress
    is observable from ``!platform consistency``.  Each item's status
    comes from a sync, fail-safe provider in
    :mod:`services.wizard_finalization`; the section is
    ``informational=True`` so it never promotes ``overall_status``.
    """
    name = "Wizard finalization"
    # Function-local import keeps this module's import graph cycle-free
    # (matches the discipline pinned by test_consistency_import_cycle).
    from services import wizard_finalization

    items = wizard_finalization.statuses()
    total = len(items)
    resolved = sum(1 for it in items if it.status == "resolved")
    # "deferred" items are intentionally out of the tranche, so they do
    # not count as pending work.
    pending = [it for it in items if it.status not in ("resolved", "deferred")]
    details = tuple(f"{it.id} [{it.pr}]: {it.status}" for it in items)

    if not pending:
        return SectionResult(
            name=name,
            status=SectionStatus.CLEAN,
            summary=f"{resolved}/{total} finalization step(s) landed; rest deferred.",
            details=details,
            informational=True,
        )
    return SectionResult(
        name=name,
        status=SectionStatus.WARNING,
        summary=(
            f"{resolved}/{total} finalization step(s) landed "
            "(informational; setup-wizard finalization in progress)."
        ),
        details=details,
        suggested_actions=(
            "See `docs/setup-platform/setup_wizard_finalization_plan.md` (PR1–PR3).",
        ),
        informational=True,
    )


# ---------------------------------------------------------------------------
# PR-01b — Platform readiness snapshot (sync)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadinessSnapshot:
    """A composite sync view of the bot's "safe to restart/deploy?" state.

    Built from already-cached signals: the most recent
    ``ConsistencyReport`` (populated by ``collect_report``), the
    canonical task supervisor, the catalogue/registry build outcomes
    recorded by ``core.runtime.startup_outcome``, and the cached
    ledger/registry/customization/provisioning state.

    Sync-only by design so it fits the existing sync
    ``diagnostics_service.register`` contract.  Consumers that want a
    fresh consistency report must call ``collect_report`` separately
    via the existing async path.
    """

    generated_at: datetime.datetime
    # Consistency report summary — None if collect_report has never
    # been called this process.
    consistency_overall_status: SectionStatus | None
    consistency_report_at: datetime.datetime | None
    consistency_blocking_sections: tuple[SectionResult, ...]
    # Catalogue/registry build outcomes (PR-01b recorder).  One per
    # KNOWN_PHASES entry; missing names indicate the phase did not
    # reach its try/except yet (e.g. crash earlier in startup).
    startup_outcomes: tuple[Any, ...]  # tuple[StartupOutcome, ...]
    # Cached state booleans — set by the corresponding build_*
    # function on success.  ``False`` means either "not built yet" or
    # "build failed"; consult ``startup_outcomes`` for the cause.
    ledger_built: bool
    settings_registry_built: bool
    customization_catalogue_built: bool
    provisioning_catalogue_built: bool
    # Canonical task supervisor snapshot.
    tasks_active_count: int
    tasks_active_names: tuple[str, ...]


def build_readiness_snapshot() -> ReadinessSnapshot:
    """Compose the readiness snapshot from cached signals.

    Pure sync — every input comes from a process-local cache or an
    in-memory state machine.  Safe to call from a diagnostics provider
    or any sync render path.

    Imports are function-local because ``core.runtime`` is
    cycle-sensitive in this codebase; the companion
    ``test_consistency_import_cycle.py`` pins the discipline.
    """
    from core.runtime import (
        command_surface_ledger,
        settings_registry,
        startup_outcome,
        tasks,
    )
    from services import customization_catalogue, resource_provisioning_catalogue

    last = _LAST_REPORT
    overall = last.overall_status if last is not None else None
    report_at = last.generated_at if last is not None else None
    blocking = iter_blocking_sections(last) if last is not None else ()

    active = tasks.active()
    active_names = tuple(sorted(t.get_name() for t in active))

    return ReadinessSnapshot(
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
        consistency_overall_status=overall,
        consistency_report_at=report_at,
        consistency_blocking_sections=blocking,
        startup_outcomes=startup_outcome.all_outcomes(),
        ledger_built=command_surface_ledger.get_cached_ledger() is not None,
        settings_registry_built=(settings_registry.get_cached_registry() is not None),
        customization_catalogue_built=(
            customization_catalogue.get_cached_catalogue() is not None
        ),
        provisioning_catalogue_built=(
            resource_provisioning_catalogue.get_cached_provisioning_catalogue()
            is not None
        ),
        tasks_active_count=len(active),
        tasks_active_names=active_names,
    )


def _readiness_snapshot_dict() -> dict[str, Any]:
    """Diagnostics provider — dict view of the readiness snapshot.

    Sync; safe to register with ``services.diagnostics_service``.
    Errors during composition surface as ``{"_error": "..."}`` so a
    broken provider does not crash the diagnostics dump.
    """
    try:
        snap = build_readiness_snapshot()
    except Exception as exc:  # noqa: BLE001 — diagnostics is fail-safe
        return {"_error": f"{type(exc).__name__}: {exc}"}
    return {
        "generated_at": snap.generated_at.isoformat(),
        "consistency": {
            "overall_status": (
                snap.consistency_overall_status.value
                if snap.consistency_overall_status is not None
                else None
            ),
            "report_at": (
                snap.consistency_report_at.isoformat()
                if snap.consistency_report_at is not None
                else None
            ),
            "blocking_section_count": len(snap.consistency_blocking_sections),
            "blocking_sections": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "kind": s.kind.value if s.kind is not None else None,
                }
                for s in snap.consistency_blocking_sections
            ],
        },
        "startup": {
            "outcomes": [
                {
                    "name": o.name,
                    "success": o.success,
                    "error": o.error,
                    "recorded_at": o.recorded_at.isoformat(),
                }
                for o in snap.startup_outcomes
            ],
        },
        "catalogues": {
            "ledger_built": snap.ledger_built,
            "settings_registry_built": snap.settings_registry_built,
            "customization_catalogue_built": snap.customization_catalogue_built,
            "provisioning_catalogue_built": snap.provisioning_catalogue_built,
        },
        "tasks": {
            "active_count": snap.tasks_active_count,
            "active_names": list(snap.tasks_active_names),
        },
    }


def _register_diagnostics() -> None:
    """Register the sync readiness provider.

    Best-effort: if the diagnostics service is unavailable for some
    reason, the snapshot still works — only the discoverability via
    ``!platform diagnostics`` is lost.
    """
    try:
        from services import diagnostics_service

        diagnostics_service.register(
            "platform_readiness",
            _readiness_snapshot_dict,
        )
    except Exception as exc:  # noqa: BLE001 — registration is best-effort
        logger.warning(
            "platform_readiness diagnostics provider registration failed: %s",
            exc,
        )


_register_diagnostics()


__all__ = [
    "ConsistencyReport",
    "READINESS_KINDS",
    "ReadinessKind",
    "ReadinessSnapshot",
    "SETUP_READINESS_BLOCKERS",
    "SectionResult",
    "SectionStatus",
    "build_readiness_snapshot",
    "collect_report",
    "get_last_report",
    "iter_blocking_sections",
]
