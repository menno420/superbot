"""Tests for utils.subsystem_registry.validate_identity_contract (INV-B).

Covers:
- clean state returns empty findings
- missing command for a non-internal entry_point is reported
- internal subsystems with no commands are NOT reported
- unknown router prefix is reported
- unknown view SUBSYSTEM is reported
- unknown panel_anchors row is reported
- DB error is swallowed (no raise)
- PR I1a: tier classification map + summarize_findings sibling helper
- PR I1a: invariant — every finding bucket has a tier classification
- PR I1b: apply_self_heal remediates auto_healable findings only
- PR I1b: apply_self_heal skips fatal-tier findings
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.subsystem_registry import (
    IDENTITY_FINDING_TIER,
    SUBSYSTEMS,
    apply_self_heal,
    summarize_findings,
    validate_identity_contract,
)


def _bot_with_commands(*names: str) -> MagicMock:
    cmds = [MagicMock(name=n) for n in names]
    # Mock's auto-name behaviour overrides .name; reset explicitly.
    for cmd, n in zip(cmds, names, strict=True):
        cmd.name = n
    bot = MagicMock()
    bot.commands = cmds
    return bot


@pytest.fixture
def _empty_registries():
    """Patch the three runtime registries to empty for predictable tests."""
    with (
        patch("core.runtime.interaction_router._handlers", {}),
        patch("core.runtime.persistent_views._REGISTRY", {}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=[]),
    ):
        yield


@pytest.mark.asyncio
async def test_clean_state_no_findings(_empty_registries):
    # Build a bot whose commands cover every non-internal entry_point in the
    # real registry — so the only finding source is left for other tests.
    all_eps = {
        ep
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }
    bot = _bot_with_commands(*all_eps)
    findings = await validate_identity_contract(bot)
    assert findings == {
        "entry_point_missing_command": [],
        "router_prefix_unknown": [],
        "view_subsystem_unknown": [],
        "db_anchor_subsystem_unknown": [],
        # Phase 1 schema findings — empty because no schemas registered yet.
        "schema_subsystem_unknown": [],
        "participation_schema_subsystem_unknown": [],
        "schema_capability_unknown": [],
    }


@pytest.mark.asyncio
async def test_missing_command_reported(_empty_registries):
    # Bot has no commands; every non-internal entry_point becomes a finding.
    bot = _bot_with_commands()
    findings = await validate_identity_contract(bot)
    assert len(findings["entry_point_missing_command"]) > 0
    # All reported entry_points belong to non-internal subsystems.
    for msg in findings["entry_point_missing_command"]:
        # Format: "subsystem=<name> entry_point=<ep>"
        assert "subsystem=" in msg and "entry_point=" in msg


@pytest.mark.asyncio
async def test_router_prefix_unknown_reported():
    all_eps = {
        ep
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }
    bot = _bot_with_commands(*all_eps)
    with (
        patch(
            "core.runtime.interaction_router._handlers",
            {"ghost": lambda *_: None},
        ),
        patch("core.runtime.persistent_views._REGISTRY", {}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=[]),
    ):
        findings = await validate_identity_contract(bot)
    assert "ghost" in findings["router_prefix_unknown"]


@pytest.mark.asyncio
async def test_view_subsystem_unknown_reported():
    all_eps = {
        ep
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }
    bot = _bot_with_commands(*all_eps)
    fake_view = MagicMock()
    with (
        patch("core.runtime.interaction_router._handlers", {}),
        patch("core.runtime.persistent_views._REGISTRY", {"ghost": fake_view}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=[]),
    ):
        findings = await validate_identity_contract(bot)
    assert "ghost" in findings["view_subsystem_unknown"]


@pytest.mark.asyncio
async def test_db_anchor_subsystem_unknown_reported():
    all_eps = {
        ep
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }
    bot = _bot_with_commands(*all_eps)
    rows = [{"subsystem": "ghost"}, {"subsystem": "role"}]
    with (
        patch("core.runtime.interaction_router._handlers", {}),
        patch("core.runtime.persistent_views._REGISTRY", {}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=rows),
    ):
        findings = await validate_identity_contract(bot)
    assert "ghost" in findings["db_anchor_subsystem_unknown"]
    # "role" exists in the real registry, so it should NOT appear.
    assert "role" not in findings["db_anchor_subsystem_unknown"]


@pytest.mark.asyncio
async def test_db_error_does_not_abort(_empty_registries):
    bot = _bot_with_commands()
    with patch(
        "utils.db.fetchall",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB down"),
    ):
        # Should NOT raise.
        findings = await validate_identity_contract(bot)
    # DB-based finding bucket is empty when DB is unreachable.
    assert findings["db_anchor_subsystem_unknown"] == []


# ---------------------------------------------------------------------------
# PR I1a — tier classification, summarize_findings, invariant tests
# ---------------------------------------------------------------------------


class TestIdentityFindingTier:
    """The tier map must cover every finding bucket the validator emits."""

    @pytest.mark.asyncio
    async def test_tier_map_covers_every_finding_bucket(self, _empty_registries):
        """Invariant: ``set(IDENTITY_FINDING_TIER) == set(validator findings)``.

        Adding a new finding bucket without a tier classification must
        fail this test — it's the durable guard the user requested.
        """
        bot = _bot_with_commands()
        findings = await validate_identity_contract(bot)
        assert set(IDENTITY_FINDING_TIER) == set(findings), (
            "IDENTITY_FINDING_TIER must classify every validator finding "
            f"bucket; missing: {set(findings) - set(IDENTITY_FINDING_TIER)}; "
            f"extra: {set(IDENTITY_FINDING_TIER) - set(findings)}"
        )

    def test_tier_values_are_known(self):
        """Every tier value must be one of the three documented severities."""
        valid_tiers = {"fatal", "auto_healable", "warn_only"}
        for kind, tier in IDENTITY_FINDING_TIER.items():
            assert tier in valid_tiers, (
                f"Unknown tier {tier!r} for finding kind {kind!r}; "
                f"must be one of {valid_tiers}"
            )

    def test_entry_point_missing_is_fatal(self):
        """``entry_point_missing_command`` violates routing/help integrity
        and is classified fatal-tier per the I1a refinement.
        """
        assert IDENTITY_FINDING_TIER["entry_point_missing_command"] == "fatal"


class TestSummarizeFindings:
    """``summarize_findings`` returns total + by_kind + by_tier."""

    def test_summary_totals_match_findings(self):
        findings = {
            "entry_point_missing_command": ["a", "b"],
            "router_prefix_unknown": ["x"],
            "view_subsystem_unknown": [],
            "db_anchor_subsystem_unknown": ["y", "z", "w"],
        }
        summary = summarize_findings(findings)
        assert summary["total"] == 6
        assert summary["by_kind"] == {
            "entry_point_missing_command": 2,
            "router_prefix_unknown": 1,
            "view_subsystem_unknown": 0,
            "db_anchor_subsystem_unknown": 3,
        }

    def test_summary_groups_by_tier(self):
        findings = {
            "entry_point_missing_command": ["a", "b"],  # fatal
            "router_prefix_unknown": ["x"],  # auto_healable
            "view_subsystem_unknown": ["y"],  # auto_healable
            "db_anchor_subsystem_unknown": ["z", "w"],  # auto_healable
        }
        summary = summarize_findings(findings)
        assert summary["by_tier"] == {
            "fatal": 2,
            "auto_healable": 4,
            "warn_only": 0,
        }

    def test_summary_clean_state(self):
        findings = {
            "entry_point_missing_command": [],
            "router_prefix_unknown": [],
            "view_subsystem_unknown": [],
            "db_anchor_subsystem_unknown": [],
        }
        summary = summarize_findings(findings)
        assert summary["total"] == 0
        assert summary["by_tier"] == {
            "fatal": 0,
            "auto_healable": 0,
            "warn_only": 0,
        }
        # Schema is stable even when empty.
        assert summary["by_kind"] == {
            "entry_point_missing_command": 0,
            "router_prefix_unknown": 0,
            "view_subsystem_unknown": 0,
            "db_anchor_subsystem_unknown": 0,
        }

    def test_unknown_kind_is_counted_as_fatal(self):
        """Defensive: an un-tier-classified bucket counts under fatal so
        the invariant test detects the omission instead of silently
        miscounting.
        """
        findings = {
            "entry_point_missing_command": [],
            "router_prefix_unknown": [],
            "view_subsystem_unknown": [],
            "db_anchor_subsystem_unknown": [],
            "made_up_future_bucket": ["x", "y"],
        }
        summary = summarize_findings(findings)
        # Total still correct.
        assert summary["total"] == 2
        # Unknown bucket counts as fatal in by_tier.
        assert summary["by_tier"]["fatal"] == 2


class TestApplySelfHeal:
    """PR I1b — apply_self_heal remediates auto_healable findings."""

    @pytest.mark.asyncio
    async def test_unregisters_orphan_router_prefixes(self):
        fake_router = {"ghost": object(), "alive": object()}
        findings = {
            "entry_point_missing_command": [],
            "router_prefix_unknown": ["ghost"],
            "view_subsystem_unknown": [],
            "db_anchor_subsystem_unknown": [],
        }
        with (
            patch(
                "core.runtime.interaction_router._handlers",
                fake_router,
            ),
            patch(
                "core.runtime.persistent_views._REGISTRY",
                {},
            ),
            patch(
                "utils.db.mark_anchors_stale_for_subsystem",
                new_callable=AsyncMock,
            ) as mock_mark,
        ):
            counts = await apply_self_heal(findings)
        assert counts["router_prefixes_unregistered"] == 1
        assert "ghost" not in fake_router
        assert "alive" in fake_router
        mock_mark.assert_not_called()

    @pytest.mark.asyncio
    async def test_unregisters_orphan_views(self):
        fake_view_registry = {"ghost_view": object(), "alive_view": object()}
        findings = {
            "entry_point_missing_command": [],
            "router_prefix_unknown": [],
            "view_subsystem_unknown": ["ghost_view"],
            "db_anchor_subsystem_unknown": [],
        }
        with (
            patch("core.runtime.interaction_router._handlers", {}),
            patch(
                "core.runtime.persistent_views._REGISTRY",
                fake_view_registry,
            ),
            patch(
                "utils.db.mark_anchors_stale_for_subsystem",
                new_callable=AsyncMock,
            ),
        ):
            counts = await apply_self_heal(findings)
        assert counts["views_unregistered"] == 1
        assert "ghost_view" not in fake_view_registry
        assert "alive_view" in fake_view_registry

    @pytest.mark.asyncio
    async def test_marks_orphan_anchors_stale(self):
        findings = {
            "entry_point_missing_command": [],
            "router_prefix_unknown": [],
            "view_subsystem_unknown": [],
            "db_anchor_subsystem_unknown": ["ghost_a", "ghost_b"],
        }
        mock_mark = AsyncMock(side_effect=[3, 2])
        with (
            patch("core.runtime.interaction_router._handlers", {}),
            patch("core.runtime.persistent_views._REGISTRY", {}),
            patch("utils.db.mark_anchors_stale_for_subsystem", mock_mark),
        ):
            counts = await apply_self_heal(findings)
        assert counts["anchors_marked_stale"] == 5  # 3 + 2
        assert mock_mark.await_count == 2
        # Calls are by subsystem name, in order.
        names = [c.args[0] for c in mock_mark.await_args_list]
        assert names == ["ghost_a", "ghost_b"]

    @pytest.mark.asyncio
    async def test_fatal_findings_are_skipped(self):
        """``entry_point_missing_command`` is fatal-tier — never auto-healed.

        Cog load failure must be diagnosed by the operator (reload the
        cog, check logs), not silently masked by registry pruning.
        """
        findings = {
            "entry_point_missing_command": ["lost_cmd_1", "lost_cmd_2"],
            "router_prefix_unknown": [],
            "view_subsystem_unknown": [],
            "db_anchor_subsystem_unknown": [],
        }
        # Sanity: the tier map agrees this is fatal.
        assert IDENTITY_FINDING_TIER["entry_point_missing_command"] == "fatal"
        with (
            patch("core.runtime.interaction_router._handlers", {}),
            patch("core.runtime.persistent_views._REGISTRY", {}),
            patch(
                "utils.db.mark_anchors_stale_for_subsystem",
                new_callable=AsyncMock,
            ) as mock_mark,
        ):
            counts = await apply_self_heal(findings)
        assert counts["skipped_fatal"] == 2
        assert counts["router_prefixes_unregistered"] == 0
        assert counts["views_unregistered"] == 0
        assert counts["anchors_marked_stale"] == 0
        mock_mark.assert_not_called()

    @pytest.mark.asyncio
    async def test_clean_state_returns_zero_counts(self):
        findings = {
            "entry_point_missing_command": [],
            "router_prefix_unknown": [],
            "view_subsystem_unknown": [],
            "db_anchor_subsystem_unknown": [],
        }
        with (
            patch("core.runtime.interaction_router._handlers", {}),
            patch("core.runtime.persistent_views._REGISTRY", {}),
            patch(
                "utils.db.mark_anchors_stale_for_subsystem",
                new_callable=AsyncMock,
            ),
        ):
            counts = await apply_self_heal(findings)
        assert counts == {
            "router_prefixes_unregistered": 0,
            "views_unregistered": 0,
            "anchors_marked_stale": 0,
            "skipped_fatal": 0,
        }

    @pytest.mark.asyncio
    async def test_db_unavailable_does_not_abort(self):
        """If the DB cleanup raises, self-heal logs a warning and
        continues — partial healing is better than no healing.
        """
        findings = {
            "entry_point_missing_command": [],
            "router_prefix_unknown": ["ghost_prefix"],
            "view_subsystem_unknown": [],
            "db_anchor_subsystem_unknown": ["ghost_anchor"],
        }
        fake_router = {"ghost_prefix": object()}
        with (
            patch(
                "core.runtime.interaction_router._handlers",
                fake_router,
            ),
            patch("core.runtime.persistent_views._REGISTRY", {}),
            patch(
                "utils.db.mark_anchors_stale_for_subsystem",
                new_callable=AsyncMock,
                side_effect=RuntimeError("DB down"),
            ),
        ):
            counts = await apply_self_heal(findings)
        # Router cleanup succeeded …
        assert counts["router_prefixes_unregistered"] == 1
        # … even though DB cleanup failed.
        assert counts["anchors_marked_stale"] == 0


class TestStrictMode:
    """PR I1b + S5.1 — IDENTITY_CONTRACT_STRICT/STRICT_DISABLED env vars.

    The truthy-IDENTITY_CONTRACT_STRICT case is kept here for symmetry
    with the I1b origin.  The full post-S5.1 truth table (default-on,
    STRICT_DISABLED escape hatch, legacy-false opt-out, precedence
    rules) lives in
    ``tests/unit/registry/test_identity_strict_default.py``.
    """

    def test_strict_flag_helper_truthy_values(self, monkeypatch):
        from bot1 import _identity_contract_strict

        # Clear the S5.1 escape hatch so it doesn't override.
        monkeypatch.delenv("STRICT_DISABLED", raising=False)
        for value in ("1", "true", "TRUE", "yes", "Yes", "on", "ON"):
            monkeypatch.setenv("IDENTITY_CONTRACT_STRICT", value)
            assert _identity_contract_strict() is True, value


class TestMetricEmission:
    """The startup orchestrator increments the metric per finding kind.

    We test the contract — every non-zero ``summary["by_kind"]`` value
    becomes a single ``.labels(kind=...).inc(count)`` call — rather than
    re-running bot1.main(), which would require the full async harness.
    """

    def test_metric_increments_per_kind(self):
        from services import metrics

        findings = {
            "entry_point_missing_command": ["a", "b"],
            "router_prefix_unknown": [],
            "view_subsystem_unknown": ["x"],
            "db_anchor_subsystem_unknown": ["y", "z", "w"],
        }
        summary = summarize_findings(findings)

        labeled: list[tuple[str, int]] = []
        # Patch the labels() chain so we can record inc() arguments.
        original = metrics.identity_contract_findings_total
        try:
            tracker = MagicMock()

            def make_label_call(kind):
                m = MagicMock()
                m.inc = lambda n=1: labeled.append((kind, n))
                return m

            tracker.labels = MagicMock(side_effect=make_label_call)
            metrics.identity_contract_findings_total = tracker

            # Mirror the orchestrator loop from bot1.py.
            for kind, count in summary["by_kind"].items():
                if count:
                    metrics.identity_contract_findings_total.labels(
                        kind=kind,
                    ).inc(count)
        finally:
            metrics.identity_contract_findings_total = original

        # No-zero kinds were skipped.
        labeled_dict = dict(labeled)
        assert labeled_dict == {
            "entry_point_missing_command": 2,
            "view_subsystem_unknown": 1,
            "db_anchor_subsystem_unknown": 3,
        }
        # router_prefix_unknown had zero findings — must not be emitted.
        assert "router_prefix_unknown" not in labeled_dict
