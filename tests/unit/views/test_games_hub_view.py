"""Unit tests for the Games hub view.

PR 2 (Games Hub v2) replaced the legacy dropdown with direct game
buttons. The shape contract this file pins:

* ``discover_game_children`` filters and orders correctly.
* ``build_games_hub_embed`` produces the expected sections.
* ``GamesHubView`` renders one button per visible game child, grouped
  by ``hub_group`` (competitive on row 0 / primary style, activities
  on row 1 / success style).
* Every rendered hub button is actionable: not ``disabled``, no
  "coming soon" / placeholder labels.
* Component count stays safely below Discord's 25-component cap
  (worst case includes Back-to-Help added by ``HelpPanelView``).
* ``attach_back_to_games_button`` adds a button and no-ops at the cap.
* The child-open callback routes through
  ``GamesHubView.handle_select``, gracefully handling missing cog,
  missing ``build_help_menu_view`` hook, and exceptions from the hook.
* Click-time governance recheck fails closed for stale visibility.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from governance.models import VisibilityResult
from utils.subsystem_registry import SUBSYSTEMS
from views.games.hub import (
    _GROUP_ORDER,
    GamesHubView,
    _build_no_panel_embed,
    _GameHubButton,
    attach_back_to_games_button,
    build_games_hub_embed,
    discover_game_children,
)


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    return author


@contextmanager
def _all_visible():
    """Stub resolve_visibility to return every subsystem visible.

    Click-time recheck inside ``handle_select`` and the rebuilt-hub
    path inside ``attach_back_to_games_button`` go through
    ``build_games_hub_panel`` which resolves governance; tests that
    aren't designed to exercise the gating need a stub so the factory
    doesn't hit the real DB.
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
# discover_game_children
# ---------------------------------------------------------------------------


def test_discover_returns_only_parent_hub_games():
    names = [name for name, _ in discover_game_children()]
    for name in names:
        assert SUBSYSTEMS[name].get("parent_hub") == "games", (
            f"discover_game_children returned {name!r} which is not a games child"
        )
    expected = {
        n for n, m in SUBSYSTEMS.items() if m.get("parent_hub") == "games"
    }
    assert set(names) == expected


def test_discover_groups_competitive_before_activities():
    children = discover_game_children()
    groups = [meta.get("hub_group") for _, meta in children]
    competitive_indices = [i for i, g in enumerate(groups) if g == "competitive"]
    activities_indices = [i for i, g in enumerate(groups) if g == "activities"]
    if competitive_indices and activities_indices:
        assert max(competitive_indices) < min(activities_indices), (
            f"groups out of order: {groups}"
        )


def test_discover_is_deterministic():
    """Order must be ``(group_rank, ui_priority, key)`` — fully deterministic."""
    children = discover_game_children()
    keys = [
        (
            _GROUP_ORDER.get(meta.get("hub_group") or "", 99),
            meta.get("ui_priority", 99),
            name,
        )
        for name, meta in children
    ]
    assert keys == sorted(keys), (
        f"discover_game_children is not deterministic: {keys}"
    )


# ---------------------------------------------------------------------------
# build_games_hub_embed
# ---------------------------------------------------------------------------


def test_embed_has_competitive_and_activities_sections():
    embed = build_games_hub_embed()
    field_names = [f.name for f in embed.fields]
    assert any("Competitive" in n for n in field_names), field_names
    assert any("Activities" in n for n in field_names), field_names


def test_embed_title_and_color():
    embed = build_games_hub_embed()
    assert embed.title is not None
    assert "Games" in embed.title
    assert embed.color is not None


def test_embed_mentions_typed_shortcuts_in_description():
    """Operators must still know typed commands work after the hub lands."""
    embed = build_games_hub_embed()
    description = embed.description or ""
    assert (
        "!blackjack" in description
        or "!mine" in description
        or "Typed" in description
    ), description


# ---------------------------------------------------------------------------
# GamesHubView shape — PR 2 button-based layout
# ---------------------------------------------------------------------------


def test_view_has_no_select_components():
    """PR 2 replaced the dropdown with direct buttons — no select stays."""
    view = GamesHubView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert selects == [], (
        "Games Hub v2 uses buttons exclusively; the legacy "
        "_GamesHubSelect dropdown was removed in PR 2."
    )


def test_view_renders_one_game_hub_button_per_visible_child():
    view = GamesHubView(_author())
    buttons = [c for c in view.children if isinstance(c, _GameHubButton)]
    subsystems = {b._subsystem for b in buttons}  # type: ignore[attr-defined]
    expected = {name for name, _ in discover_game_children()}
    assert subsystems == expected


def test_view_children_are_all_ui_items_not_tuples():
    """Regression: a previous bug stored the discovered child-meta list as
    ``self._children``, which collides with ``discord.ui.View``'s internal
    items list.
    """
    view = GamesHubView(_author())
    for child in view.children:
        assert isinstance(child, discord.ui.Item), (
            f"GamesHubView leaked a non-Item ({type(child).__name__}) "
            "into its children — this would crash when sent to Discord."
        )


def test_view_serializes_to_components_without_raising():
    """``view.to_components()`` is the exact serialization Discord runs
    before sending a view. If a non-Item child leaks in, this raises
    and ``ctx.send(view=view)`` fails silently from the user's
    perspective.
    """
    view = GamesHubView(_author())
    components = view.to_components()
    assert len(components) >= 1
    for row in components:
        assert isinstance(row, dict)


def test_view_does_not_shadow_discord_internal_children_attr():
    view = GamesHubView(_author())
    assert all(isinstance(c, discord.ui.Item) for c in view.children)
    assert not hasattr(view, "_children") or all(
        isinstance(c, discord.ui.Item)
        for c in view._children  # type: ignore[attr-defined]
    ), "GamesHubView._children must not hold raw tuples"


def test_view_has_no_built_in_back_to_help_button():
    """Back-to-Help is added by HelpPanelView when surfaced from the
    help menu; direct ``!games`` invocation has no back nav (mirrors
    ``!countingmenu``).
    """
    view = GamesHubView(_author())
    back_labels = [
        (c.label or "")
        for c in view.children
        if isinstance(c, discord.ui.Button) and "Back" in (c.label or "")
    ]
    assert back_labels == [], (
        f"Games hub should not include a built-in Back button: {back_labels}"
    )


# ---------------------------------------------------------------------------
# Button row + style layout
# ---------------------------------------------------------------------------


def test_competitive_buttons_on_row_0_with_primary_style():
    view = GamesHubView(_author())
    for btn in view.children:
        if not isinstance(btn, _GameHubButton):
            continue
        meta = SUBSYSTEMS[btn._subsystem]  # type: ignore[attr-defined]
        if meta.get("hub_group") == "competitive":
            assert btn.row == 0, (
                f"competitive button {btn._subsystem!r} on row {btn.row}"  # type: ignore[attr-defined]
            )
            assert btn.style is discord.ButtonStyle.primary


def test_activities_buttons_on_row_1_with_success_style():
    view = GamesHubView(_author())
    for btn in view.children:
        if not isinstance(btn, _GameHubButton):
            continue
        meta = SUBSYSTEMS[btn._subsystem]  # type: ignore[attr-defined]
        if meta.get("hub_group") == "activities":
            assert btn.row == 1, (
                f"activities button {btn._subsystem!r} on row {btn.row}"  # type: ignore[attr-defined]
            )
            assert btn.style is discord.ButtonStyle.success


def test_button_labels_come_from_registry_metadata():
    """Labels must use ``{emoji} {display_name}`` from the registry."""
    view = GamesHubView(_author())
    for btn in view.children:
        if not isinstance(btn, _GameHubButton):
            continue
        meta = SUBSYSTEMS[btn._subsystem]  # type: ignore[attr-defined]
        expected = f"{meta.get('emoji', '')} {meta.get('display_name', '')}".strip()
        assert btn.label == expected[:80], (
            f"button {btn._subsystem!r} label {btn.label!r} does not "  # type: ignore[attr-defined]
            f"match registry metadata {expected!r}"
        )


def test_button_custom_ids_are_stable_and_namespaced():
    view = GamesHubView(_author())
    expected = {f"games:open:{name}" for name, _ in discover_game_children()}
    actual = {
        c.custom_id
        for c in view.children
        if isinstance(c, _GameHubButton)
    }
    assert actual == expected


# ---------------------------------------------------------------------------
# PR 2 actionability + no-placeholder + component count
# ---------------------------------------------------------------------------


def test_every_hub_button_is_actionable_not_disabled():
    """No rendered Games Hub button may be ``disabled=True`` — placeholder
    or "coming soon" buttons are forbidden by §2.9 of the operating
    contract.
    """
    view = GamesHubView(_author())
    for btn in view.children:
        if not isinstance(btn, discord.ui.Button):
            continue
        assert btn.disabled is False, (
            f"Games Hub button {btn.label!r} (custom_id={btn.custom_id!r}) "
            "is disabled — placeholder buttons are forbidden."
        )


def test_no_placeholder_or_coming_soon_labels():
    """No "Coming Soon" / "TODO" / "WIP" / "Placeholder" labels."""
    forbidden_tokens = ("coming soon", "todo", "wip", "placeholder", "tbd")
    view = GamesHubView(_author())
    for btn in view.children:
        if not isinstance(btn, discord.ui.Button):
            continue
        lower = (btn.label or "").lower()
        for token in forbidden_tokens:
            assert token not in lower, (
                f"Games Hub button label {btn.label!r} contains forbidden "
                f"placeholder token {token!r}."
            )


def test_component_count_is_under_discord_cap():
    """Components per view ≤ 25 (Discord hard cap), including the
    worst-case scenario where ``HelpPanelView`` appends Back-to-Help
    when opening via Help.
    """
    view = GamesHubView(_author())
    # Add one extra child to simulate Back-to-Help.
    view.add_item(
        discord.ui.Button(
            label="↩ Back to Help",
            style=discord.ButtonStyle.secondary,
            custom_id="help:back",
            row=4,
        ),
    )
    assert len(view.children) <= 25, (
        f"Games hub + Back-to-Help has {len(view.children)} components, "
        "exceeds Discord's 25-component cap."
    )


# ---------------------------------------------------------------------------
# attach_back_to_games_button
# ---------------------------------------------------------------------------


def test_attach_back_button_adds_one_button():
    view = discord.ui.View()
    added = attach_back_to_games_button(view, _author())
    assert added is True
    assert len(view.children) == 1
    button = view.children[0]
    assert isinstance(button, discord.ui.Button)
    assert button.label == "↩ Back to Games"
    assert button.custom_id == "games:back"
    assert button.row == 4


def test_attach_back_button_noops_at_25_children():
    view = discord.ui.View()
    for i in range(25):
        view.add_item(
            discord.ui.Button(
                label=f"b{i}",
                custom_id=f"filler:{i}",
                style=discord.ButtonStyle.secondary,
                row=i // 5,
            ),
        )
    added = attach_back_to_games_button(view, _author())
    assert added is False
    assert len(view.children) == 25


# ---------------------------------------------------------------------------
# handle_select routing (shared by every _GameHubButton)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_select_unknown_subsystem_sends_ephemeral():
    view = GamesHubView(_author())
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    await view.handle_select(interaction, "not_a_real_subsystem")

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_select_missing_cog_renders_fallback():
    view = GamesHubView(_author())
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    with _all_visible(), patch("views.games.hub.SUBSYSTEMS") as fake_subs:
        sub_name = "blackjack"
        fake_subs.get.return_value = dict(SUBSYSTEMS[sub_name])
        with patch("cogs.help_cog._cog_for_subsystem", return_value=None):
            await view.handle_select(interaction, sub_name)

    interaction.response.edit_message.assert_awaited_once()
    args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["view"] is view  # falls back to the hub itself + back btn
    embed: discord.Embed = kwargs["embed"]
    assert "Blackjack" in (embed.title or "")


@pytest.mark.asyncio
async def test_handle_select_hook_failure_renders_fallback():
    view = GamesHubView(_author())
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(side_effect=RuntimeError("boom"))

    with _all_visible(), patch(
        "cogs.help_cog._cog_for_subsystem", return_value=fake_cog
    ):
        await view.handle_select(interaction, "blackjack")

    interaction.response.edit_message.assert_awaited_once()
    fake_cog.build_help_menu_view.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_select_success_attaches_back_button():
    view = GamesHubView(_author())
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    child_view = discord.ui.View()
    child_embed = discord.Embed(title="Blackjack")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(child_embed, child_view))

    with _all_visible(), patch(
        "cogs.help_cog._cog_for_subsystem", return_value=fake_cog
    ):
        await view.handle_select(interaction, "blackjack")

    interaction.response.edit_message.assert_awaited_once()
    args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is child_embed
    assert kwargs["view"] is child_view
    back_buttons = [
        c
        for c in child_view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "games:back"
    ]
    assert len(back_buttons) == 1


@pytest.mark.asyncio
async def test_button_callback_delegates_to_handle_select():
    """Clicking a ``_GameHubButton`` must call
    ``GamesHubView.handle_select`` with its bound subsystem — that is
    how it shares the routing brain with the legacy dropdown's path.
    """
    view = GamesHubView(_author())
    btn = next(
        c
        for c in view.children
        if isinstance(c, _GameHubButton) and c._subsystem == "blackjack"  # type: ignore[attr-defined]
    )
    interaction = MagicMock(spec=discord.Interaction)
    with patch.object(
        GamesHubView,
        "handle_select",
        new=AsyncMock(),
    ) as mock_handle:
        await btn.callback(interaction)
    mock_handle.assert_awaited_once_with(interaction, "blackjack")


# ---------------------------------------------------------------------------
# Fallback embed
# ---------------------------------------------------------------------------


def test_build_no_panel_embed_lists_entry_points():
    embed = _build_no_panel_embed("blackjack", dict(SUBSYSTEMS["blackjack"]))
    field_values = [f.value for f in embed.fields]
    text = "\n".join(field_values)
    for ep in SUBSYSTEMS["blackjack"]["entry_points"]:
        assert f"!{ep}" in text


def test_build_no_panel_embed_handles_empty_entry_points():
    fake_meta = {
        "display_name": "Empty",
        "description": "",
        "entry_points": (),
        "emoji": "🧪",
    }
    embed = _build_no_panel_embed("empty", fake_meta)
    assert embed.fields
    assert "No commands declared" in embed.fields[0].value


# ---------------------------------------------------------------------------
# Back-to-Games click-time behaviour (S2 migration)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_back_button_callback_rebuilds_games_hub_with_original_author():
    """Clicking ↩ Back to Games must rebuild ``GamesHubView`` with the
    same author the panel was opened by.
    """
    author = _author(id_=42)
    view = discord.ui.View()
    attach_back_to_games_button(view, author)

    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.edit_original_response = AsyncMock()

    btn = next(c for c in view.children if isinstance(c, discord.ui.Button))
    with _all_visible():
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    rebuilt = kwargs["view"]
    assert isinstance(rebuilt, GamesHubView)
    assert rebuilt._author is author


def test_attach_back_to_games_button_delegates_to_shared_helper():
    """Migration pin (S2): ``attach_back_to_games_button`` must call
    into ``views.navigation.attach_back_button``.
    """
    import inspect

    from views.games import hub as games_hub

    fn_src = inspect.getsource(games_hub.attach_back_to_games_button)
    module_src = inspect.getsource(games_hub)
    assert "attach_back_button" in fn_src
    assert "from views.navigation" in module_src or "views.navigation" in fn_src


# ---------------------------------------------------------------------------
# Governance filtering and click-time recheck
# ---------------------------------------------------------------------------


def test_view_falls_back_to_unfiltered_when_children_omitted():
    """Backward-compat: ``GamesHubView(author)`` still works for tests
    and persistent re-registration that can't await the factory.
    """
    view = GamesHubView(_author())
    button_subsystems = {
        c._subsystem  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, _GameHubButton)
    }
    expected = {name for name, _ in discover_game_children()}
    assert button_subsystems == expected


def test_view_uses_pre_filtered_children_when_supplied():
    """The factory passes ``children`` so only visible subsystems
    appear as buttons.
    """
    only = [(name, dict(SUBSYSTEMS[name])) for name in ("blackjack",)]
    view = GamesHubView(_author(), children=only)
    button_subsystems = {
        c._subsystem  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, _GameHubButton)
    }
    assert button_subsystems == {"blackjack"}


@pytest.mark.asyncio
async def test_build_games_hub_panel_filters_via_visible_set():
    from views.games.hub import build_games_hub_panel

    _embed, view = await build_games_hub_panel(
        _author(),
        visible={"blackjack"},
    )
    button_subsystems = {
        c._subsystem  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, _GameHubButton)
    }
    assert button_subsystems == {"blackjack"}


@pytest.mark.asyncio
async def test_build_games_hub_panel_resolves_when_visible_none():
    from views.games.hub import build_games_hub_panel

    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = _author()
    interaction.guild_id = 7
    interaction.channel = MagicMock()

    vis_result = VisibilityResult(
        visible_subsystems={"blackjack"},
        member_tier="moderator",
        resolved_from={},
        traces={},
    )
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ) as mock_resolve:
        _embed, view = await build_games_hub_panel(
            _author(),
            interaction=interaction,
        )

    mock_resolve.assert_awaited_once()
    button_subsystems = {
        c._subsystem  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, _GameHubButton)
    }
    assert button_subsystems == {"blackjack"}


@pytest.mark.asyncio
async def test_build_games_hub_panel_raises_without_context():
    from views.games.hub import build_games_hub_panel

    with pytest.raises(ValueError, match="interaction or ctx"):
        await build_games_hub_panel(_author())


@pytest.mark.asyncio
async def test_handle_select_fails_closed_when_subsystem_invisible():
    """Click-time recheck: if a subsystem drops out of visibility
    between render and click, ``handle_select`` must surface an
    ephemeral and NOT call into the cog.
    """
    view = GamesHubView(_author())
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.user = _author()
    interaction.guild_id = 7
    interaction.channel = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    vis_result = VisibilityResult(
        visible_subsystems=set(),
        member_tier="member",
        resolved_from={},
        traces={},
    )
    cog_lookup = MagicMock()
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ), patch("cogs.help_cog._cog_for_subsystem", cog_lookup):
        await view.handle_select(interaction, "blackjack")

    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    message = args[0] if args else kwargs.get("content", "")
    assert "no longer available" in message
    assert kwargs.get("ephemeral") is True
    cog_lookup.assert_not_called()
    interaction.response.edit_message.assert_not_called()
