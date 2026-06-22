"""Unit tests for the Community hub view (S9 + PR #4).

Pins the metadata-driven v2 behaviour:

- Primary children discovered from ``SUBSYSTEMS`` where
  ``parent_hub == "community"`` (xp + role today).
- Cross-link children discovered from
  ``hub_registry.get_hub("community").cross_link_children``
  (counting + chain + leaderboard today).
- Buttons follow the hub-ui-standard layout: primary on row 0 with
  primary style, cross-links on row 1 with secondary style.
- Stable custom_ids in ``community:open:<subsystem>`` form.
- Labels come from registry metadata (emoji + display_name) — not
  view-local hardcoded strings.
- Failure paths surface as ephemerals; the message is never left
  half-edited.

The hub is nav-only — no DB writes, no game logic, no governance
resolution.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from governance.models import VisibilityResult
from utils.hub_registry import get_hub
from utils.subsystem_registry import SUBSYSTEMS
from views.community.hub import (
    CommunityHubView,
    _CommunityChildButton,
    build_community_hub_embed,
    discover_community_children,
)


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    return author


def _interaction() -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


@contextmanager
def _all_visible():
    """Patch resolve_visibility to return every subsystem visible.

    PR D added a click-time recheck inside
    ``_CommunityChildButton.callback`` that hits
    ``governance_service.resolve_visibility`` before delegating to the
    target cog. Existing button-callback tests assume the recheck
    passes; without this stub the recheck tries to hit the DB.
    """
    vis_result = VisibilityResult(
        visible_subsystems=set(SUBSYSTEMS),
        member_tier="moderator",
        resolved_from={},
        traces={},
    )
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ):
        yield


# ---------------------------------------------------------------------------
# discover_community_children — metadata-driven discovery
# ---------------------------------------------------------------------------


def test_discover_primary_comes_from_parent_hub_metadata():
    """Primary children must equal the set of SUBSYSTEMS entries with
    ``parent_hub == "community"`` — never a hardcoded view-local list.
    """
    primary, _cross = discover_community_children()
    primary_keys = {name for name, _meta in primary}
    expected = {
        name
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == "community"
    }
    assert primary_keys == expected


def test_discover_cross_link_comes_from_hub_registry():
    """Cross-links must equal the HubEntry.cross_link_children tuple —
    never a hardcoded view-local list.
    """
    _primary, cross = discover_community_children()
    cross_keys = [name for name, _meta in cross]
    hub = get_hub("community")
    assert hub is not None
    assert tuple(cross_keys) == hub.cross_link_children


def test_discover_primary_sorted_by_ui_priority_then_key():
    """Ordering must be deterministic — ui_priority ascending, then key
    ascending — so the button layout doesn't drift across imports.
    """
    primary, _cross = discover_community_children()
    keys = [(meta.get("ui_priority", 99), name) for name, meta in primary]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_embed_lists_all_five_children():
    embed = build_community_hub_embed()
    description = embed.description or ""
    # Match by display_name as registered today; this catches metadata
    # drift but not styling tweaks to the description.
    for key in ("xp", "role", "counting", "chain", "leaderboard"):
        display = SUBSYSTEMS[key]["display_name"]
        assert (
            display in description
        ), f"{key!r} display_name {display!r} missing from embed description"


def test_embed_title_and_color():
    embed = build_community_hub_embed()
    assert "Community" in (embed.title or "")
    assert embed.color is not None


def test_embed_section_headings_present():
    """The Progression / Community games & standings headings are
    hardcoded framing and must remain so a registry-only edit doesn't
    silently collapse the layout.
    """
    embed = build_community_hub_embed()
    description = embed.description or ""
    assert "**Progression**" in description
    assert "**Community games & standings**" in description


# ---------------------------------------------------------------------------
# View shape — six buttons routing to the six child subsystems
# ---------------------------------------------------------------------------


def test_view_has_nine_child_buttons():
    # 6 primary (xp, karma, community_spotlight, welcome, counters, role) +
    # 3 cross-link (counting, chain, leaderboard) = 9 children when unfiltered.
    # Karma (parent_hub="community") was added 2026-06-22; the view wraps
    # primaries past the 5-per-row Discord cap onto a second row.
    view = CommunityHubView(_author())
    buttons = [c for c in view.children if isinstance(c, _CommunityChildButton)]
    assert len(buttons) == 9


def test_buttons_cover_each_target_subsystem():
    view = CommunityHubView(_author())
    subsystems = {
        btn._subsystem  # type: ignore[attr-defined]
        for btn in view.children
        if isinstance(btn, _CommunityChildButton)
    }
    assert subsystems == {
        "xp",
        "karma",
        "community_spotlight",
        "role",
        "welcome",
        "counters",
        "counting",
        "chain",
        "leaderboard",
    }


def test_button_custom_ids_are_stable_and_namespaced():
    view = CommunityHubView(_author())
    ids = {c.custom_id for c in view.children if isinstance(c, _CommunityChildButton)}
    assert ids == {
        "community:open:xp",
        "community:open:karma",
        "community:open:community_spotlight",
        "community:open:role",
        "community:open:welcome",
        "community:open:counters",
        "community:open:counting",
        "community:open:chain",
        "community:open:leaderboard",
    }


def test_primaries_wrap_then_cross_links_follow():
    """Primary children (parent_hub="community") fill rows from 0 at 5/row
    (Discord's cap); cross-links (Counting/Chain/Leaderboard, declared in
    hub_registry.cross_link_children) follow on the next free row. With 6
    primaries (xp, karma, community_spotlight, welcome, counters, role) that
    is row 0 (5) + row 1 (1), then cross-links on row 2.
    """
    view = CommunityHubView(_author())

    def _row(n: int) -> set[str]:
        return {
            btn._subsystem  # type: ignore[attr-defined]
            for btn in view.children
            if isinstance(btn, _CommunityChildButton) and btn.row == n
        }

    assert _row(0) == {"xp", "karma", "community_spotlight", "welcome", "counters"}
    assert _row(1) == {"role"}
    assert _row(2) == {"counting", "chain", "leaderboard"}
    # No row exceeds Discord's 5-button cap.
    for n in range(5):
        assert len(_row(n)) <= 5


def test_primaries_use_primary_style_cross_links_use_secondary():
    """Layout convention: primary children are visually highlighted (primary
    style); cross-links recede (secondary style) — regardless of which row
    they wrap onto.
    """
    primary, cross_link = discover_community_children()
    primary_names = {name for name, _ in primary}
    cross_names = {name for name, _ in cross_link}

    view = CommunityHubView(_author())
    for btn in view.children:
        if not isinstance(btn, _CommunityChildButton):
            continue
        sub = btn._subsystem  # type: ignore[attr-defined]
        if sub in primary_names:
            assert btn.style is discord.ButtonStyle.primary, sub
        elif sub in cross_names:
            assert btn.style is discord.ButtonStyle.secondary, sub


def test_button_labels_come_from_registry_metadata():
    """Labels must use the subsystem's registered emoji + display_name,
    not a hardcoded view-local string. PR #4 removed the literal label
    table; this test pins the new contract.
    """
    view = CommunityHubView(_author())
    for btn in view.children:
        if not isinstance(btn, _CommunityChildButton):
            continue
        key = btn._subsystem  # type: ignore[attr-defined]
        meta = SUBSYSTEMS[key]
        expected = f"{meta['emoji']} {meta['display_name']}"
        assert btn.label == expected, (
            f"button {key!r} label {btn.label!r} does not match registry "
            f"metadata {expected!r}"
        )


# ---------------------------------------------------------------------------
# Button callback routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_button_opens_host_cog_panel_in_place():
    """Clicking a Community child button must open the host cog's
    panel AND attach Back-to-Community so the user can return.

    PR 2: this is the fix for the long-standing asymmetry where the
    Games hub attached the back button after a successful child build
    but the Community hub did not, leaving the user without a back
    nav from any Community child panel.
    """
    parent_view = CommunityHubView(_author(id_=42))
    button = next(
        c
        for c in parent_view.children
        if isinstance(c, _CommunityChildButton) and c._subsystem == "xp"  # type: ignore[attr-defined]
    )
    fake_cog = MagicMock()
    fake_embed = discord.Embed(title="XP")
    fake_view = discord.ui.View()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))

    interaction = _interaction()
    with (
        _all_visible(),
        patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog),
    ):
        await button.callback(interaction)

    fake_cog.build_help_menu_view.assert_awaited_once_with(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is fake_embed
    assert kwargs["view"] is fake_view
    # Back-to-Community must have been attached to the child view.
    back_buttons = [
        c
        for c in fake_view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "community:back"
    ]
    assert len(back_buttons) == 1, (
        "Community child panel must have Back-to-Community attached — "
        "this is the navigation symmetry fix from PR 2."
    )


@pytest.mark.asyncio
async def test_child_panel_preserves_back_to_help_chain():
    """AB2 back-chain: when the Community hub carries a Help back-target (it
    was opened from !help), a child panel must get BOTH Back-to-Community AND
    Back-to-Help — mirroring the Games hub. Without this, a Help → Community →
    child → back round-trip silently dropped Back-to-Help.
    """
    from views.navigation import BackTarget

    parent_view = CommunityHubView(_author(id_=42))

    async def _fake_help_parent(_interaction):
        return discord.Embed(title="Help"), discord.ui.View()

    parent_view._back_target = BackTarget(
        builder=_fake_help_parent,
        label="↩ Back to Help",
        custom_id="help:back",
    )
    button = next(
        c
        for c in parent_view.children
        if isinstance(c, _CommunityChildButton) and c._subsystem == "xp"  # type: ignore[attr-defined]
    )
    fake_cog = MagicMock()
    fake_view = discord.ui.View()
    fake_cog.build_help_menu_view = AsyncMock(
        return_value=(discord.Embed(title="XP"), fake_view),
    )

    interaction = _interaction()
    with (
        _all_visible(),
        patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog),
    ):
        await button.callback(interaction)

    custom_ids = {
        c.custom_id for c in fake_view.children if isinstance(c, discord.ui.Button)
    }
    assert "community:back" in custom_ids
    assert (
        "help:back" in custom_ids
    ), "child opened from a Help-rooted Community hub must keep Back-to-Help"
    # The back-chain propagates so deeper navigation can keep unwinding.
    assert getattr(fake_view, "_back_target", None) is parent_view._back_target


@pytest.mark.asyncio
async def test_button_missing_cog_sends_ephemeral():
    button = _CommunityChildButton(
        subsystem="xp",
        label="🏆 XP",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    interaction = _interaction()
    with _all_visible(), patch("cogs.help_cog._cog_for_subsystem", return_value=None):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_button_cog_without_hook_sends_ephemeral():
    button = _CommunityChildButton(
        subsystem="xp",
        label="🏆 XP",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    fake_cog = MagicMock(spec=[])  # no build_help_menu_view attr
    interaction = _interaction()
    with (
        _all_visible(),
        patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog),
    ):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_button_hook_exception_sends_ephemeral():
    button = _CommunityChildButton(
        subsystem="xp",
        label="🏆 XP",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(side_effect=RuntimeError("boom"))
    interaction = _interaction()
    with (
        _all_visible(),
        patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog),
    ):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


# ---------------------------------------------------------------------------
# Doctrine: hub is nav-only
# ---------------------------------------------------------------------------


def test_view_contains_no_select_components():
    """The Community hub uses buttons exclusively — five children fit
    under the hub-ui-standard ≤8-button threshold.
    """
    view = CommunityHubView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert selects == []


# ---------------------------------------------------------------------------
# PR D — Governance filtering and click-time recheck
# ---------------------------------------------------------------------------


def test_view_falls_back_to_unfiltered_when_lists_omitted():
    """Backward-compat: ``CommunityHubView(author)`` still works for
    tests and persistent re-registration paths that can't await the
    factory. Click-time recheck remains the safety net.
    """
    view = CommunityHubView(_author())
    buttons = {
        c._subsystem  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, _CommunityChildButton)
    }
    # All nine children rendered when nothing is filtered (karma added under
    # Community 2026-06-22; welcome + counters homed here by PR #1290).
    assert buttons == {
        "xp",
        "karma",
        "community_spotlight",
        "role",
        "welcome",
        "counters",
        "counting",
        "chain",
        "leaderboard",
    }


def test_view_uses_pre_filtered_lists_when_supplied():
    """The factory passes ``primary`` and ``cross_link`` so only
    visible subsystems render. Pin the constructor honors the filter.
    """
    primary = [("xp", dict(SUBSYSTEMS["xp"]))]
    cross_link = [("leaderboard", dict(SUBSYSTEMS["leaderboard"]))]
    view = CommunityHubView(
        _author(),
        primary=primary,
        cross_link=cross_link,
    )
    buttons = {
        c._subsystem  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, _CommunityChildButton)
    }
    assert buttons == {"xp", "leaderboard"}


@pytest.mark.asyncio
async def test_build_community_hub_panel_filters_via_visible_set():
    from views.community.hub import build_community_hub_panel

    _embed, view = await build_community_hub_panel(
        _author(),
        visible={"xp", "leaderboard"},
    )
    buttons = {
        c._subsystem  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, _CommunityChildButton)
    }
    assert buttons == {"xp", "leaderboard"}


@pytest.mark.asyncio
async def test_build_community_hub_panel_resolves_when_visible_none():
    """The factory must call governance once when ``visible`` is None."""
    from views.community.hub import build_community_hub_panel

    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = _author()
    interaction.guild_id = 7
    interaction.channel = MagicMock()

    vis_result = VisibilityResult(
        visible_subsystems={"xp"},
        member_tier="moderator",
        resolved_from={},
        traces={},
    )
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ) as mock_resolve:
        _embed, view = await build_community_hub_panel(
            _author(),
            interaction=interaction,
        )

    mock_resolve.assert_awaited_once()
    buttons = {
        c._subsystem  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, _CommunityChildButton)
    }
    assert buttons == {"xp"}


@pytest.mark.asyncio
async def test_button_fails_closed_when_subsystem_invisible():
    """Click-time recheck: if a subsystem drops out of visibility
    between render and click, the button must surface an ephemeral
    and NOT call into the cog.
    """
    button = _CommunityChildButton(
        subsystem="xp",
        label="🏆 XP",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    interaction = _interaction()
    interaction.user = _author()
    interaction.guild_id = 7
    interaction.channel = MagicMock()

    vis_result = VisibilityResult(
        visible_subsystems=set(),  # xp not visible anymore
        member_tier="member",
        resolved_from={},
        traces={},
    )
    cog_lookup = MagicMock()
    with (
        patch(
            "services.governance_service.resolve_visibility",
            new_callable=AsyncMock,
            return_value=vis_result,
        ),
        patch("cogs.help_cog._cog_for_subsystem", cog_lookup),
    ):
        await button.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    message = args[0] if args else kwargs.get("content", "")
    assert "no longer available" in message
    assert kwargs.get("ephemeral") is True
    cog_lookup.assert_not_called()
    interaction.response.edit_message.assert_not_called()


def test_attach_back_to_community_button_adds_back_button():
    """Symmetry pin: a back-to-community helper must exist for child
    panels opened from the hub, mirroring back-to-games.
    """
    from views.community.hub import attach_back_to_community_button

    view = discord.ui.View()
    added = attach_back_to_community_button(view, _author())
    assert added is True
    btn = next(c for c in view.children if isinstance(c, discord.ui.Button))
    assert btn.label == "↩ Back to Community"
    assert btn.custom_id == "community:back"
