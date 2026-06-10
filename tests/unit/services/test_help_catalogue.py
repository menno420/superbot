"""Contract tests for the Help Catalogue (HLP-2 Phase 1).

The catalogue is the stable-keyed inventory the Help projection and the
future guild overlay (HLP-3) validate against. These tests pin:

* identity — one row per registered hub / subsystem, canonical orders;
* relationships — host-subsystem convention, parent_hub/top_level shape;
* **zero registry-drift findings** — the four finding kinds
  (``hub_without_subsystem`` / ``unknown_parent_hub`` / ``tier_mismatch``
  / ``roster_drift``) are all empty today. ``tier_mismatch`` empty is the
  Q-0074 placement pin: every hub's ``minimum_tier`` equals its host
  subsystem's ``visibility_tier``, so Help-Home placement and governance
  visibility can never silently disagree again (FIND-B03).
"""

from __future__ import annotations

from services.help_catalogue import (
    build_help_catalogue,
    invalidate_help_catalogue_cache,
)
from utils.hub_registry import HUBS
from utils.subsystem_registry import SUBSYSTEMS, all_subsystems_sorted


def setup_function() -> None:
    invalidate_help_catalogue_cache()


def teardown_function() -> None:
    invalidate_help_catalogue_cache()


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def test_one_hub_row_per_registered_hub_in_registry_order():
    catalogue = build_help_catalogue()
    assert [h.key for h in catalogue.hubs] == [h.key for h in HUBS]
    # The HubEntry passthrough is the registry object itself, not a copy.
    for row, hub in zip(catalogue.hubs, HUBS):
        assert row.entry is hub


def test_one_subsystem_row_per_registry_entry_in_ui_priority_order():
    catalogue = build_help_catalogue()
    assert [s.key for s in catalogue.subsystems] == [
        name for name, _meta in all_subsystems_sorted()
    ]
    assert len(catalogue.subsystems) == len(SUBSYSTEMS)


def test_subsystem_rows_snapshot_registry_metadata():
    catalogue = build_help_catalogue()
    row = catalogue.subsystem("blackjack")
    assert row is not None
    meta = SUBSYSTEMS["blackjack"]
    assert row.display_name == meta["display_name"]
    assert row.visibility_tier == meta["visibility_tier"]
    assert row.entry_points == tuple(meta["entry_points"])
    assert row.parent_hub == meta.get("parent_hub")


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


def test_every_hub_has_a_same_key_host_subsystem():
    """The host-subsystem convention: each hub key is a subsystem key."""
    catalogue = build_help_catalogue()
    for row in catalogue.hubs:
        assert (
            row.host_subsystem == row.key
        ), f"hub {row.key!r} lost its same-key host subsystem"


def test_top_level_flag_matches_parent_hub_absence():
    catalogue = build_help_catalogue()
    for row in catalogue.subsystems:
        assert row.top_level == (row.parent_hub is None), row.key


def test_accessors_return_rows_or_none():
    catalogue = build_help_catalogue()
    assert catalogue.hub("games") is not None
    assert catalogue.hub("not-a-hub") is None
    assert catalogue.subsystem("xp") is not None
    assert catalogue.subsystem("not-a-subsystem") is None


# ---------------------------------------------------------------------------
# Findings — all four drift classes pinned empty
# ---------------------------------------------------------------------------


def test_no_registry_drift_findings():
    """Empty findings = the registries agree with each other.

    A new finding here is real drift (a hub without its host subsystem, a
    dangling parent_hub, a hub/subsystem tier contradiction, or a child
    roster mismatch) — fix the registries, don't relax this pin.
    """
    catalogue = build_help_catalogue()
    assert catalogue.findings == (), [
        f"{f.kind}:{f.key} — {f.detail}" for f in catalogue.findings
    ]


def test_tier_mismatch_finding_is_the_q0074_placement_pin():
    """Explicit form of the Q-0074 pin: hub placement tier == host
    subsystem governance tier, for every hub (Admin included — the
    registry row moved owner → administrator with the 2026-06-10 answer)."""
    for hub in HUBS:
        assert SUBSYSTEMS[hub.key]["visibility_tier"] == hub.minimum_tier, (
            f"hub {hub.key!r}: minimum_tier={hub.minimum_tier!r} disagrees "
            f"with subsystem visibility_tier="
            f"{SUBSYSTEMS[hub.key]['visibility_tier']!r}"
        )


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


def test_catalogue_is_cached_until_invalidated():
    first = build_help_catalogue()
    assert build_help_catalogue() is first
    invalidate_help_catalogue_cache()
    rebuilt = build_help_catalogue()
    assert rebuilt is not first
    assert rebuilt == first
