"""Security tiers 1+2 (Q-0111) — detection layer + join orchestration.

The pure detectors (RaidTracker window, account-age) are tested directly; the
fail-open orchestration is tested with a stubbed policy + mocked Discord/alert/
kick so no real I/O happens.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import security_config, security_service  # noqa: E402


@pytest.fixture(autouse=True)
def _reset():
    security_service.reset_state()
    yield
    security_service.reset_state()


# --- RaidTracker (pure) -------------------------------------------------------


def test_raid_tracker_counts_within_window():
    t = security_service.RaidTracker()
    # 5 joins at t=0..4 within a 10s window -> count rises to 5.
    counts = [t.record_and_count(1, window_seconds=10, now=float(i)) for i in range(5)]
    assert counts == [1, 2, 3, 4, 5]


def test_raid_tracker_evicts_outside_window():
    t = security_service.RaidTracker()
    t.record_and_count(1, window_seconds=10, now=0.0)
    t.record_and_count(1, window_seconds=10, now=5.0)
    # A join at t=100 is far outside the window — only it remains.
    assert t.record_and_count(1, window_seconds=10, now=100.0) == 1


def test_raid_tracker_is_per_guild():
    t = security_service.RaidTracker()
    t.record_and_count(1, window_seconds=10, now=0.0)
    assert t.record_and_count(2, window_seconds=10, now=0.0) == 1


# --- account age (pure) -------------------------------------------------------


def _member(created_at):
    return SimpleNamespace(created_at=created_at, id=99, guild=SimpleNamespace(id=1))


def test_account_age_days_and_young_check():
    now = datetime(2026, 1, 31, tzinfo=timezone.utc)
    young = _member(now - timedelta(days=2))
    old = _member(now - timedelta(days=400))
    assert security_service.account_age_days(young, now=now) == pytest.approx(2.0)
    assert security_service.is_young_account(young, min_days=7, now=now)
    assert not security_service.is_young_account(old, min_days=7, now=now)


def test_account_age_unknown_timestamp_is_not_young():
    assert security_service.account_age_days(_member(None)) is None
    assert not security_service.is_young_account(_member(None), min_days=7)


# --- orchestration ------------------------------------------------------------


def _make_member(*, age_days: float = 100.0, guild_id: int = 1):
    created = datetime.now(timezone.utc) - timedelta(days=age_days)
    guild = SimpleNamespace(id=guild_id)
    return SimpleNamespace(id=42, bot=False, guild=guild, created_at=created)


def _patch_policy(monkeypatch, policy):
    async def _load(_gid):
        return policy

    monkeypatch.setattr(security_config, "load_policy", _load)


@pytest.mark.asyncio
async def test_disabled_master_is_a_noop(monkeypatch):
    _patch_policy(monkeypatch, security_config.SecurityPolicy(enabled=False))
    alert = AsyncMock()
    monkeypatch.setattr(security_service, "_post_alert", alert)
    result = await security_service.handle_member_join(_make_member())
    assert not result.raid_triggered and not result.account_flagged
    alert.assert_not_awaited()


@pytest.mark.asyncio
async def test_raid_triggers_alert_once_then_dedupes(monkeypatch):
    policy = security_config.SecurityPolicy(
        enabled=True,
        raid_enabled=True,
        raid_join_count=3,
        raid_window_seconds=600,
        raid_slowmode_seconds=0,  # alert-only, no slowmode channel
        alert_channel_id=555,
    )
    _patch_policy(monkeypatch, policy)
    alert = AsyncMock()
    emit = AsyncMock()
    monkeypatch.setattr(security_service, "_post_alert", alert)
    monkeypatch.setattr(security_service, "_emit", emit)

    triggered = []
    for _ in range(5):
        r = await security_service.handle_member_join(_make_member())
        triggered.append(r.raid_triggered)

    # Threshold 3 → first trigger on the 3rd join; subsequent joins dedupe
    # (guild already locked) so only ONE alert fires.
    assert triggered == [False, False, True, False, False]
    assert alert.await_count == 1


@pytest.mark.asyncio
async def test_raid_lock_clears_so_a_later_distinct_raid_realerts(monkeypatch):
    # Alert-only (the default) has no slowmode to carry the lock-clear. Regression
    # for the bug where the guild stayed in _locked_guilds for the life of the
    # process, silently suppressing every subsequent raid until a restart.
    policy = security_config.SecurityPolicy(
        enabled=True,
        raid_enabled=True,
        raid_join_count=3,
        raid_window_seconds=600,
        raid_slowmode_seconds=0,  # alert-only, no slowmode channel
        alert_channel_id=555,
    )
    _patch_policy(monkeypatch, policy)
    alert = AsyncMock()
    monkeypatch.setattr(security_service, "_post_alert", alert)
    monkeypatch.setattr(security_service, "_emit", AsyncMock())

    # Capture the scheduled clear instead of sleeping out the real raid window.
    scheduled: list[tuple[int, float]] = []

    async def _fake_clear(guild_id, delay):
        scheduled.append((guild_id, delay))

    monkeypatch.setattr(security_service, "_clear_lock_after", _fake_clear)

    for _ in range(3):
        await security_service.handle_member_join(_make_member())
    await asyncio.sleep(0)  # let the fire-and-forget clear task run

    # First raid alerted once and scheduled a clear for the raid window.
    assert alert.await_count == 1
    assert scheduled == [(1, 600.0)]

    # Simulate the window expiring (the scheduled clear firing).
    security_service._locked_guilds.discard(1)

    # A second, distinct raid must re-alert — previously suppressed until restart.
    for _ in range(3):
        await security_service.handle_member_join(_make_member())
    assert alert.await_count == 2


@pytest.mark.asyncio
async def test_young_account_alert_only_does_not_kick(monkeypatch):
    policy = security_config.SecurityPolicy(
        enabled=True,
        age_enabled=True,
        age_min_days=7,
        age_action=security_config.ACTION_ALERT,
        alert_channel_id=555,
    )
    _patch_policy(monkeypatch, policy)
    monkeypatch.setattr(security_service, "_post_alert", AsyncMock())
    monkeypatch.setattr(security_service, "_emit", AsyncMock())

    import services.moderation_service as mod

    kick = AsyncMock()
    monkeypatch.setattr(mod, "kick", kick)

    result = await security_service.handle_member_join(_make_member(age_days=2))
    assert result.account_flagged
    assert result.age_action_taken == "alert"
    kick.assert_not_awaited()


@pytest.mark.asyncio
async def test_young_account_kick_action_routes_through_moderation(monkeypatch):
    policy = security_config.SecurityPolicy(
        enabled=True,
        age_enabled=True,
        age_min_days=7,
        age_action=security_config.ACTION_KICK,
        alert_channel_id=555,
    )
    _patch_policy(monkeypatch, policy)
    monkeypatch.setattr(security_service, "_post_alert", AsyncMock())
    monkeypatch.setattr(security_service, "_emit", AsyncMock())

    import services.moderation_service as mod

    kick = AsyncMock()
    monkeypatch.setattr(mod, "kick", kick)

    result = await security_service.handle_member_join(_make_member(age_days=1))
    assert result.account_flagged and result.age_action_taken == "kick"
    kick.assert_awaited_once()


@pytest.mark.asyncio
async def test_old_account_is_not_flagged(monkeypatch):
    policy = security_config.SecurityPolicy(
        enabled=True, age_enabled=True, age_min_days=7, alert_channel_id=555
    )
    _patch_policy(monkeypatch, policy)
    alert = AsyncMock()
    monkeypatch.setattr(security_service, "_post_alert", alert)
    monkeypatch.setattr(security_service, "_emit", AsyncMock())
    result = await security_service.handle_member_join(_make_member(age_days=365))
    assert not result.account_flagged
    alert.assert_not_awaited()


@pytest.mark.asyncio
async def test_config_fault_fails_open(monkeypatch):
    async def _boom(_gid):
        raise RuntimeError("db down")

    monkeypatch.setattr(security_config, "load_policy", _boom)
    # Must not raise — a config fault swallows and returns an empty result.
    result = await security_service.handle_member_join(_make_member())
    assert not result.raid_triggered and not result.account_flagged
