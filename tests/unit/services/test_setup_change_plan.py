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
            # Word-like bool tokens → bool.
            (True, "true"),
            (True, "True"),
            (True, "yes"),
            (True, "ON"),
            (False, "false"),
            (False, "no"),
            (False, "off"),
            # Numeric strings → int.  ``"0"``/``"1"`` are intentionally
            # parsed as int (not bool) so they collapse with int 0/1
            # rather than bool False/True — see
            # ``test_strict_bool_int_separation`` below for the
            # rationale (operator-safe correctness over convenience).
            (1, "1"),
            (100, "100"),
            (0, "0"),
            ("abc", "ABC"),
            ("abc", " abc "),
        ],
    )
    def test_equivalent_pairs(self, current, proposed):
        assert (
            values_equivalent(current, proposed) is True
        ), f"{current!r} should compare equal to {proposed!r}"
        # Must be symmetric.
        assert (
            values_equivalent(proposed, current) is True
        ), f"Equality must be symmetric: {proposed!r} vs {current!r}"

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
        assert (
            values_equivalent(current, proposed) is False
        ), f"{current!r} must NOT compare equal to {proposed!r}"

    # ---- Strict bool/int separation -------------------------------------
    #
    # Python evaluates ``True == 1`` and ``False == 0`` as ``True`` (bool
    # is a subclass of int).  Without the strict-bool guard in
    # ``values_equivalent``, a stored numeric setting would collapse with
    # a staged boolean and the operator would see a misleading "no
    # change" render.  Pin the policy here so a future contributor
    # cannot accidentally re-introduce the collapse.

    @pytest.mark.parametrize(
        ("current", "proposed"),
        [
            (False, 0),
            (True, 1),
            (0, False),
            (1, True),
            ("0", False),  # "0" → int 0; False → bool False; differ
            ("1", True),  # "1" → int 1; True → bool True; differ
            ("yes", 1),  # "yes" → bool True; 1 → int 1; differ
            ("no", 0),  # "no" → bool False; 0 → int 0; differ
        ],
    )
    def test_strict_bool_int_separation(self, current, proposed):
        """Bool/int must NOT collapse.  Operator-safe correctness: a
        false no-op (rendered as "no change" when state would change)
        is worse than a false diff (operator sees noise but no harm
        done).  When in doubt, the renderer should show the diff."""
        assert values_equivalent(current, proposed) is False, (
            f"{current!r} vs {proposed!r} must NOT be equivalent — "
            "Python's True == 1 would otherwise hide a real "
            "type-mismatch in the preflight render."
        )
        assert (
            values_equivalent(proposed, current) is False
        ), "Strict bool/int check must be symmetric."

    def test_bool_vs_string_int_form_is_mismatch(self):
        """Concrete demonstration: a setting stored as numeric ``"1"``
        and a staged boolean ``True`` are NOT equivalent — they
        represent different observable values even though Python's
        ``True == 1`` evaluates to True."""
        assert values_equivalent(True, "1") is False
        assert values_equivalent("1", True) is False
        assert values_equivalent(False, "0") is False
        assert values_equivalent("0", False) is False


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
        # PR-04b review fix: render_change_plan now appends a
        # truncation suffix when entries are dropped, so the line
        # count is max_lines + 1 (the indicator).
        assert len(lines) == 4
        assert lines[-1].startswith("…")


# ---------------------------------------------------------------------------
# PR-04b (review fix) — render_change_plan enforces Discord field limit
# ---------------------------------------------------------------------------


from services.setup_change_plan import (  # noqa: E402
    DISCORD_FIELD_VALUE_LIMIT,
    RenderedChangePlan,
    format_change_plan_lines,
    render_change_plan,
)


def _entry(label: str = "x", *, would_change: bool = True) -> ChangePlanEntry:
    return ChangePlanEntry(
        op=SetupOperation(kind="set_setting", subsystem="xp"),
        label=label,
        current=ChangeValue(kind="value", value="a"),
        proposed=ChangeValue(kind="value", value="b"),
        would_change=would_change,
    )


class TestRenderChangePlan:
    def test_empty_entries_returns_empty_block(self):
        r = render_change_plan([])
        assert r.lines == ()
        assert r.rendered_count == 0
        assert r.truncated is False
        assert r.dropped_count == 0
        assert r.body == ""

    def test_short_diff_renders_all_entries_no_truncation(self):
        entries = [_entry(f"op{i}") for i in range(3)]
        r = render_change_plan(entries)
        assert r.rendered_count == 3
        assert r.truncated is False
        assert r.dropped_count == 0
        assert len(r.lines) == 3
        # Body fits within Discord's field cap.
        assert len(r.body) <= DISCORD_FIELD_VALUE_LIMIT

    def test_many_line_diff_truncated_by_line_count(self):
        """``max_lines`` still works (per-entry cap) and the truncation
        suffix appears."""
        entries = [_entry(f"op{i}") for i in range(20)]
        r = render_change_plan(entries, max_lines=5)
        # 5 rendered + 1 truncation suffix
        assert r.rendered_count == 5
        assert r.truncated is True
        assert r.dropped_count == 15
        assert r.lines[-1].startswith("…")
        assert len(r.body) <= DISCORD_FIELD_VALUE_LIMIT

    def test_single_very_long_line_is_clipped(self):
        """One pathological label cannot consume the whole budget; the
        line is clipped to the per-line cap with an ellipsis."""
        long_label = "x" * 5000
        r = render_change_plan([_entry(long_label)])
        assert r.truncated is True
        # The single line must fit the per-line cap (~256 chars), well
        # under the field cap.
        assert all(len(line) <= 1024 for line in r.lines)
        # The very long content is signalled as truncated via ellipsis.
        assert any("…" in line for line in r.lines)

    def test_exactly_at_field_limit_does_not_overflow(self):
        """A render that exactly hits the field-cap budget must still
        return a body ≤ 1024 chars (suffix budget is reserved)."""
        # ~50-char labels × 30 entries ≈ 1500 raw chars (over cap),
        # so the renderer must stop early.
        entries = [_entry("x" * 50) for _ in range(30)]
        r = render_change_plan(entries, max_lines=30)
        assert r.truncated is True
        assert len(r.body) <= DISCORD_FIELD_VALUE_LIMIT

    def test_over_limit_diff_stops_packing_before_overflow(self):
        """When the line-count cap would admit more entries but the
        char budget runs out, the renderer must stop packing rather
        than blow the field limit."""
        entries = [_entry("x" * 100) for _ in range(20)]
        r = render_change_plan(entries, max_lines=20)
        assert r.rendered_count < 20
        assert r.dropped_count == 20 - r.rendered_count
        assert r.truncated is True
        assert len(r.body) <= DISCORD_FIELD_VALUE_LIMIT

    def test_truncation_suffix_carries_dropped_count(self):
        """``dropped_count`` reports how many entries were omitted so
        operators / tests can detect the truncation programmatically."""
        entries = [_entry(f"op{i}") for i in range(50)]
        r = render_change_plan(entries, max_lines=3)
        assert r.rendered_count == 3
        assert r.dropped_count == 47
        assert r.truncated is True

    def test_custom_field_limit_respected(self):
        """The ``field_limit`` parameter lets callers reuse the helper
        for non-embed-field surfaces (e.g. a panel description that
        caps at 4096)."""
        entries = [_entry(f"op{i}") for i in range(50)]
        r = render_change_plan(entries, max_lines=50, field_limit=4096)
        assert len(r.body) <= 4096

    def test_format_change_plan_lines_backcompat_shape(self):
        """The legacy helper still returns a list[str]; callers that
        only need the lines keep working unchanged."""
        entries = [_entry(f"op{i}") for i in range(3)]
        lines = format_change_plan_lines(entries)
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)
        # No truncation suffix on a short diff.
        assert not any("truncated" in line.lower() for line in lines)


# ---------------------------------------------------------------------------
# PR-04b (review fix) — degenerate field_limit edge cases
# ---------------------------------------------------------------------------


class TestRenderChangePlanFieldLimitEdgeCases:
    """Pin that the render helper NEVER returns a body longer than
    ``field_limit`` — including the degenerate case where
    ``field_limit`` is smaller than the truncation suffix itself.

    Operator-safe rule: the render contract is "embed-field safe", so
    a caller passing the result directly to ``embed.add_field(value=...)``
    can rely on the cap.  Returning the suffix when it would push the
    body over the cap was a bug in the original PR-04b helper.
    """

    def test_field_limit_smaller_than_suffix_returns_empty_body(self):
        entries = [_entry(f"op{i}") for i in range(3)]
        # _TRUNCATION_SUFFIX is ~38 chars; any field_limit below that
        # cannot include it.
        r = render_change_plan(entries, field_limit=20)
        assert len(r.body) <= 20, (
            f"Body must respect the field_limit; got {len(r.body)} chars: "
            f"{r.body!r}"
        )
        # The dataclass still reports truncated=True so callers know
        # content was dropped even when the suffix did not fit.
        assert r.truncated is True

    def test_field_limit_zero_returns_empty_body(self):
        """Degenerate but well-defined: zero budget → empty body."""
        entries = [_entry(f"op{i}") for i in range(3)]
        r = render_change_plan(entries, field_limit=0)
        assert r.body == ""
        assert r.lines == ()
        assert r.truncated is True

    def test_field_limit_exactly_at_suffix_length_admits_only_suffix(self):
        """A field_limit equal to the suffix length lets the suffix
        through but admits no real content lines."""
        from services.setup_change_plan import _TRUNCATION_SUFFIX

        entries = [_entry(f"op{i}") for i in range(3)]
        r = render_change_plan(entries, field_limit=len(_TRUNCATION_SUFFIX))
        # Either empty body, or just the suffix — but never over the cap.
        assert len(r.body) <= len(_TRUNCATION_SUFFIX)
        assert r.truncated is True

    def test_default_field_limit_handles_large_diff_without_overflow(self):
        """50 long entries with the default 1024-char cap must produce
        a body ≤ 1024 chars and a non-zero ``dropped_count``."""
        from services.setup_change_plan import DISCORD_FIELD_VALUE_LIMIT

        entries = [_entry("x" * 80) for _ in range(50)]
        r = render_change_plan(entries, max_lines=50)
        assert len(r.body) <= DISCORD_FIELD_VALUE_LIMIT
        assert r.truncated is True
        assert r.dropped_count > 0
