"""Security tiers 1+2 (Q-0111) — config read model + threshold clamping.

Pins the frozen :class:`SecurityPolicy` predicates and the guardrail clamping in
:func:`services.security_config.load_policy` (a fat-fingered/hostile setting can
never produce an absurd detector). Resolution is stubbed so the test owns inputs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import security_config  # noqa: E402


def _policy(**over: object) -> security_config.SecurityPolicy:
    return security_config.SecurityPolicy(**over)  # type: ignore[arg-type]


# --- predicates ---------------------------------------------------------------


def test_master_switch_gates_every_tier():
    p = _policy(enabled=False, raid_enabled=True, age_enabled=True)
    assert not p.raid_detection_on
    assert not p.age_filter_on
    assert not p.any_tier_enabled


def test_tier_flags_gate_individually():
    p = _policy(enabled=True, raid_enabled=True, age_enabled=False)
    assert p.raid_detection_on
    assert not p.age_filter_on
    assert p.any_tier_enabled


def test_applies_raid_slowmode_needs_channel_and_seconds():
    assert not _policy(
        raid_slowmode_channel_id=None, raid_slowmode_seconds=10
    ).applies_raid_slowmode
    assert not _policy(
        raid_slowmode_channel_id=5, raid_slowmode_seconds=0
    ).applies_raid_slowmode
    assert _policy(
        raid_slowmode_channel_id=5, raid_slowmode_seconds=10
    ).applies_raid_slowmode


def test_parse_id_is_tolerant():
    assert security_config.parse_id("123") == 123
    assert security_config.parse_id("") is None
    assert security_config.parse_id("  ") is None
    assert security_config.parse_id("not-an-id") is None
    assert security_config.parse_id(None) is None


# --- load_policy clamping + coercion -----------------------------------------


@pytest.mark.asyncio
async def test_load_policy_clamps_and_coerces(monkeypatch):
    # Hostile/garbage stored values: out-of-range ints, a bad action, junk id.
    stored = {
        "enabled": True,
        "raid_enabled": True,
        "raid_join_count": 99999,  # over MAX -> clamped to 100
        "raid_window_seconds": 1,  # under MIN -> clamped to 5
        "raid_slowmode_seconds": "garbage",  # non-int -> default
        "raid_lockdown_seconds": -5,  # under 0 -> clamped to 0
        "raid_slowmode_channel": "777",
        "age_enabled": True,
        "age_min_days": 100000,  # over MAX -> clamped to 365
        "age_action": "NUKE",  # invalid -> default alert
        "alert_channel": "888",
    }

    async def _resolve(_gid, _sub, name, default):
        return stored.get(name, default)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", _resolve)

    p = await security_config.load_policy(123)
    assert p.raid_join_count == security_config.MAX_RAID_JOIN_COUNT
    assert p.raid_window_seconds == security_config.MIN_RAID_WINDOW_SECONDS
    assert p.raid_slowmode_seconds == security_config.DEFAULT_RAID_SLOWMODE_SECONDS
    assert p.raid_lockdown_seconds == 0
    assert p.raid_slowmode_channel_id == 777
    assert p.age_min_days == security_config.MAX_AGE_DAYS
    assert p.age_action == security_config.DEFAULT_AGE_ACTION
    assert p.alert_channel_id == 888


@pytest.mark.asyncio
async def test_load_policy_defaults_off(monkeypatch):
    async def _resolve(_gid, _sub, _name, default):
        return default

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", _resolve)
    p = await security_config.load_policy(1)
    assert not p.enabled and not p.any_tier_enabled
