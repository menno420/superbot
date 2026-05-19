"""Unit tests for the central hub presentation registry (S3).

Pins the canonical structure shipped with S3 v1 (existing-hub-only
rollout): only mother hubs whose panels exist today appear here.
Economy, Moderation/Safety, Community, and Utility hubs are added by
S7-S10 PRs and will land with their own entries — the tests should
fail loudly if a hub is added without a corresponding panel.
"""

from __future__ import annotations

from utils.hub_registry import (
    ALL_COMMANDS_KEY,
    HUBS,
    HubEntry,
    get_hub,
    hubs_for_tier,
)
from utils.subsystem_registry import SUBSYSTEMS

# ---------------------------------------------------------------------------
# Registry shape
# ---------------------------------------------------------------------------


def test_hubs_are_immutable_tuple_of_hubentry():
    """HUBS is intentionally a tuple — readers may iterate but not mutate.
    Each entry must be a frozen HubEntry so a stale reference can't be
    edited at runtime.
    """
    assert isinstance(HUBS, tuple)
    for hub in HUBS:
        assert isinstance(hub, HubEntry)


def test_hub_keys_are_unique():
    keys = [hub.key for hub in HUBS]
    assert len(keys) == len(set(keys)), f"duplicate hub keys: {keys}"


def test_all_commands_key_is_not_a_hub():
    """ALL_COMMANDS_KEY is a sentinel for the permanent fallback option,
    not a mother hub. It must not appear in HUBS.
    """
    assert ALL_COMMANDS_KEY not in {hub.key for hub in HUBS}


def test_committed_hub_set_matches_promoted_hubs():
    """The committed hub set is the union of S3 v1 (Games, Admin,
    Settings, Platform) plus any hubs promoted in later PRs.

    S7 promotes Economy. Moderation/Safety (S8), Community (S9), and
    Utility (S10) join when their hub views land — adding a hub here
    without a real panel would re-introduce the "Coming soon"
    category that the mother-hub map forbids.
    """
    assert {hub.key for hub in HUBS} == {
        "games",
        "economy",
        "admin",
        "settings",
        "diagnostic",
    }


def test_economy_hub_uses_existing_panel():
    """S7 v1: the Economy hub category routes to the existing
    economy_cog.build_help_menu_view panel. Inventory/Leaderboard
    are NOT yet parent_hub="economy" — that promotion happens in a
    follow-up PR once the hub view gains explicit child navigation.
    """
    economy = get_hub("economy")
    assert economy is not None
    assert economy.entry_command == "!economymenu"
    # Empty primary_children / cross_links in v1 — pin so a future
    # PR doesn't silently rewrite child wiring without updating
    # subsystem metadata too.
    assert economy.primary_children == ()
    assert economy.cross_link_children == ()
    assert economy.panel_available is True
    assert economy.minimum_tier == "user"


# ---------------------------------------------------------------------------
# Cross-references with SUBSYSTEMS
# ---------------------------------------------------------------------------


def test_hub_keys_resolve_to_real_subsystems():
    """Every hub key must correspond to a real ``SUBSYSTEMS`` entry so
    ``_cog_for_subsystem(hub.key)`` can find the host cog.
    """
    for hub in HUBS:
        assert hub.key in SUBSYSTEMS, (
            f"hub key {hub.key!r} has no matching SUBSYSTEMS entry"
        )


def test_games_hub_primary_children_match_parent_hub_filter():
    """The Games hub's ``primary_children`` must equal the set of
    SUBSYSTEMS entries whose ``parent_hub == "games"`` — otherwise the
    Help "Includes:" line and the GamesHubView dropdown disagree.
    """
    games = get_hub("games")
    assert games is not None
    declared = set(games.primary_children)
    actual = {
        name
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == "games"
    }
    assert declared == actual, (
        f"Games primary_children {declared} != parent_hub filter {actual}"
    )


# ---------------------------------------------------------------------------
# Tier visibility
# ---------------------------------------------------------------------------


def test_hubs_for_tier_user_sees_only_user_tier_hubs():
    """Normal users see Games + Economy (user tier) but not
    Admin/Settings/Platform (administrator tier).
    """
    visible = {hub.key for hub in hubs_for_tier("user")}
    assert "games" in visible
    assert "economy" in visible
    assert "admin" not in visible
    assert "settings" not in visible
    assert "diagnostic" not in visible


def test_hubs_for_tier_administrator_sees_all():
    visible = {hub.key for hub in hubs_for_tier("administrator")}
    assert visible == {"games", "economy", "admin", "settings", "diagnostic"}


def test_hubs_for_tier_owner_sees_all():
    visible = {hub.key for hub in hubs_for_tier("owner")}
    assert visible == {"games", "economy", "admin", "settings", "diagnostic"}


def test_hubs_for_tier_filters_panel_unavailable():
    """If a hub were to be defined with panel_available=False, it must
    not appear regardless of tier. Pinned via a runtime-constructed
    fake registry so the contract holds even when no hub uses it.
    """
    from dataclasses import replace

    # Mutate a copy of an existing hub to flip the flag.
    fake_hub = replace(HUBS[0], panel_available=False)
    # Use the same hubs_for_tier code but with a monkeypatch on HUBS.
    import utils.hub_registry as registry

    original = registry.HUBS
    try:
        registry.HUBS = (fake_hub,)
        visible = registry.hubs_for_tier("owner")
        assert visible == []
    finally:
        registry.HUBS = original


# ---------------------------------------------------------------------------
# Doctrine: registry is presentation, not a router
# ---------------------------------------------------------------------------


def test_no_runtime_callable_fields_on_hubentry():
    """HubEntry is a frozen dataclass with literal/string fields only —
    no callbacks, no factory closures. Pins the "presentation only"
    doctrine; if a future field types a callable, this catches it.
    """
    import dataclasses

    for field in dataclasses.fields(HubEntry):
        annotation = field.type
        # Allow str, str|None, int, bool, tuple[str, ...], etc. Reject
        # anything that looks like a callable type.
        assert "Callable" not in str(annotation), (
            f"HubEntry.{field.name} appears to type a callable — registry "
            "must stay presentation-only"
        )
