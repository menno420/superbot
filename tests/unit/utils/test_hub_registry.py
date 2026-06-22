"""Unit tests for the central hub presentation registry (S3).

Pins the canonical structure shipped with S3 v1 (existing-hub-only
rollout): only mother hubs whose panels exist today appear here.
Economy, Moderation/Safety, Community, and Utility hubs are added by
S7-S10 PRs and will land with their own entries — the tests should
fail loudly if a hub is added without a corresponding panel.
"""

from __future__ import annotations

from utils.hub_registry import (
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


def test_committed_hub_set_matches_promoted_hubs():
    """The committed top-level hub set after the help-menu regrouping
    (PR #1290): Games, BTD6, Economy, Moderation & Safety, Community,
    Utility, and the consolidated Server & Admin section.

    The regrouping nested the four former child-less admin hubs
    (Admin, Settings, Diagnostics/Platform, Server Management) into one
    ``admin`` section so the admin-side Help index stops being crowded —
    ``settings`` / ``diagnostic`` / ``server_management`` are now
    ``admin`` children, not top-level hubs. Future PRs that add a
    top-level hub must come with a real panel or fail this test.
    """
    assert {hub.key for hub in HUBS} == {
        "games",
        "btd6",
        "economy",
        "moderation",
        "community",
        "utility",
        "admin",
    }


def test_utility_hub_uses_existing_panel():
    """Post-PR-#3: the Utility hub routes to the existing utility_cog
    ``build_help_menu_view`` (UtilityHubView). ``general`` is its
    primary child via ``parent_hub="utility"``; PR #420 adds the 🍃
    ``four_twenty`` easter-egg subsystem as a second utility child.
    ``help`` itself stays top-level — it IS the Help surface.
    """
    utility = get_hub("utility")
    assert utility is not None
    assert utility.entry_command == "!utilitymenu"
    assert utility.minimum_tier == "user"
    assert utility.primary_children == ("general", "four_twenty")
    assert utility.cross_link_children == ()
    assert utility.panel_available is True


def test_community_hub_uses_new_cog():
    """Post-PR-#4: the Community hub's ``community_cog`` is nav-only.
    ``xp`` and ``role`` are primary children via ``parent_hub=
    "community"``. Counting, Chain (Games children) and Leaderboard
    (Economy child) are now declared as ``cross_link_children`` so the
    ``CommunityHubView`` can discover them from registry rather than
    a hardcoded view-local tuple.
    """
    community = get_hub("community")
    assert community is not None
    assert community.entry_command == "!community"
    assert community.minimum_tier == "user"
    # welcome + counters homed here by the help-menu regrouping (PR #1290);
    # both are administrator-tier so they stay operator-only in the user view.
    assert community.primary_children == (
        "xp",
        "karma",
        "community_spotlight",
        "role",
        "welcome",
        "counters",
    )
    assert community.cross_link_children == ("counting", "chain", "leaderboard")
    assert community.panel_available is True


def test_moderation_hub_uses_existing_panel():
    """Post-PR-#3: the Moderation/Safety hub routes to
    ``moderation_cog.build_help_menu_view`` (ModPanelView). Cleanup,
    Logging, and Proof Channel are now primary children via
    ``parent_hub="moderation"``.
    """
    moderation = get_hub("moderation")
    assert moderation is not None
    assert moderation.entry_command == "!modmenu"
    assert moderation.minimum_tier == "moderator"
    # security homed here by the help-menu regrouping (PR #1290).
    assert moderation.primary_children == (
        "automod",
        "image_moderation",
        "cleanup",
        "logging",
        "proof_channel",
        "security",
    )
    assert moderation.cross_link_children == ()
    assert moderation.panel_available is True


def test_admin_hub_consolidates_ops_sections():
    """Help-menu regrouping (PR #1290): the Server & Admin hub is the single
    operator section. The four former child-less admin hubs (Admin, Settings,
    Diagnostics/Platform, Server Management) plus Channels, AI Platform, and
    UX Lab are now its primary children, so the admin-side Help index is no
    longer crowded. Pinned so a future change can't silently re-split them.
    """
    admin = get_hub("admin")
    assert admin is not None
    assert admin.display_name == "Server & Admin"
    assert admin.minimum_tier == "administrator"
    assert set(admin.primary_children) == {
        "ux_lab",
        "channel",
        "server_management",
        "ai",
        "settings",
        "diagnostic",
    }
    # The nested ops surfaces are no longer top-level hubs.
    hub_keys = {hub.key for hub in HUBS}
    for nested in ("settings", "diagnostic", "server_management"):
        assert nested not in hub_keys


def test_btd6_is_top_level_hub():
    """M1 of the BTD6-top-level + AI-central-policy initiative:
    BTD6 Assistant is its own top-level hub. It has no
    primary_children (BTD6 has no sub-cogs), no cross_link_children,
    is user-tier visible, and has a real panel.

    Pinned so a future change cannot silently demote BTD6 back to a
    Games child.
    """
    btd6 = get_hub("btd6")
    assert btd6 is not None
    assert btd6.entry_command == "!btd6"
    assert btd6.minimum_tier == "user"
    assert btd6.primary_children == ()
    assert btd6.cross_link_children == ()
    assert btd6.panel_available is True

    # No Games cross-link by accepted decision.
    games = get_hub("games")
    assert games is not None
    assert "btd6" not in games.primary_children
    assert "btd6" not in games.cross_link_children


def test_economy_hub_uses_existing_panel():
    """Post-PR-#3: the Economy hub category routes to the existing
    ``economy_cog.build_help_menu_view`` panel. Inventory and
    Leaderboard are now primary children via ``parent_hub="economy"``.
    Mining stays under Games (its primary) and appears here only as a
    cross-link.
    """
    economy = get_hub("economy")
    assert economy is not None
    assert economy.entry_command == "!economymenu"
    assert economy.primary_children == ("inventory", "leaderboard", "treasury")
    assert economy.cross_link_children == ("mining",)
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
        assert (
            hub.key in SUBSYSTEMS
        ), f"hub key {hub.key!r} has no matching SUBSYSTEMS entry"


def test_games_hub_primary_children_match_parent_hub_filter():
    """The Games hub's ``primary_children`` must equal the set of
    SUBSYSTEMS entries whose ``parent_hub == "games"`` — otherwise the
    Help "Includes:" line and the GamesHubView dropdown disagree.
    """
    games = get_hub("games")
    assert games is not None
    declared = set(games.primary_children)
    actual = {
        name for name, meta in SUBSYSTEMS.items() if meta.get("parent_hub") == "games"
    }
    assert (
        declared == actual
    ), f"Games primary_children {declared} != parent_hub filter {actual}"


def test_every_hub_primary_children_match_parent_hub_filter():
    """For every hub whose key is referenced by at least one
    subsystem's ``parent_hub``, the hub's ``primary_children`` must
    equal the set of subsystems pointing at it. Generalises the
    games-only check above so future PRs cannot silently drift
    metadata away from the hub declaration.
    """
    # Collect parent_hub references per hub key.
    parents: dict[str, set[str]] = {}
    for name, meta in SUBSYSTEMS.items():
        parent = meta.get("parent_hub")
        if parent is None:
            continue
        parents.setdefault(parent, set()).add(name)

    for hub_key, expected_children in parents.items():
        hub = get_hub(hub_key)
        assert hub is not None, (
            f"subsystem(s) {expected_children} point at hub {hub_key!r} but "
            f"no such hub exists in HUBS"
        )
        declared = set(hub.primary_children)
        assert declared == expected_children, (
            f"hub {hub_key!r}: primary_children {declared} != parent_hub "
            f"filter {expected_children}"
        )


def test_cross_link_children_reference_real_subsystems():
    """Every entry in any hub's ``cross_link_children`` must be a real
    subsystem key. Pins the contract for the Mining → Economy
    cross-link added in PR #3 and for any future cross-links.
    """
    for hub in HUBS:
        for child in hub.cross_link_children:
            assert child in SUBSYSTEMS, (
                f"hub {hub.key!r} declares cross_link_children {child!r} "
                f"which is not a valid SUBSYSTEMS key"
            )


# ---------------------------------------------------------------------------
# Tier visibility
# ---------------------------------------------------------------------------


def test_hubs_for_tier_user_sees_only_user_tier_hubs():
    """Normal users see Games + BTD6 + Economy + Community + Utility
    (user tier) but not Moderation (moderator) or
    Admin/Settings/Platform (administrator).
    """
    visible = {hub.key for hub in hubs_for_tier("user")}
    assert "games" in visible
    assert "btd6" in visible
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
    assert "btd6" in visible
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
        "btd6",
        "economy",
        "moderation",
        "community",
        "utility",
        "admin",
    }


def test_hubs_for_tier_owner_sees_all():
    visible = {hub.key for hub in hubs_for_tier("owner")}
    assert visible == {
        "games",
        "btd6",
        "economy",
        "moderation",
        "community",
        "utility",
        "admin",
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
