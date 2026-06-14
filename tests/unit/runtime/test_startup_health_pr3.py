"""Tests for PR3 — startup health integration (bot awareness).

Covers the sibling extension-load recorder, the ``extensions`` health
subsystem (incl. the required-cog CRITICAL rule), the settled-startup
snapshot cache + embed, and — the key reconnect-safety property — that the
post-ready startup-health report is spawned exactly once per process even
when ``on_ready`` re-fires on a gateway reconnect.
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot1
from cogs.diagnostic._platform_embeds import build_startup_health_embed
from core.runtime import startup_outcome
from services import health_snapshot_service as hss
from services.health_contracts import (
    HealthAudience,
    HealthSnapshot,
    SnapshotStatus,
)


@pytest.fixture(autouse=True)
def _reset():
    startup_outcome.reset_for_tests()
    yield
    startup_outcome.reset_for_tests()


def _make_snapshot(status: SnapshotStatus = SnapshotStatus.HEALTHY) -> HealthSnapshot:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    return HealthSnapshot(
        snapshot_id="startupxx",
        generated_at=now,
        purpose="startup",
        status=status,
        summary="settled",
        subsystems=(),
        findings=(),
        redaction_audience=HealthAudience.PLATFORM_OWNER,
    )


# --- extension-load recorder ----------------------------------------------


def test_extension_recorder_records_success_and_failure() -> None:
    startup_outcome.record_extension_success("cogs.a")
    startup_outcome.record_extension_failure("cogs.b", RuntimeError("boom"))
    outcomes = startup_outcome.all_extension_outcomes()
    assert [o.name for o in outcomes] == ["cogs.a", "cogs.b"]  # sorted by name
    a = next(o for o in outcomes if o.name == "cogs.a")
    b = next(o for o in outcomes if o.name == "cogs.b")
    assert a.success and a.error is None
    assert not b.success and "RuntimeError" in (b.error or "")


def test_reset_clears_extension_outcomes() -> None:
    startup_outcome.record_extension_success("cogs.a")
    startup_outcome.reset_for_tests()
    assert startup_outcome.all_extension_outcomes() == ()


def test_extension_recorder_does_not_touch_known_phases() -> None:
    """The sibling recorder must not leak into the catalogue-phase ledger."""
    startup_outcome.record_extension_success("cogs.a")
    assert startup_outcome.all_outcomes() == ()  # KNOWN_PHASES untouched


# --- extensions health subsystem ------------------------------------------


def test_extensions_subsystem_unknown_when_unrecorded() -> None:
    sub = hss._extensions_subsystem()
    assert sub.name == "extensions"
    assert sub.status is SnapshotStatus.UNKNOWN
    assert sub.required is True


def test_extensions_subsystem_healthy_when_all_loaded() -> None:
    startup_outcome.record_extension_success("cogs.a")
    startup_outcome.record_extension_success("cogs.b")
    sub = hss._extensions_subsystem()
    assert sub.status is SnapshotStatus.HEALTHY
    assert sub.facts["loaded"] == 2
    assert sub.facts["failed"] == 0


def test_extensions_subsystem_degraded_on_optional_failure() -> None:
    startup_outcome.record_extension_success("cogs.a")
    startup_outcome.record_extension_failure("cogs.btd6_cog", RuntimeError("x"))
    sub = hss._extensions_subsystem()
    assert sub.status is SnapshotStatus.DEGRADED
    assert any(f.category == "extension.load_failed" for f in sub.findings)


def test_extensions_subsystem_critical_on_required_failure() -> None:
    startup_outcome.record_extension_failure(
        "cogs.bootstrap_access_cog", RuntimeError("x")
    )
    sub = hss._extensions_subsystem()
    assert sub.status is SnapshotStatus.CRITICAL


# --- settled-startup snapshot cache + embed --------------------------------


def test_startup_snapshot_cache_roundtrip() -> None:
    snap = _make_snapshot()
    hss.record_startup_snapshot(snap)
    assert hss.get_last_startup_snapshot() is snap


def test_build_startup_health_embed() -> None:
    embed = build_startup_health_embed(_make_snapshot(SnapshotStatus.DEGRADED))
    assert embed.title == "🚀 Startup health"
    assert "settled-startup" in (embed.footer.text or "")


# --- bot1 wiring -----------------------------------------------------------


def test_startup_health_reported_once_across_reconnect(monkeypatch) -> None:
    """on_ready re-firing on reconnect must not re-spawn the report."""
    monkeypatch.setattr(bot1, "_startup_health_reported", False)
    spawned: list[str] = []

    def _fake_spawn(name, coro, **_kw):
        spawned.append(name)
        coro.close()  # we never run it; avoid 'coroutine never awaited'
        return MagicMock()

    monkeypatch.setattr(bot1._runtime_tasks, "spawn", _fake_spawn)

    bot1._maybe_report_startup_health()
    bot1._maybe_report_startup_health()  # simulated gateway reconnect
    bot1._maybe_report_startup_health()

    assert spawned == ["startup:health_report"]


async def test_report_startup_health_caches_snapshot(monkeypatch) -> None:
    snap = _make_snapshot()
    monkeypatch.setattr(hss, "collect_snapshot", AsyncMock(return_value=snap))
    await bot1._report_startup_health()
    assert hss.get_last_startup_snapshot() is snap


async def test_report_startup_health_requests_fresh_consistency(monkeypatch) -> None:
    """Regression: the once-per-process startup report must collect a *fresh*
    consistency report, not the process-local cache.

    The cache (``platform_consistency._LAST_REPORT``) is only ever populated by
    ``collect_report`` (the ``!platform consistency`` command / platform panel),
    never at boot — so reading it at startup yields a required ``UNKNOWN``
    consistency subsystem, which dragged every fresh-boot snapshot to
    ``degraded`` with an empty attention list (a false alarm). Requesting fresh
    consistency fixes that and primes the cache.
    """
    captured: list = []

    async def _capture(request, *, bot=None):  # noqa: ANN001
        captured.append(request)
        return _make_snapshot()

    monkeypatch.setattr(hss, "collect_snapshot", _capture)
    await bot1._report_startup_health()
    assert len(captured) == 1
    assert captured[0].purpose == "startup"
    assert captured[0].include_fresh_consistency is True


async def test_report_startup_health_swallows_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        hss, "collect_snapshot", AsyncMock(side_effect=RuntimeError("down"))
    )
    # Must not raise — startup reporting can never break the running bot.
    await bot1._report_startup_health()
