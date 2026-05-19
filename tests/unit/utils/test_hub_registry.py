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

    S7 → Economy. S8 → Moderation/Safety. S9 → Community. S10 →
    Utility. The map's S10 milestone is now complete; future PRs
    that add hubs must come with a real panel or fail this test.
    """
    assert {hub.key for hub in HUBS} == {
        "games",
        "economy",
        "moderation",
        "community",
        "utility",
        "admin",
        "settings",
        "diagnostic",
    }


def test_utility_hub_uses_existing_panel():
    """S10 v1: the Utility hub routes to the existing utility_cog
    build_help_menu_view (UtilityHubView). General and Help remain
    top-level for now; promotion to parent_hub="utility" lands when
    the hub view gains explicit child navigation.
    """
    utility = get_hub("utility")
    assert utility is not None
    assert utility.entry_command == "!utilitymenu"
    assert utility.minimum_tier == "user"
    assert utility.primary_children == ()
    assert utility.cross_link_children == ()
    assert utility.panel_available is True


def test_community_hub_uses_new_cog():
    """S9: the Community hub gets a brand-new ``community_cog`` because
    no existing domain cog naturally owns the union of XP + Roles +
    Counting + Chain + Leaderboard. The cog is nav-only; cross-link
    buttons forward to the host cogs' existing build_help_menu_view.
    """
    community = get_hub("community")
    assert community is not None
    assert community.entry_command == "!community"
    assert community.minimum_tier == "user"
    assert community.primary_children == ()
    assert community.cross_link_children == ()
    assert community.panel_available is True


def test_moderation_hub_uses_existing_panel():
    """S8 v1: the Moderation/Safety hub routes to
    moderation_cog.build_help_menu_view (ModPanelView). Cleanup and
    Logging stay top-level for now — promotion to parent_hub of
    "moderation" lands when the hub view gains explicit child nav.
    """
    moderation = get_hub("moderation")
    assert moderation is not None
    assert moderation.entry_command == "!modmenu"
    assert moderation.minimum_tier == "moderator"
    assert moderation.primary_children == ()
    assert moderation.cross_link_children == ()
    assert moderation.panel_available is True


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
    """Normal users see Games + Economy + Community + Utility (user
    tier) but not Moderation (moderator) or Admin/Settings/Platform
    (administrator).
    """
    visible = {hub.key for hub in hubs_for_tier("user")}
    assert "games" in visible
    assert "economy" in visible
    assert "community" in visible
    assert "utility" in visible
    assert "moderation" not in visible
    assert "admin" not in visible
    assert "settings" not in visible
    assert "diagnostic" not in visible


def test_hubs_for_tier_moderator_sees_moderation_but_not_admin():
    """Moderators see user-tier hubs + Moderation, but still can't open
    administrator-restricted hubs (Admin/Settings/Platform).
    """
    visible = {hub.key for hub in hubs_for_tier("moderator")}
    assert "games" in visible
    assert "economy" in visible
    assert "community" in visible
    assert "utility" in visible
    assert "moderation" in visible
    assert "admin" not in visible
    assert "settings" not in visible
    assert "diagnostic" not in visible


def test_hubs_for_tier_administrator_sees_all():
    visible = {hub.key for hub in hubs_for_tier("administrator")}
    assert visible == {
        "games",
        "economy",
        "moderation",
        "community",
        "utility",
        "admin",
        "settings",
        "diagnostic",
    }


def test_hubs_for_tier_owner_sees_all():
    visible = {hub.key for hub in hubs_for_tier("owner")}
    assert visible == {
        "games",
        "economy",
        "moderation",
        "community",
        "utility",
        "admin",
        "settings",
        "diagnostic",
    }


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
