"""Grammar-spike tests — the manifests are real and the rules fire.

Pin: (1) the three example manifests construct (every §3.2-phase-1
validator ran), (2) the S/A/O classification is total (§2.0's red-check),
(3) the compile rules the design spec promises actually reject bad input,
(4) the measurement ledger is internally consistent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.grammar_spike import spec as g  # noqa: E402
from tools.grammar_spike.manifests import ALL_MANIFESTS  # noqa: E402
from tools.grammar_spike.measure import UNITS, compute  # noqa: E402


def test_all_three_manifests_construct():
    keys = {m.key for m in ALL_MANIFESTS}
    assert keys == {"karma", "logging", "blackjack"}


def test_every_spec_field_is_role_tagged():
    for spec_type in g.ALL_SPEC_TYPES:
        assert not g.untagged_fields(spec_type), spec_type.__name__


def test_manifest_keys_are_shipped_subsystem_keys():
    """Compat item 1: the example manifests use the persisted keys verbatim."""
    sys.path.insert(0, str(_REPO_ROOT / "disbot"))
    from utils.subsystem_registry import SUBSYSTEMS

    for manifest in ALL_MANIFESTS:
        assert manifest.key in SUBSYSTEMS


def test_two_lane_authority_rule_fires():
    with pytest.raises(ValueError, match="two-lane"):
        g.CommandSpec(
            name="bad",
            kind=g.CommandKind.PREFIX,
            summary="",
            route=g.PanelRef("x"),
            capability_required="x.y.z",
            audience_tier="staff",
        )


def test_external_side_effects_forces_opt_in():
    with pytest.raises(ValueError, match="off_until_opt_in"):
        g.SettingSpec(
            name="scan",
            value_type="bool",
            default=False,
            settings_key="k",
            activation=g.Activation.ON_BY_DEFAULT,
            external_side_effects=True,
        )


def test_bool_setting_requires_conscious_activation():
    with pytest.raises(ValueError, match="activation"):
        g.SettingSpec(name="b", value_type="bool", default=False, settings_key="k")


def test_persistent_panel_requires_no_timeout():
    with pytest.raises(ValueError, match="persistent"):
        g.PanelSpec(
            panel_id="p",
            subsystem="s",
            title="t",
            audience="persistent",
            timeout_s=60,
        )


def test_layout_coverage_rule_fires():
    action = g.PanelActionSpec(
        action_id="a",
        label="A",
        handler=g.PanelRef("p"),
    )
    with pytest.raises(ValueError, match="coverage"):
        g.PanelSpec(
            panel_id="p",
            subsystem="s",
            title="t",
            actions=(action,),
            layout=g.LayoutSpec(pages=(((("a",), ("ghost",))),)),
        )


def test_subscriberless_event_requires_observability_marker():
    with pytest.raises(ValueError, match="observability_only"):
        g.EventSpec(
            name="x.y",
            payload_schema=(),
            owner_subsystem="x",
        )


def test_command_pool_is_kind_scoped_but_duplicates_die():
    """G-6: /karma + !karma coexist; two prefix karmas collide."""
    card = g.PanelRef("card")
    g.SubsystemManifest(
        key="k",
        display_name="K",
        description="",
        commands=(
            g.CommandSpec(name="x", kind=g.CommandKind.PREFIX, summary="", route=card),
            g.CommandSpec(name="x", kind=g.CommandKind.SLASH, summary="", route=card),
        ),
    )
    with pytest.raises(ValueError, match="duplicate prefix"):
        g.SubsystemManifest(
            key="k",
            display_name="K",
            description="",
            commands=(
                g.CommandSpec(
                    name="x",
                    kind=g.CommandKind.PREFIX,
                    summary="",
                    route=card,
                ),
                g.CommandSpec(
                    name="y",
                    kind=g.CommandKind.PREFIX,
                    summary="",
                    route=card,
                    aliases=("x",),
                ),
            ),
        )


def test_destructive_action_must_be_danger_styled():
    with pytest.raises(ValueError, match="danger"):
        g.PanelActionSpec(
            action_id="wipe",
            label="Wipe",
            handler=g.PanelRef("p"),
            destructive=True,
            style="primary",
        )


def test_measurement_ledger_is_consistent():
    for unit in UNITS:
        assert unit.tier_spec in (1, 2, 3), unit
        assert unit.tier_proposed in (1, 2, 3), unit
        # proposals only ever LOWER a tier (they add expressiveness)
        assert unit.tier_proposed <= unit.tier_spec, unit
        assert unit.rationale, unit
    stats = compute()
    assert set(stats) == {"karma", "logging", "blackjack", "OVERALL"}
    for row in stats.values():
        assert 0.0 <= row["spec_fit"] <= row["proposed_fit"] <= 1.0


def test_results_doc_matches_ledger():
    """RESULTS.md is generated — if the ledger changed, it must be re-run."""
    results = (_REPO_ROOT / "tools" / "grammar_spike" / "RESULTS.md").read_text()
    stats = compute()
    overall = stats["OVERALL"]
    assert f"**{overall['spec_fit']:.0%}**" in results
    assert f"**{overall['proposed_fit']:.0%}**" in results
