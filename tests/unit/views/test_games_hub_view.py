"""Unit tests for the Games hub view (Phase 3).

Covers:

* ``discover_game_children`` filters and orders correctly.
* ``build_games_hub_embed`` produces the expected sections.
* ``GamesHubView`` has exactly one select with the right options.
* ``attach_back_to_games_button`` adds a button and no-ops at the
  25-child cap.
* The select callback gracefully handles missing cog,
  missing ``build_help_menu_view`` hook, and exceptions from the hook.

The Games hub is a router — it never contains game logic — so the
tests assert on routing surfaces only.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from utils.subsystem_registry import SUBSYSTEMS
from views.games.hub import (
    _GROUP_ORDER,
    GamesHubView,
    _build_no_panel_embed,
    attach_back_to_games_button,
    build_games_hub_embed,
    discover_game_children,
)


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    return author


# ---------------------------------------------------------------------------
# discover_game_children
# ---------------------------------------------------------------------------


def test_discover_returns_only_parent_hub_games():
    names = [name for name, _ in discover_game_children()]
    # Every returned child must declare parent_hub == "games" in the registry.
    for name in names:
        assert SUBSYSTEMS[name].get("parent_hub") == "games", (
            f"discover_game_children returned {name!r} which is not a games child"
        )
    # And no games-tagged subsystem with parent_hub == "games" is missing.
    expected = {
        n for n, m in SUBSYSTEMS.items() if m.get("parent_hub") == "games"
    }
    assert set(names) == expected


def test_discover_groups_competitive_before_activities():
    children = discover_game_children()
    groups = [meta.get("hub_group") for _, meta in children]
    competitive_indices = [i for i, g in enumerate(groups) if g == "competitive"]
    activities_indices = [i for i, g in enumerate(groups) if g == "activities"]
    # Every competitive index must come before every activities index.
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
    assert keys == sorted(keys), f"discover_game_children is not deterministic: {keys}"


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
    # Either a literal typed shortcut OR an explicit "Typed shortcut" mention.
    assert (
        "!blackjack" in description
        or "!mine" in description
        or "Typed" in description
    ), description


# ---------------------------------------------------------------------------
# GamesHubView shape
# ---------------------------------------------------------------------------


def test_view_has_exactly_one_select():
    view = GamesHubView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1


def test_view_children_are_all_ui_items_not_tuples():
    """Regression: a previous bug stored the discovered child-meta list as
    ``self._children``, which collides with ``discord.ui.View``'s internal
    ``_children`` items list. That left raw tuples in ``view.children``,
    which crashed Discord-side serialization when the view was sent.
    """
    view = GamesHubView(_author())
    for child in view.children:
        assert isinstance(child, discord.ui.Item), (
            f"GamesHubView leaked a non-Item ({type(child).__name__}) "
            "into its children — this would crash when sent to Discord."
        )


def test_view_serializes_to_components_without_raising():
    """Regression: ``view.to_components()`` is the exact serialization
    Discord runs before sending a view. If a non-Item child leaks in,
    this raises and ``ctx.send(view=view)`` fails silently from the
    user's perspective. Pin the contract.
    """
    view = GamesHubView(_author())
    components = view.to_components()
    assert len(components) >= 1
    # Walk every serialized component to verify dict-like shape.
    for row in components:
        assert isinstance(row, dict)


def test_view_does_not_shadow_discord_internal_children_attr():
    """Regression: the GamesHubView used to set ``self._children`` directly,
    which is the same attribute name ``discord.ui.View`` uses for its
    internal items list. Pin that the view exposes its child-meta under
    a different attribute name.
    """
    view = GamesHubView(_author())
    # ``view.children`` (discord.py's property) returns the items list —
    # one ``_GamesHubSelect`` and nothing else.
    assert all(isinstance(c, discord.ui.Item) for c in view.children)
    # The view caches its discovered child-meta as well, but under a
    # name that does NOT collide with discord.py.
    assert not hasattr(view, "_children") or all(
        isinstance(c, discord.ui.Item) for c in view._children  # type: ignore[attr-defined]
    ), "GamesHubView._children must not hold raw tuples (collides with discord.ui.View)"


def test_view_has_no_built_in_back_button():
    """Back-to-Help is added by help_cog when surfaced from the help menu;
    direct ``!games`` invocation has no back nav (mirrors !countingmenu).
    """
    view = GamesHubView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert buttons == []


def test_select_options_cover_every_child():
    view = GamesHubView(_author())
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    option_values = {o.value for o in select.options}
    expected_values = {name for name, _ in discover_game_children()}
    assert option_values == expected_values


def test_select_options_carry_emoji_and_description():
    view = GamesHubView(_author())
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    for option in select.options:
        meta = SUBSYSTEMS[option.value]
        if meta.get("emoji"):
            # PartialEmoji.name preserves the unicode glyph
            actual = (
                option.emoji.name
                if option.emoji is not None
                else None
            )
            assert actual == meta["emoji"], (
                f"emoji for {option.value!r}: expected {meta['emoji']!r}, "
                f"got {actual!r}"
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
    # Fill view to exactly 25 children — Discord's hard cap.
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
# Select-callback routing
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

    with patch("views.games.hub.SUBSYSTEMS") as fake_subs:
        # Pick any real games child but make _cog_for_subsystem return None.
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

    with patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog):
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

    with patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog):
        await view.handle_select(interaction, "blackjack")

    interaction.response.edit_message.assert_awaited_once()
    args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is child_embed
    assert kwargs["view"] is child_view
    # The back-to-games button must have been attached to the child view.
    back_buttons = [
        c
        for c in child_view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "games:back"
    ]
    assert len(back_buttons) == 1


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
    assert embed.fields  # always shows a Commands field
    assert "No commands declared" in embed.fields[0].value
