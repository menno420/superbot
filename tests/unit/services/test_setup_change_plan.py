"""Unit tests for services.setup_change_plan + preflight_operations — PR-04a."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.setup_change_plan import (
    ABSENT,
    UNKNOWN,
    ChangePlanEntry,
    ChangeValue,
)
from services.setup_operations import (
    SetupOperation,
    is_preflight_enabled,
    preflight_operations,
)

# ---------------------------------------------------------------------------
# ChangeValue / sentinels
# ---------------------------------------------------------------------------


class TestChangeValue:
    def test_value_kind_default(self):
        cv = ChangeValue(kind="value", value=42)
        assert cv.kind == "value"
        assert cv.value == 42
        assert repr(cv) == "42"

    def test_absent_singleton_repr(self):
        assert ABSENT.kind == "absent"
        assert "ABSENT" in repr(ABSENT)

    def test_unknown_singleton_repr(self):
        assert UNKNOWN.kind == "unknown"
        assert "UNKNOWN" in repr(UNKNOWN)

    def test_default_kind_is_value(self):
        cv = ChangeValue()
        assert cv.kind == "value"
        assert cv.value is None


# ---------------------------------------------------------------------------
# Feature flag toggle
# ---------------------------------------------------------------------------


class TestPreflightFlag:
    def test_disabled_by_default(self):
        with patch.dict("os.environ", {}, clear=False):
            # Ensure the env var is not set in this test.
            import os

            os.environ.pop("SETUP_PREFLIGHT_DIFF", None)
            assert is_preflight_enabled() is False

    @pytest.mark.parametrize("val", ["1", "true", "TRUE", "yes", "on"])
    def test_truthy_values_enable(self, val: str):
        with patch.dict("os.environ", {"SETUP_PREFLIGHT_DIFF": val}):
            assert is_preflight_enabled() is True

    @pytest.mark.parametrize("val", ["", "0", "no", "off", "garbage"])
    def test_other_values_keep_disabled(self, val: str):
        with patch.dict("os.environ", {"SETUP_PREFLIGHT_DIFF": val}):
            assert is_preflight_enabled() is False


# ---------------------------------------------------------------------------
# preflight_operations — per-op-kind diff coverage
# ---------------------------------------------------------------------------


def _guild(gid: int = 100) -> SimpleNamespace:
    return SimpleNamespace(id=gid)


@pytest.mark.asyncio
async def test_preflight_bind_channel_existing_match_no_change():
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=42,
        target_kind="channel",
    )
    fake_row = {"target_id": 42, "status": "bound", "kind": "channel"}
    with patch(
        "utils.db.bindings.get_one",
        new=AsyncMock(return_value=fake_row),
    ):
        entries = await preflight_operations([op], guild=_guild())
    assert len(entries) == 1
    e = entries[0]
    assert e.current.kind == "value"
    assert e.current.value == 42
    assert e.proposed.value == 42
    assert e.would_change is False
    assert e.read_error is None


@pytest.mark.asyncio
async def test_preflight_bind_channel_existing_different_target_changes():
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=99,
        target_kind="channel",
    )
    fake_row = {"target_id": 42, "status": "bound", "kind": "channel"}
    with patch(
        "utils.db.bindings.get_one",
        new=AsyncMock(return_value=fake_row),
    ):
        entries = await preflight_operations([op], guild=_guild())
    assert entries[0].would_change is True
    assert entries[0].current.value == 42
    assert entries[0].proposed.value == 99


@pytest.mark.asyncio
async def test_preflight_bind_channel_absent_current_marks_change():
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=99,
    )
    with patch(
        "utils.db.bindings.get_one",
        new=AsyncMock(return_value=None),
    ):
        entries = await preflight_operations([op], guild=_guild())
    assert entries[0].current.kind == "absent"
    assert entries[0].would_change is True


@pytest.mark.asyncio
async def test_preflight_bind_read_error_isolated_to_entry():
    """A raising adapter populates read_error; the batch continues."""
    op_bad = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=1,
    )
    op_good = SetupOperation(
        kind="bind_role",
        subsystem="logging",
        binding_name="mod_role",
        target_id=2,
    )
    call_count = {"n": 0}

    async def flaky(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("db down")
        return None

    with patch("utils.db.bindings.get_one", side_effect=flaky):
        entries = await preflight_operations([op_bad, op_good], guild=_guild())
    assert len(entries) == 2
    assert entries[0].read_error is not None
    assert "RuntimeError" in entries[0].read_error
    assert entries[1].read_error is None


@pytest.mark.asyncio
async def test_preflight_clear_binding_existing_row_changes():
    op = SetupOperation(
        kind="clear_binding",
        subsystem="logging",
        binding_name="mod_channel",
    )
    fake_row = {"target_id": 42, "status": "bound", "kind": "channel"}
    with patch(
        "utils.db.bindings.get_one",
        new=AsyncMock(return_value=fake_row),
    ):
        entries = await preflight_operations([op], guild=_guild())
    e = entries[0]
    assert e.current.value == 42
    assert e.proposed.kind == "absent"
    assert e.would_change is True


@pytest.mark.asyncio
async def test_preflight_clear_binding_absent_row_is_noop():
    op = SetupOperation(
        kind="clear_binding",
        subsystem="logging",
        binding_name="mod_channel",
    )
    with patch(
        "utils.db.bindings.get_one",
        new=AsyncMock(return_value=None),
    ):
        entries = await preflight_operations([op], guild=_guild())
    assert entries[0].current.kind == "absent"
    assert entries[0].proposed.kind == "absent"
    assert entries[0].would_change is False


@pytest.mark.asyncio
async def test_preflight_set_setting_equal_value_is_noop():
    op = SetupOperation(
        kind="set_setting",
        subsystem="xp",
        setting_name="threshold",
        value="100",
    )
    with patch(
        "utils.db.get_setting",
        new=AsyncMock(return_value="100"),
    ):
        entries = await preflight_operations([op], guild=_guild())
    assert entries[0].current.value == "100"
    assert entries[0].would_change is False


@pytest.mark.asyncio
async def test_preflight_set_setting_different_value_changes():
    op = SetupOperation(
        kind="set_setting",
        subsystem="xp",
        setting_name="threshold",
        value="200",
    )
    with patch(
        "utils.db.get_setting",
        new=AsyncMock(return_value="100"),
    ):
        entries = await preflight_operations([op], guild=_guild())
    assert entries[0].would_change is True


@pytest.mark.asyncio
async def test_preflight_set_cog_routing_equal_is_noop():
    op = SetupOperation(
        kind="set_cog_routing",
        subsystem="economy",
        target_id=12345,
        value=True,
    )
    with patch(
        "services.command_routing.is_cog_enabled",
        new=AsyncMock(return_value=True),
    ):
        entries = await preflight_operations([op], guild=_guild())
    assert entries[0].would_change is False


@pytest.mark.asyncio
async def test_preflight_unknown_kind_marks_no_adapter():
    op = SetupOperation(kind="bogus_kind", subsystem="logging")
    entries = await preflight_operations([op], guild=_guild())
    assert entries[0].preflight_skipped_reason == "unknown_op_kind"


@pytest.mark.asyncio
async def test_preflight_create_channel_marks_no_adapter():
    op = SetupOperation(
        kind="create_channel",
        subsystem="logging",
        resource_name="mod-log",
    )
    entries = await preflight_operations([op], guild=_guild())
    assert entries[0].preflight_skipped_reason == "no_adapter"
    assert entries[0].current.kind == "absent"


@pytest.mark.asyncio
async def test_preflight_propagates_risk_and_rollback_metadata():
    op = SetupOperation(
        kind="set_setting",
        subsystem="xp",
        setting_name="threshold",
        value="100",
        metadata={
            "risk": "high",
            "rollback_note": "revert to legacy default",
        },
    )
    with patch("utils.db.get_setting", new=AsyncMock(return_value="100")):
        entries = await preflight_operations([op], guild=_guild())
    assert entries[0].risk == "high"
    assert entries[0].rollback_note == "revert to legacy default"


@pytest.mark.asyncio
async def test_preflight_entry_carries_op_back():
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=1,
    )
    with patch("utils.db.bindings.get_one", new=AsyncMock(return_value=None)):
        entries = await preflight_operations([op], guild=_guild())
    assert entries[0].op is op
    assert entries[0].label  # non-empty
