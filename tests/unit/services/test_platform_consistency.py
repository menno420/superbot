"""Unit tests for services.platform_consistency — Phase 2 PR-10."""

from __future__ import annotations

import asyncio
import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from services import platform_consistency as pc

# ---------------------------------------------------------------------------
# Status promotion logic
# ---------------------------------------------------------------------------


def _make_section(
    status: pc.SectionStatus, *, informational: bool = False
) -> pc.SectionResult:
    return pc.SectionResult(
        name=f"section-{status.value}",
        status=status,
        summary="summary",
        informational=informational,
    )


def _report(
    *statuses: pc.SectionStatus, informational: tuple[bool, ...] | None = None
) -> pc.ConsistencyReport:
    if informational is None:
        informational = (False,) * len(statuses)
    sections = tuple(
        _make_section(s, informational=info)
        for s, info in zip(statuses, informational, strict=False)
    )
    return pc.ConsistencyReport(
        sections=sections,
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )


def test_overall_status_promotes_fatal_over_warning():
    r = _report(
        pc.SectionStatus.WARNING, pc.SectionStatus.FATAL, pc.SectionStatus.CLEAN
    )
    assert r.overall_status == pc.SectionStatus.FATAL


def test_overall_status_warning_when_no_fatal():
    r = _report(
        pc.SectionStatus.CLEAN, pc.SectionStatus.WARNING, pc.SectionStatus.SKIPPED
    )
    assert r.overall_status == pc.SectionStatus.WARNING


def test_overall_status_all_skipped_returns_skipped():
    r = _report(pc.SectionStatus.SKIPPED, pc.SectionStatus.SKIPPED)
    assert r.overall_status == pc.SectionStatus.SKIPPED


def test_overall_status_skipped_does_not_demote_clean():
    r = _report(
        pc.SectionStatus.CLEAN, pc.SectionStatus.SKIPPED, pc.SectionStatus.CLEAN
    )
    assert r.overall_status == pc.SectionStatus.CLEAN


def test_overall_status_ignores_informational_warning():
    """Informational WARNING (Setup readiness) does not demote CLEAN."""
    r = _report(
        pc.SectionStatus.CLEAN,
        pc.SectionStatus.WARNING,
        informational=(False, True),
    )
    assert r.overall_status == pc.SectionStatus.CLEAN


def test_overall_status_clean_when_only_informational_sections():
    r = pc.ConsistencyReport(
        sections=(_make_section(pc.SectionStatus.WARNING, informational=True),),
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    assert r.overall_status == pc.SectionStatus.SKIPPED


# ---------------------------------------------------------------------------
# Orchestrator — collector exception isolation
# ---------------------------------------------------------------------------


def test_collect_report_isolates_collector_exception():
    """If a section collector raises, the report still contains the section
    with status=FATAL and summary identifying the exception class."""

    async def bad_collector() -> pc.SectionResult:
        raise RuntimeError("boom")

    async def good_collector() -> pc.SectionResult:
        return pc.SectionResult(
            name="ok",
            status=pc.SectionStatus.CLEAN,
            summary="fine",
        )

    # Patch every collector except identity to a fast-CLEAN async stub so
    # the orchestrator returns deterministically.
    with patch.multiple(
        pc,
        _collect_identity_contract=lambda bot: bad_collector(),
        _collect_feature_flags=lambda: good_collector(),
        _collect_rollout_audit=lambda: good_collector(),
        _collect_bindings=lambda guild: good_collector(),
        _collect_binding_backfill=lambda: good_collector(),
        _collect_config_arbitration=lambda: good_collector(),
        _collect_participation=lambda: good_collector(),
        _collect_migrations=lambda: good_collector(),
        _collect_runtime_providers=lambda: good_collector(),
        _collect_lifecycle=lambda: good_collector(),
        _collect_setup_readiness=lambda: good_collector(),
        _collect_wizard_finalization=lambda: good_collector(),
    ):
        report = asyncio.run(pc.collect_report(bot=object(), guild=None))

    assert len(report.sections) == 12
    identity = report.sections[0]
    assert identity.status == pc.SectionStatus.FATAL
    assert "RuntimeError" in identity.summary


def test_collect_report_is_guild_aware_passes_guild_to_bindings():
    """The bindings collector must receive the guild passed to collect_report."""
    captured: dict[str, object] = {}

    async def capturing_bindings(guild: object | None) -> pc.SectionResult:
        captured["guild"] = guild
        return pc.SectionResult(
            name="Bindings",
            status=pc.SectionStatus.SKIPPED,
            summary="captured",
        )

    async def trivial(*args, **kwargs) -> pc.SectionResult:
        return pc.SectionResult(name="x", status=pc.SectionStatus.SKIPPED, summary="x")

    sentinel_guild = object()
    with patch.multiple(
        pc,
        _collect_identity_contract=trivial,
        _collect_feature_flags=trivial,
        _collect_rollout_audit=trivial,
        _collect_bindings=capturing_bindings,
        _collect_binding_backfill=trivial,
        _collect_config_arbitration=trivial,
        _collect_participation=trivial,
        _collect_migrations=trivial,
        _collect_runtime_providers=trivial,
        _collect_setup_readiness=trivial,
    ):
        asyncio.run(pc.collect_report(bot=None, guild=sentinel_guild))

    assert captured["guild"] is sentinel_guild


# ---------------------------------------------------------------------------
# Identity contract collector — uses the live validate_identity_contract
# ---------------------------------------------------------------------------


def test_identity_contract_skipped_when_bot_is_none():
    result = asyncio.run(pc._collect_identity_contract(None))
    assert result.status == pc.SectionStatus.SKIPPED


def test_identity_contract_clean_when_findings_empty():
    async def stub(_bot):
        return {}

    with patch(
        "utils.subsystem_registry.validate_identity_contract",
        side_effect=stub,
    ):
        result = asyncio.run(pc._collect_identity_contract(object()))
    assert result.status == pc.SectionStatus.CLEAN


def test_identity_contract_warning_when_only_warn_only():
    async def stub(_bot):
        return {"schema_subsystem_unknown": ["x", "y"]}

    with patch(
        "utils.subsystem_registry.validate_identity_contract",
        side_effect=stub,
    ):
        result = asyncio.run(pc._collect_identity_contract(object()))
    assert result.status == pc.SectionStatus.WARNING


def test_identity_contract_fatal_when_fatal_tier():
    async def stub(_bot):
        return {"entry_point_missing_command": ["zzz"]}

    with patch(
        "utils.subsystem_registry.validate_identity_contract",
        side_effect=stub,
    ):
        result = asyncio.run(pc._collect_identity_contract(object()))
    assert result.status == pc.SectionStatus.FATAL


def test_identity_contract_no_wait_for_used():
    """Clarification #1: collector must NOT wrap the validator in
    asyncio.wait_for in v1.  Keeps the collector simple; a timeout
    can be added in a follow-up PR if data justifies it."""
    src = Path(pc.__file__).read_text()
    assert "asyncio.wait_for" not in src


# ---------------------------------------------------------------------------
# Feature flags collector
# ---------------------------------------------------------------------------


def test_feature_flags_warning_when_bootstrap_fallback_positive():
    fake_flags = {"foo": object(), "bar": object()}

    async def fake_resolve(_name, _gid):
        return ("decision", "source")

    with (
        patch("core.runtime.feature_flags.all_flags", return_value=fake_flags),
        patch(
            "core.runtime.feature_flags.resolve_with_provenance",
            side_effect=fake_resolve,
        ),
        patch(
            "core.runtime.feature_flags.bootstrap_fallback_count",
            return_value=3,
        ),
    ):
        result = asyncio.run(pc._collect_feature_flags())
    assert result.status == pc.SectionStatus.WARNING
    assert "fallback" in result.summary.lower()


def test_feature_flags_clean_when_no_fallback():
    fake_flags = {"foo": object()}

    async def fake_resolve(_name, _gid):
        return ("decision", "source")

    with (
        patch("core.runtime.feature_flags.all_flags", return_value=fake_flags),
        patch(
            "core.runtime.feature_flags.resolve_with_provenance",
            side_effect=fake_resolve,
        ),
        patch(
            "core.runtime.feature_flags.bootstrap_fallback_count",
            return_value=0,
        ),
    ):
        result = asyncio.run(pc._collect_feature_flags())
    assert result.status == pc.SectionStatus.CLEAN


def test_feature_flags_fatal_when_resolve_raises():
    fake_flags = {"foo": object()}

    async def fake_resolve(_name, _gid):
        raise RuntimeError("evaluator dead")

    with (
        patch("core.runtime.feature_flags.all_flags", return_value=fake_flags),
        patch(
            "core.runtime.feature_flags.resolve_with_provenance",
            side_effect=fake_resolve,
        ),
    ):
        result = asyncio.run(pc._collect_feature_flags())
    assert result.status == pc.SectionStatus.FATAL


def test_feature_flags_does_not_assert_malformed_override():
    """Clarification #2: collector must NOT claim to detect malformed
    overrides, because resolve_with_provenance does not expose that
    signal today.  Verified by reading the collector source: only the
    API-exposed signals (all_flags, resolve_with_provenance,
    bootstrap_fallback_count) are referenced."""
    src = Path(pc.__file__).read_text()
    # Find the feature flags collector body.
    start = src.index("async def _collect_feature_flags")
    end = src.index("async def _collect_rollout_audit", start)
    body = src[start:end]
    # The collector must not mention "malformed" anywhere — that
    # would imply a signal we cannot read.
    assert "malformed" not in body.lower()
    # Sanity: it must use the API-exposed signals.
    assert "bootstrap_fallback_count" in body
    assert "resolve_with_provenance" in body


# ---------------------------------------------------------------------------
# Bindings collector
# ---------------------------------------------------------------------------


def test_bindings_warning_on_missing_or_invalid_only():
    guild = type("G", (), {"id": 42})()
    fake_histogram = {"bound": 5, "unresolved": 2, "missing": 1, "invalid": 0}
    with patch(
        "utils.db.bindings.count_by_status",
        new_callable=AsyncMock,
        return_value=fake_histogram,
    ):
        result = asyncio.run(pc._collect_bindings(guild))
    assert result.status == pc.SectionStatus.WARNING
    assert "broken" in result.summary.lower()


def test_bindings_unresolved_does_not_promote_status():
    """Regression: `unresolved` alone is unconfigured-by-default and
    must not be reported as a broken binding in v1."""
    guild = type("G", (), {"id": 42})()
    fake_histogram = {"bound": 5, "unresolved": 10, "missing": 0, "invalid": 0}
    with patch(
        "utils.db.bindings.count_by_status",
        new_callable=AsyncMock,
        return_value=fake_histogram,
    ):
        result = asyncio.run(pc._collect_bindings(guild))
    assert result.status == pc.SectionStatus.CLEAN


def test_bindings_skipped_when_guild_is_none():
    result = asyncio.run(pc._collect_bindings(None))
    assert result.status == pc.SectionStatus.SKIPPED


def test_bindings_fatal_when_db_raises():
    guild = type("G", (), {"id": 42})()
    with patch(
        "utils.db.bindings.count_by_status",
        new_callable=AsyncMock,
        side_effect=RuntimeError("table missing"),
    ):
        result = asyncio.run(pc._collect_bindings(guild))
    assert result.status == pc.SectionStatus.FATAL


# ---------------------------------------------------------------------------
# Binding backfill collector
# ---------------------------------------------------------------------------


def test_binding_backfill_warning_on_in_progress():
    with patch(
        "utils.db.platform_migration_checkpoints.count_by_status",
        new_callable=AsyncMock,
        return_value={"complete": 5, "in_progress": 1},
    ):
        result = asyncio.run(pc._collect_binding_backfill())
    assert result.status == pc.SectionStatus.WARNING


def test_binding_backfill_fatal_on_failed():
    with patch(
        "utils.db.platform_migration_checkpoints.count_by_status",
        new_callable=AsyncMock,
        return_value={"complete": 3, "failed": 2},
    ):
        result = asyncio.run(pc._collect_binding_backfill())
    assert result.status == pc.SectionStatus.FATAL


def test_binding_backfill_skipped_when_no_rows():
    with patch(
        "utils.db.platform_migration_checkpoints.count_by_status",
        new_callable=AsyncMock,
        return_value={},
    ):
        result = asyncio.run(pc._collect_binding_backfill())
    assert result.status == pc.SectionStatus.SKIPPED


def test_binding_backfill_clean_when_only_complete():
    with patch(
        "utils.db.platform_migration_checkpoints.count_by_status",
        new_callable=AsyncMock,
        return_value={"complete": 4, "dry_run_complete": 2},
    ):
        result = asyncio.run(pc._collect_binding_backfill())
    assert result.status == pc.SectionStatus.CLEAN


# ---------------------------------------------------------------------------
# Migrations collector
# ---------------------------------------------------------------------------


def test_migrations_warning_on_numbering_gap(tmp_path, monkeypatch):
    # Create a fake migrations directory with a gap (001, 002, 005).
    for n in (1, 2, 5):
        (tmp_path / f"{n:03d}_test.sql").write_text("-- noop")
    monkeypatch.setattr(pc, "_MIGRATIONS_DIR", str(tmp_path))

    # Stub the DB to return the full filesystem set so the only signal
    # is the filesystem gap.
    async def fake_fetch(*_args, **_kwargs):
        return [{"version": n} for n in (1, 2, 5)]

    fake_pool = type("P", (), {"fetch": staticmethod(fake_fetch)})()
    with patch("utils.db.pool.get", return_value=fake_pool):
        result = asyncio.run(pc._collect_migrations())
    assert result.status == pc.SectionStatus.WARNING
    assert "gap" in result.summary.lower()


def test_migrations_warning_when_db_query_raises_but_files_clean(tmp_path, monkeypatch):
    for n in (1, 2, 3):
        (tmp_path / f"{n:03d}_test.sql").write_text("-- noop")
    monkeypatch.setattr(pc, "_MIGRATIONS_DIR", str(tmp_path))

    def boom():
        raise RuntimeError("pool down")

    with patch("utils.db.pool.get", side_effect=boom):
        result = asyncio.run(pc._collect_migrations())
    assert result.status == pc.SectionStatus.WARNING
    assert (
        "db probe" in result.summary.lower()
        or "db probe" in " ".join(result.details).lower()
    )


def test_migrations_fatal_when_directory_missing(monkeypatch):
    monkeypatch.setattr(pc, "_MIGRATIONS_DIR", "/nonexistent/path/for/test")
    result = asyncio.run(pc._collect_migrations())
    assert result.status == pc.SectionStatus.FATAL


def test_migrations_clean_when_contiguous_and_applied(tmp_path, monkeypatch):
    for n in (1, 2, 3):
        (tmp_path / f"{n:03d}_test.sql").write_text("-- noop")
    monkeypatch.setattr(pc, "_MIGRATIONS_DIR", str(tmp_path))

    async def fake_fetch(*_args, **_kwargs):
        return [{"version": n} for n in (1, 2, 3)]

    fake_pool = type("P", (), {"fetch": staticmethod(fake_fetch)})()
    with patch("utils.db.pool.get", return_value=fake_pool):
        result = asyncio.run(pc._collect_migrations())
    assert result.status == pc.SectionStatus.CLEAN


# ---------------------------------------------------------------------------
# Runtime providers collector (meta-health only)
# ---------------------------------------------------------------------------


def test_runtime_providers_marks_per_provider_error():
    with (
        patch(
            "services.diagnostics_service.registered_names",
            return_value=["a", "b"],
        ),
        patch(
            "services.diagnostics_service.snapshot_all",
            return_value={
                "a": {"ok": True},
                "b": {"_error": "RuntimeError: boom"},
            },
        ),
    ):
        result = asyncio.run(pc._collect_runtime_providers())
    assert result.status == pc.SectionStatus.WARNING
    assert "b" in " ".join(result.details)


def test_runtime_providers_clean_when_all_ok():
    with (
        patch(
            "services.diagnostics_service.registered_names",
            return_value=["a", "b"],
        ),
        patch(
            "services.diagnostics_service.snapshot_all",
            return_value={"a": {"ok": True}, "b": {"ok": True}},
        ),
    ):
        result = asyncio.run(pc._collect_runtime_providers())
    assert result.status == pc.SectionStatus.CLEAN


def test_runtime_providers_skipped_when_registry_empty():
    with (
        patch(
            "services.diagnostics_service.registered_names",
            return_value=[],
        ),
        patch(
            "services.diagnostics_service.snapshot_all",
            return_value={},
        ),
    ):
        result = asyncio.run(pc._collect_runtime_providers())
    assert result.status == pc.SectionStatus.SKIPPED


def test_runtime_providers_is_meta_only():
    """Clarification #3: this section reports counts + error names; it
    does NOT inspect provider contents (domain analysis is in the
    dedicated sections)."""
    src = Path(pc.__file__).read_text()
    start = src.index("async def _collect_runtime_providers")
    end = src.index("async def _collect_setup_readiness", start)
    body = src[start:end]
    # Must NOT reach into domain-specific keys.
    forbidden_terms = (
        "by_source",
        "by_binding_status",
        "by_flag_state",
        "calls_total",
        "validator_dispatch",
    )
    for term in forbidden_terms:
        assert term not in body, (
            f"Runtime providers collector must stay meta-only — found {term!r} "
            f"which suggests domain analysis."
        )


# ---------------------------------------------------------------------------
# Rollout / audit collector
# ---------------------------------------------------------------------------


def test_rollout_audit_skipped_when_table_absent():
    async def fake_fetchval(query, *args):
        return None  # to_regclass returns NULL when table missing

    fake_pool = type("P", (), {"fetchval": staticmethod(fake_fetchval)})()
    with patch("utils.db.pool.get", return_value=fake_pool):
        result = asyncio.run(pc._collect_rollout_audit())
    assert result.status == pc.SectionStatus.SKIPPED


def test_rollout_audit_clean_when_table_present():
    calls = {"n": 0}

    async def fake_fetchval(query, *args):
        calls["n"] += 1
        if "to_regclass" in query:
            return "feature_flag_audit"
        return 42  # count

    fake_pool = type("P", (), {"fetchval": staticmethod(fake_fetchval)})()
    with patch("utils.db.pool.get", return_value=fake_pool):
        result = asyncio.run(pc._collect_rollout_audit())
    assert result.status == pc.SectionStatus.CLEAN
    assert "42" in result.summary


# ---------------------------------------------------------------------------
# Participation collector
# ---------------------------------------------------------------------------


def test_participation_skipped_when_tables_absent():
    async def fake_fetchval(query, *args):
        return None

    fake_pool = type("P", (), {"fetchval": staticmethod(fake_fetchval)})()
    with patch("utils.db.pool.get", return_value=fake_pool):
        result = asyncio.run(pc._collect_participation())
    assert result.status == pc.SectionStatus.SKIPPED


# ---------------------------------------------------------------------------
# Setup readiness collector
# ---------------------------------------------------------------------------


def test_setup_readiness_lists_all_documented_blockers():
    result = asyncio.run(pc._collect_setup_readiness())
    # PR-03: status depends on how many blockers are resolved at the
    # moment the test runs; WARNING is the expected default since at
    # least one blocker is still pending in this codebase.
    assert result.status in (pc.SectionStatus.WARNING, pc.SectionStatus.CLEAN)
    assert result.informational is True
    # PR-03: details are now "<id>: <status>" pairs.  Every blocker ID
    # must still appear as a prefix in some detail line.
    detail_text = " ".join(result.details)
    for blocker in pc.SETUP_READINESS_BLOCKERS:
        assert (
            blocker in detail_text
        ), f"{blocker!r} missing from setup readiness section details"


def test_setup_readiness_marked_informational():
    result = asyncio.run(pc._collect_setup_readiness())
    assert result.informational is True


def test_setup_readiness_constant_is_nonempty_tuple():
    assert isinstance(pc.SETUP_READINESS_BLOCKERS, tuple)
    assert len(pc.SETUP_READINESS_BLOCKERS) > 0
    # Spot-check a few well-known blocker names.
    assert "command_surface_ledger" in pc.SETUP_READINESS_BLOCKERS
    assert "setup_wizard" in pc.SETUP_READINESS_BLOCKERS
    assert "panel_registry" in pc.SETUP_READINESS_BLOCKERS


# ---------------------------------------------------------------------------
# collect_report integration smoke
# ---------------------------------------------------------------------------


def test_collect_report_returns_twelve_sections_in_order():
    async def trivial(*args, **kwargs) -> pc.SectionResult:
        return pc.SectionResult(name="x", status=pc.SectionStatus.SKIPPED, summary="x")

    with patch.multiple(
        pc,
        _collect_identity_contract=trivial,
        _collect_feature_flags=trivial,
        _collect_rollout_audit=trivial,
        _collect_bindings=trivial,
        _collect_binding_backfill=trivial,
        _collect_config_arbitration=trivial,
        _collect_participation=trivial,
        _collect_migrations=trivial,
        _collect_runtime_providers=trivial,
        _collect_lifecycle=trivial,
        # Real setup-readiness + wizard-finalization collectors so we get
        # the informational tags on the last two sections.
    ):
        report = asyncio.run(pc.collect_report(bot=object(), guild=None))
    assert len(report.sections) == 12
    # Last section must be Wizard finalization, marked informational.
    assert report.sections[-1].name == "Wizard finalization"
    assert report.sections[-1].informational is True
    # Setup readiness is now second-to-last, also informational.
    assert report.sections[-2].name == "Setup readiness"
    assert report.sections[-2].informational is True


# ---------------------------------------------------------------------------
# PR-01a: typed readiness kind + iter_blocking_sections
# ---------------------------------------------------------------------------


def test_readiness_kinds_canonical_ordering():
    """``READINESS_KINDS`` pins the canonical section order.

    The diagnostic embed and the upcoming readiness snapshot rely on
    this ordering being stable; adding a new collector requires
    appending its kind and updating ``_LABEL_TO_KIND`` together.
    """
    assert pc.READINESS_KINDS == (
        pc.ReadinessKind.IDENTITY_CONTRACT,
        pc.ReadinessKind.FEATURE_FLAGS,
        pc.ReadinessKind.ROLLOUT_AUDIT,
        pc.ReadinessKind.BINDINGS,
        pc.ReadinessKind.BINDING_BACKFILL,
        pc.ReadinessKind.CONFIG_ARBITRATION,
        pc.ReadinessKind.PARTICIPATION,
        pc.ReadinessKind.MIGRATIONS,
        pc.ReadinessKind.RUNTIME_PROVIDERS,
        pc.ReadinessKind.LIFECYCLE,
        pc.ReadinessKind.SETUP_READINESS,
        pc.ReadinessKind.WIZARD_FINALIZATION,
    )
    # Every declared kind must appear in the canonical tuple.
    assert set(pc.READINESS_KINDS) == set(pc.ReadinessKind)


def test_collect_report_stamps_typed_kind_on_every_section():
    """Every section in the collected report has a non-None typed kind
    matching ``READINESS_KINDS``."""

    async def trivial(*args, **kwargs) -> pc.SectionResult:
        return pc.SectionResult(name="x", status=pc.SectionStatus.SKIPPED, summary="x")

    with patch.multiple(
        pc,
        _collect_identity_contract=trivial,
        _collect_feature_flags=trivial,
        _collect_rollout_audit=trivial,
        _collect_bindings=trivial,
        _collect_binding_backfill=trivial,
        _collect_config_arbitration=trivial,
        _collect_participation=trivial,
        _collect_migrations=trivial,
        _collect_runtime_providers=trivial,
        _collect_setup_readiness=trivial,
    ):
        report = asyncio.run(pc.collect_report(bot=object(), guild=None))

    kinds = [s.kind for s in report.sections]
    assert all(k is not None for k in kinds), f"Untyped section in {kinds}"
    assert tuple(kinds) == pc.READINESS_KINDS


def test_collect_report_stamps_kind_even_when_collector_raises():
    """A collector exception still produces a typed section."""

    async def bad(*args, **kwargs) -> pc.SectionResult:
        raise RuntimeError("boom")

    async def trivial(*args, **kwargs) -> pc.SectionResult:
        return pc.SectionResult(name="x", status=pc.SectionStatus.SKIPPED, summary="x")

    with patch.multiple(
        pc,
        _collect_identity_contract=bad,
        _collect_feature_flags=trivial,
        _collect_rollout_audit=trivial,
        _collect_bindings=trivial,
        _collect_binding_backfill=trivial,
        _collect_config_arbitration=trivial,
        _collect_participation=trivial,
        _collect_migrations=trivial,
        _collect_runtime_providers=trivial,
        _collect_setup_readiness=trivial,
    ):
        report = asyncio.run(pc.collect_report(bot=object(), guild=None))

    # The FATAL fallback section for identity_contract still gets stamped.
    assert report.sections[0].status == pc.SectionStatus.FATAL
    assert report.sections[0].kind == pc.ReadinessKind.IDENTITY_CONTRACT


def test_iter_blocking_sections_filters_informational_and_clean():
    """Non-informational FATAL/WARNING/SKIPPED are returned; CLEAN and
    informational sections are filtered out."""
    sections = (
        pc.SectionResult(name="a", status=pc.SectionStatus.CLEAN, summary=""),
        pc.SectionResult(name="b", status=pc.SectionStatus.WARNING, summary=""),
        pc.SectionResult(name="c", status=pc.SectionStatus.FATAL, summary=""),
        pc.SectionResult(name="d", status=pc.SectionStatus.SKIPPED, summary=""),
        # Informational warning must be excluded (Setup readiness pattern).
        pc.SectionResult(
            name="e", status=pc.SectionStatus.WARNING, summary="", informational=True
        ),
    )
    report = pc.ConsistencyReport(
        sections=sections,
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    blocking = pc.iter_blocking_sections(report)
    names = [s.name for s in blocking]
    assert names == ["b", "c", "d"]


def test_iter_blocking_sections_returns_empty_for_all_clean():
    report = _report(pc.SectionStatus.CLEAN, pc.SectionStatus.CLEAN)
    assert pc.iter_blocking_sections(report) == ()


def test_setup_readiness_section_remains_informational():
    """Regression pin: the Setup readiness collector must report
    ``informational=True`` so the static blocker list cannot promote
    ``overall_status``.  PR-03 (dynamic blocker registry) preserves
    this contract."""
    result = asyncio.run(pc._collect_setup_readiness())
    assert result.informational is True
    # Canonical section name matches the orchestrator's label mapping.
    assert result.name == "Setup readiness"


# ---------------------------------------------------------------------------
# PR-01b: readiness snapshot + diagnostics provider
# ---------------------------------------------------------------------------


@pytest.fixture
def _reset_pc_state():
    """Clear platform_consistency module state for snapshot tests."""
    from core.runtime import startup_outcome

    pc._LAST_REPORT = None
    startup_outcome.reset_for_tests()
    yield
    pc._LAST_REPORT = None
    startup_outcome.reset_for_tests()


def test_get_last_report_returns_none_before_first_collect(_reset_pc_state):
    assert pc.get_last_report() is None


def test_collect_report_populates_last_report_cache(_reset_pc_state):
    """The orchestrator caches the most recent report so the sync
    snapshot can read it without awaiting."""

    async def trivial(*args, **kwargs) -> pc.SectionResult:
        return pc.SectionResult(name="x", status=pc.SectionStatus.SKIPPED, summary="x")

    with patch.multiple(
        pc,
        _collect_identity_contract=trivial,
        _collect_feature_flags=trivial,
        _collect_rollout_audit=trivial,
        _collect_bindings=trivial,
        _collect_binding_backfill=trivial,
        _collect_config_arbitration=trivial,
        _collect_participation=trivial,
        _collect_migrations=trivial,
        _collect_runtime_providers=trivial,
        _collect_setup_readiness=trivial,
    ):
        report = asyncio.run(pc.collect_report(bot=object(), guild=None))

    cached = pc.get_last_report()
    assert cached is report


def test_build_readiness_snapshot_with_no_report_returns_none_overall(
    _reset_pc_state,
):
    snap = pc.build_readiness_snapshot()
    assert snap.consistency_overall_status is None
    assert snap.consistency_report_at is None
    assert snap.consistency_blocking_sections == ()
    assert snap.startup_outcomes == ()


def test_build_readiness_snapshot_after_collect_includes_status(
    _reset_pc_state,
):
    """A fresh collect_report populates the snapshot fields."""

    async def trivial(*args, **kwargs) -> pc.SectionResult:
        return pc.SectionResult(name="x", status=pc.SectionStatus.CLEAN, summary="x")

    with patch.multiple(
        pc,
        _collect_identity_contract=trivial,
        _collect_feature_flags=trivial,
        _collect_rollout_audit=trivial,
        _collect_bindings=trivial,
        _collect_binding_backfill=trivial,
        _collect_config_arbitration=trivial,
        _collect_participation=trivial,
        _collect_migrations=trivial,
        _collect_runtime_providers=trivial,
        _collect_setup_readiness=trivial,
    ):
        asyncio.run(pc.collect_report(bot=object(), guild=None))

    snap = pc.build_readiness_snapshot()
    assert snap.consistency_overall_status == pc.SectionStatus.CLEAN
    assert snap.consistency_report_at is not None
    assert snap.consistency_blocking_sections == ()


def test_build_readiness_snapshot_reflects_startup_outcomes(_reset_pc_state):
    from core.runtime import startup_outcome

    startup_outcome.record_success("command_surface_ledger")
    try:
        raise RuntimeError("missing")
    except RuntimeError as exc:
        startup_outcome.record_failure("settings_registry", exc)

    snap = pc.build_readiness_snapshot()
    names = {o.name: o for o in snap.startup_outcomes}
    assert names["command_surface_ledger"].success is True
    assert names["settings_registry"].success is False
    assert "RuntimeError" in names["settings_registry"].error


def test_readiness_snapshot_dict_view_for_diagnostics(_reset_pc_state):
    """The diagnostics provider dict view is JSON-serialisable shape."""
    snap_dict = pc._readiness_snapshot_dict()
    # Top-level keys.
    assert {"generated_at", "consistency", "startup", "catalogues", "tasks"} <= set(
        snap_dict.keys(),
    )
    # Nested catalogue booleans.
    assert "ledger_built" in snap_dict["catalogues"]
    # Tasks subsection always present.
    assert "active_count" in snap_dict["tasks"]


def test_readiness_provider_registered_in_diagnostics():
    """Sync diagnostics service contract preserved — no async provider."""
    from services import diagnostics_service

    assert "platform_readiness" in diagnostics_service.registered_names()
    # Calling it must return a dict synchronously (no coroutine).
    snap = diagnostics_service.snapshot("platform_readiness")
    assert isinstance(snap, dict)
