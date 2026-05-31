"""Config-arbitration fallback attribution — setup-wizard PR1.

Pins the redacted, bounded, per-key attribution that lets
``!platform consistency`` name *which* config key degraded to legacy
instead of only showing a count.

Privacy contract (docs/setup_wizard_finalization_plan.md §D6): only
stable internal identifiers are stored — never resolved values or
display names.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from core.resources.status import ResourceStatus
from core.runtime import config_arbitration
from core.runtime.bindings import BindingValue
from core.runtime.config_arbitration import (
    ConfigReadResult,
    attribution_snapshot,
    read_config,
)
from core.runtime.subsystem_schema import BindingKind

# Exactly the fields the snapshot is allowed to expose — no value, no names.
_ALLOWED_KEYS = {
    "guild_id",
    "subsystem",
    "binding_name",
    "legacy_key",
    "source",
    "flag_state",
    "binding_status",
    "recorded_at",
}


@pytest.fixture(autouse=True)
def _reset():
    config_arbitration._reset_counters_for_tests()
    yield
    config_arbitration._reset_counters_for_tests()


def _bv(*, target_id: int | None, status: ResourceStatus) -> BindingValue:
    return BindingValue(
        guild_id=1,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
        target_id=target_id,
        status=status,
        last_validated_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        version=1,
    )


# ---------------------------------------------------------------------------
# What gets recorded (via the real read_config path)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_is_recorded_with_redacted_fields():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=None, status=ResourceStatus.MISSING),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="123456789",
        ),
    ):
        await read_config(
            guild_id=42,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    snap = attribution_snapshot()
    assert len(snap) == 1
    entry = snap[0]
    assert entry["subsystem"] == "xp"
    assert entry["binding_name"] == "announce_channel"
    assert entry["legacy_key"] == "xp_announce_channel"
    assert entry["source"] == "fallback"
    assert entry["flag_state"] == "on"
    assert entry["binding_status"] == "missing"
    # Privacy: only the allowed identifier keys, and never the value.
    assert set(entry) == _ALLOWED_KEYS
    assert "123456789" not in entry.values()


@pytest.mark.asyncio
async def test_missing_under_flag_on_is_recorded():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=None, status=ResourceStatus.UNRESOLVED),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="",
        ),
    ):
        await read_config(
            guild_id=7,
            subsystem="economy",
            binding_name="log_channel",
            legacy_key="economy_log_channel",
        )
    snap = attribution_snapshot()
    assert len(snap) == 1
    assert snap[0]["source"] == "missing"
    assert snap[0]["flag_state"] == "on"


# ---------------------------------------------------------------------------
# What is NOT recorded (clean reads / ordinary unconfigured legacy)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_legacy_clean_is_not_recorded():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="123",
        ),
    ):
        await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert attribution_snapshot() == []


@pytest.mark.asyncio
async def test_binding_clean_is_not_recorded():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=999, status=ResourceStatus.BOUND),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
        ),
    ):
        await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert attribution_snapshot() == []


@pytest.mark.asyncio
async def test_missing_under_flag_off_is_not_recorded():
    """Flag OFF + empty legacy is an ordinary unconfigured optional setting,
    not a migration degradation — it must not flood the attribution map."""
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="",
        ),
    ):
        await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert attribution_snapshot() == []


# ---------------------------------------------------------------------------
# Cardinality: dedup per (guild, subsystem, binding) + hard cap
# ---------------------------------------------------------------------------


def _record(guild_id: int, subsystem: str, binding_name: str) -> None:
    """Record a synthetic fallback directly (fast, deterministic)."""
    config_arbitration._record_attribution(
        ConfigReadResult(
            value="x",
            source="fallback",
            binding_status="missing",
            flag_state="on",
            diagnostics=[],
        ),
        guild_id,
        subsystem,
        binding_name,
        "legacy_key",
    )


def test_repeated_reads_of_same_key_dedup_to_one_entry():
    for _ in range(50):
        _record(1, "xp", "announce_channel")
    assert len(attribution_snapshot(limit=1000)) == 1


def test_distinct_keys_are_separate_entries():
    _record(1, "xp", "announce_channel")
    _record(1, "economy", "log_channel")
    _record(2, "xp", "announce_channel")
    assert len(attribution_snapshot(limit=1000)) == 3


def test_map_is_hard_capped():
    cap = config_arbitration._ATTRIBUTION_MAX
    for i in range(cap + 25):
        _record(i, "xp", "announce_channel")
    # Never grows past the cap, regardless of how many distinct keys arrive.
    assert len(config_arbitration._FALLBACK_ATTRIBUTION) == cap


def test_snapshot_limit_is_respected():
    for i in range(10):
        _record(i, "xp", "announce_channel")
    assert len(attribution_snapshot(limit=3)) == 3


def test_reset_clears_attribution():
    _record(1, "xp", "announce_channel")
    assert attribution_snapshot() != []
    config_arbitration._reset_counters_for_tests()
    assert attribution_snapshot() == []
