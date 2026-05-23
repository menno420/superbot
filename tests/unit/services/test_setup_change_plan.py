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
    """PR-04b: default flipped to on; explicit off-values opt out."""

    @pytest.mark.parametrize("val", ["1", "true", "TRUE", "yes", "on"])
    def test_truthy_values_enable(self, val: str):
        with patch.dict("os.environ", {"SETUP_PREFLIGHT_DIFF": val}):
            assert is_preflight_enabled() is True


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


# ---------------------------------------------------------------------------
# PR-04a (review fix) — normalized comparison via values_equivalent
# ---------------------------------------------------------------------------


from services.setup_change_plan import values_equivalent  # noqa: E402


class TestValuesEquivalent:
    """Pin the normalization table used by _preflight_set_setting.

    The DB stores settings as TEXT but operators stage them via the
    wizard as Python-typed values (bool, int, etc.).  Naive ``str()``
    comparison would either hide real type mismatches or surface false
    diffs; ``values_equivalent`` collapses common equivalent forms.
    """

    # ---- Equivalence cases (must be True) -------------------------------

    @pytest.mark.parametrize(
        ("current", "proposed"),
        [
            (None, None),
            ("", None),
            ("None", None),
            ("null", None),
            ("  ", None),
            (True, "true"),
            (True, "True"),
            (True, "1"),
            (True, "yes"),
            (True, "ON"),
            (False, "false"),
            (False, "0"),
            (False, "no"),
            (False, "off"),
            (1, "1"),
            (100, "100"),
            (0, "0"),
            ("abc", "ABC"),
            ("abc", " abc "),
        ],
    )
    def test_equivalent_pairs(self, current, proposed):
        assert values_equivalent(current, proposed) is True, (
            f"{current!r} should compare equal to {proposed!r}"
        )
        # Must be symmetric.
        assert values_equivalent(proposed, current) is True, (
            f"Equality must be symmetric: {proposed!r} vs {current!r}"
        )

    # ---- Type-sensitive mismatches (must be False) ----------------------

    @pytest.mark.parametrize(
        ("current", "proposed"),
        [
            # Note: "" → None is *intentionally equivalent* (the DB
            # layer stores unset values as the empty string for some
            # keys).  See test_equivalent_pairs above.
            (None, "abc"),
            (True, False),
            (True, "garbage"),
            (1, 2),
            (1, "2"),
            ("abc", "def"),
            (None, 0),  # None != 0 — different observable state
            (None, False),  # None != False — distinct unset vs unchecked
        ],
    )
    def test_type_sensitive_mismatches(self, current, proposed):
        assert values_equivalent(current, proposed) is False, (
            f"{current!r} must NOT compare equal to {proposed!r}"
        )


# ---------------------------------------------------------------------------
# PR-04a (review fix) — preflight set_setting normalized comparison
# ---------------------------------------------------------------------------


class TestPreflightSetSettingNormalized:
    """Integration: _preflight_set_setting consumes values_equivalent."""

    @pytest.mark.asyncio
    async def test_bool_true_vs_string_true_is_noop(self):
        op = SetupOperation(
            kind="set_setting",
            subsystem="logging",
            setting_name="enabled",
            value=True,
        )
        with patch("utils.db.get_setting", new=AsyncMock(return_value="true")):
            entries = await preflight_operations([op], guild=_guild())
        assert entries[0].would_change is False

    @pytest.mark.asyncio
    async def test_int_vs_string_int_is_noop(self):
        op = SetupOperation(
            kind="set_setting",
            subsystem="xp",
            setting_name="threshold",
            value=100,
        )
        with patch("utils.db.get_setting", new=AsyncMock(return_value="100")):
            entries = await preflight_operations([op], guild=_guild())
        assert entries[0].would_change is False

    @pytest.mark.asyncio
    async def test_empty_string_vs_none_is_noop(self):
        op = SetupOperation(
            kind="set_setting",
            subsystem="logging",
            setting_name="channel",
            value=None,
        )
        with patch("utils.db.get_setting", new=AsyncMock(return_value="")):
            entries = await preflight_operations([op], guild=_guild())
        assert entries[0].would_change is False

    @pytest.mark.asyncio
    async def test_real_type_change_still_detected(self):
        """``True`` → ``False`` (or string-equivalents) MUST surface."""
        op = SetupOperation(
            kind="set_setting",
            subsystem="logging",
            setting_name="enabled",
            value=False,
        )
        with patch("utils.db.get_setting", new=AsyncMock(return_value="true")):
            entries = await preflight_operations([op], guild=_guild())
        assert entries[0].would_change is True

    @pytest.mark.asyncio
    async def test_int_to_different_int_still_detected(self):
        op = SetupOperation(
            kind="set_setting",
            subsystem="xp",
            setting_name="threshold",
            value=200,
        )
        with patch("utils.db.get_setting", new=AsyncMock(return_value="100")):
            entries = await preflight_operations([op], guild=_guild())
        assert entries[0].would_change is True

    @pytest.mark.asyncio
    async def test_string_change_detected(self):
        op = SetupOperation(
            kind="set_setting",
            subsystem="logging",
            setting_name="prefix",
            value="warn",
        )
        with patch("utils.db.get_setting", new=AsyncMock(return_value="info")):
            entries = await preflight_operations([op], guild=_guild())
        assert entries[0].would_change is True

    @pytest.mark.asyncio
    async def test_missing_current_value_marks_change(self):
        """None current vs concrete proposed = change."""
        op = SetupOperation(
            kind="set_setting",
            subsystem="logging",
            setting_name="channel",
            value="123456",
        )
        with patch("utils.db.get_setting", new=AsyncMock(return_value=None)):
            entries = await preflight_operations([op], guild=_guild())
        assert entries[0].would_change is True

    @pytest.mark.asyncio
    async def test_multi_op_batch_evaluates_each_independently(self):
        """A no-op and a real change in the same batch render
        differently; the normalizer is per-entry."""
        noop = SetupOperation(
            kind="set_setting",
            subsystem="xp",
            setting_name="threshold",
            value=100,
        )
        change = SetupOperation(
            kind="set_setting",
            subsystem="logging",
            setting_name="enabled",
            value=False,
        )

        # Distinct return values for distinct settings; the side_effect
        # is invoked once per get_setting call.
        async def fake_get_setting(_gid, key):
            return {
                "xp.threshold": "100",
                "logging.enabled": "true",
            }[key]

        with patch("utils.db.get_setting", side_effect=fake_get_setting):
            entries = await preflight_operations([noop, change], guild=_guild())
        assert entries[0].would_change is False
        assert entries[1].would_change is True


# ---------------------------------------------------------------------------
# PR-04b — default-on + format_change_plan_lines
# ---------------------------------------------------------------------------


class TestPreflightDefaultOn:
    def test_default_when_env_unset_is_on(self):
        import os

        os.environ.pop("SETUP_PREFLIGHT_DIFF", None)
        assert is_preflight_enabled() is True

    @pytest.mark.parametrize("val", ["0", "false", "no", "off", "FALSE"])
    def test_explicit_off_disables(self, val: str):
        with patch.dict("os.environ", {"SETUP_PREFLIGHT_DIFF": val}):
            assert is_preflight_enabled() is False

    @pytest.mark.parametrize("val", ["", "1", "true", "garbage"])
    def test_truthy_or_unrecognised_values_remain_on(self, val: str):
        with patch.dict("os.environ", {"SETUP_PREFLIGHT_DIFF": val}):
            assert is_preflight_enabled() is True


class TestFormatChangePlanLines:
    def test_no_change_renders_check_mark(self):
        from services.setup_change_plan import format_change_plan_lines

        entry = ChangePlanEntry(
            op=SetupOperation(kind="set_setting", subsystem="xp"),
            label="set xp.threshold",
            current=ChangeValue(kind="value", value="100"),
            proposed=ChangeValue(kind="value", value="100"),
            would_change=False,
        )
        lines = format_change_plan_lines([entry])
        assert lines == ["✅ set xp.threshold · no change (current matches proposed)"]

    def test_changed_low_risk_renders_pencil(self):
        from services.setup_change_plan import format_change_plan_lines

        entry = ChangePlanEntry(
            op=SetupOperation(kind="set_setting", subsystem="xp"),
            label="set xp.threshold",
            current=ChangeValue(kind="value", value="100"),
            proposed=ChangeValue(kind="value", value="200"),
            would_change=True,
            risk="low",
        )
        lines = format_change_plan_lines([entry])
        assert lines[0].startswith("✏")
        assert "current='100' → '200'" in lines[0]
        assert "[risk=low]" in lines[0]

    def test_high_risk_renders_warning(self):
        from services.setup_change_plan import format_change_plan_lines

        entry = ChangePlanEntry(
            op=SetupOperation(kind="set_setting", subsystem="xp"),
            label="set xp.threshold",
            current=ChangeValue(kind="value", value="100"),
            proposed=ChangeValue(kind="value", value="200"),
            would_change=True,
            risk="high",
        )
        lines = format_change_plan_lines([entry])
        assert lines[0].startswith("⚠")
        assert "[risk=high]" in lines[0]

    def test_read_error_rendered_first(self):
        from services.setup_change_plan import format_change_plan_lines

        entry = ChangePlanEntry(
            op=SetupOperation(kind="set_setting", subsystem="xp"),
            label="set xp.threshold",
            current=UNKNOWN,
            proposed=ChangeValue(kind="value", value="200"),
            would_change=True,
            read_error="RuntimeError: db down",
        )
        lines = format_change_plan_lines([entry])
        assert lines == ["⚠ set xp.threshold · read error: RuntimeError: db down"]

    def test_no_adapter_rendered_first(self):
        from services.setup_change_plan import format_change_plan_lines

        entry = ChangePlanEntry(
            op=SetupOperation(kind="create_channel", subsystem="logging"),
            label="create channel #mod-log",
            current=ABSENT,
            proposed=ChangeValue(kind="value", value="mod-log"),
            would_change=True,
            preflight_skipped_reason="no_adapter",
        )
        lines = format_change_plan_lines([entry])
        assert lines == [
            "⚠ create channel #mod-log · preflight unavailable (no_adapter)",
        ]

    def test_max_lines_truncates(self):
        from services.setup_change_plan import format_change_plan_lines

        entries = [
            ChangePlanEntry(
                op=SetupOperation(kind="set_setting", subsystem="xp"),
                label=f"line {i}",
                current=ChangeValue(kind="value", value="a"),
                proposed=ChangeValue(kind="value", value="b"),
                would_change=True,
            )
            for i in range(20)
        ]
        lines = format_change_plan_lines(entries, max_lines=3)
        assert len(lines) == 3
