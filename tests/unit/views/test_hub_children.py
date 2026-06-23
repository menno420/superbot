"""Unit tests for the shared hub child-discovery primitive."""

from __future__ import annotations

import pytest

from views.hub_children import discover_hub_children


def test_utility_children_are_general_and_four_twenty():
    """The Utility hub's registry children (the general-cog fix relies on this)."""
    keys = [name for name, _ in discover_hub_children("utility")]
    assert "general" in keys
    assert "four_twenty" in keys


def test_unknown_hub_has_no_children():
    assert discover_hub_children("nope-not-a-hub") == []


def test_default_sort_is_ui_priority_then_key(monkeypatch):
    fake = {
        "b_low": {"parent_hub": "h", "ui_priority": 5},
        "a_high": {"parent_hub": "h", "ui_priority": 1},
        "c_mid": {"parent_hub": "h", "ui_priority": 1},  # tie → key order
        "other": {"parent_hub": "elsewhere", "ui_priority": 0},
    }
    monkeypatch.setattr("views.hub_children.SUBSYSTEMS", fake)
    assert [n for n, _ in discover_hub_children("h")] == ["a_high", "c_mid", "b_low"]


def test_group_order_sorts_groups_first(monkeypatch):
    fake = {
        "act": {"parent_hub": "g", "hub_group": "activities", "ui_priority": 0},
        "comp": {"parent_hub": "g", "hub_group": "competitive", "ui_priority": 9},
    }
    monkeypatch.setattr("views.hub_children.SUBSYSTEMS", fake)
    order = {"competitive": 0, "activities": 1}
    # competitive ranks first despite higher ui_priority — group beats priority.
    assert [n for n, _ in discover_hub_children("g", group_order=order)] == [
        "comp",
        "act",
    ]


def test_meta_is_copied(monkeypatch):
    fake = {"x": {"parent_hub": "h", "ui_priority": 0}}
    monkeypatch.setattr("views.hub_children.SUBSYSTEMS", fake)
    _, meta = discover_hub_children("h")[0]
    meta["mutated"] = True
    assert "mutated" not in fake["x"]  # caller mutation must not leak into the registry


def test_delegation_matches_games_and_community():
    """The 3 hubs delegate to this primitive — pin the equivalence."""
    from views.community.hub import discover_community_children
    from views.games.hub import _GROUP_ORDER, discover_game_children

    assert discover_game_children() == discover_hub_children(
        "games", group_order=_GROUP_ORDER
    )
    primary, _cross = discover_community_children()
    assert primary == discover_hub_children("community")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
