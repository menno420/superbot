"""Tests for the reaction-roles refinement views (owner direction, 2026-06-21).

Two behaviours, both CI-safe with no Discord gateway:

* ``_BindEmotesView`` binds **several emotes on one message, each to its own
  role**, walking the typed emotes in order.
* ``RoleMenuBuilder.from_menu(as_copy=True)`` loads a saved menu as a **duplicate**
  — id dropped so Post creates a new menu, title marked, options carried over.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord
import pytest

from views.roles import reaction_panel
from views.roles.role_menu_builder import _AdvancedView, RoleMenuBuilder


class _FakeRole:
    def __init__(self, rid: int, name: str = "Role") -> None:
        self.id = rid
        self.name = name

    def is_default(self) -> bool:
        return False


def _panel(roles: list[_FakeRole]) -> SimpleNamespace:
    guild = SimpleNamespace(id=1, roles=roles)
    ctx = SimpleNamespace(author=SimpleNamespace(id=42), guild=guild)
    return SimpleNamespace(ctx=ctx, _rerender=AsyncMock())


@pytest.mark.asyncio
async def test_bind_emotes_view_binds_each_emote_to_its_own_role() -> None:
    panel = _panel([_FakeRole(10, "A"), _FakeRole(20, "B")])
    view = reaction_panel._BindEmotesView(panel, 555, ["💀", "❤️"])
    # The first prompt names the first emote + its position in the run.
    assert "💀" in view.prompt()
    assert "1/2" in view.prompt()

    interaction = SimpleNamespace(
        user=SimpleNamespace(id=42),
        response=SimpleNamespace(edit_message=AsyncMock()),
        edit_original_response=AsyncMock(),
        channel=SimpleNamespace(),  # not Messageable → reaction-seeding is skipped
    )

    with (
        patch("services.reaction_role_service.bind_emoji", new=AsyncMock()) as bind,
        patch.object(
            reaction_panel.resources,
            "resolve_role",
            side_effect=lambda guild, role_id: _FakeRole(role_id, f"R{role_id}"),
        ),
    ):
        await view._on_pick(interaction, 10)  # 💀 → role 10, advance
        assert view.index == 1
        assert "❤️" in view.prompt()
        await view._on_pick(interaction, 20)  # ❤️ → role 20, finish

    assert bind.await_count == 2
    assert bind.await_args_list[0].args == (1, 555, "💀", 10)
    assert bind.await_args_list[1].args == (1, 555, "❤️", 20)
    panel._rerender.assert_awaited_once()


def test_from_menu_as_copy_drops_id_marks_title_and_keeps_config() -> None:
    guild = SimpleNamespace(id=1)
    menu = {
        "menu_id": 5,
        "channel_id": 9,
        "title": "Colour Roles",
        "description": "Pick one",
        "style": "dropdown",
        "mode": "unique",
        "max_roles": 2,
        "theme": "pastel",
    }
    options = [SimpleNamespace(role_id=10), SimpleNamespace(role_id=20)]

    builder = RoleMenuBuilder.from_menu(
        SimpleNamespace(id=42),
        guild,
        menu,
        options,
        as_copy=True,
        channel=SimpleNamespace(id=99),  # post the copy here, not the original channel
    )

    # No id → the builder's Post creates a NEW menu; original is untouched.
    assert builder.menu_id is None
    assert builder.title == "Colour Roles (copy)"
    assert builder.role_ids == [10, 20]
    assert builder.mode == "unique"
    assert builder.max_roles == 2
    assert builder.channel.id == 99


def test_from_menu_edit_keeps_id() -> None:
    # The default (edit) path still loads the menu for in-place update.
    guild = SimpleNamespace(id=1)
    menu = {
        "menu_id": 5,
        "channel_id": 9,
        "title": "Game Roles",
        "description": None,
        "style": "button",
        "mode": "normal",
        "max_roles": 0,
        "theme": "game",
    }
    builder = RoleMenuBuilder.from_menu(
        SimpleNamespace(id=42),
        guild,
        menu,
        [SimpleNamespace(role_id=10)],
        channel=SimpleNamespace(id=9),
    )
    assert builder.menu_id == 5
    assert builder.title == "Game Roles"


def _counter_builder(show_counts: bool = False) -> RoleMenuBuilder:
    guild = SimpleNamespace(id=1, features=[])
    builder = RoleMenuBuilder(SimpleNamespace(id=42), guild, None)
    builder.show_counts = show_counts
    return builder


def test_builder_preview_shows_signup_counts_state() -> None:
    off = _counter_builder(False).build_embed()
    settings = next(f for f in off.fields if f.name == "Settings")
    assert "Sign-up counts: **off**" in settings.value

    on = _counter_builder(True).build_embed()
    settings = next(f for f in on.fields if f.name == "Settings")
    assert "Sign-up counts: **on**" in settings.value


def test_from_menu_loads_show_counts() -> None:
    guild = SimpleNamespace(id=1)
    menu = {
        "menu_id": 5,
        "channel_id": 9,
        "title": "RSVP",
        "description": None,
        "style": "button",
        "mode": "unique",
        "max_roles": 0,
        "theme": "announcement",
        "show_counts": True,
    }
    builder = RoleMenuBuilder.from_menu(
        SimpleNamespace(id=42),
        guild,
        menu,
        [SimpleNamespace(role_id=10)],
        channel=SimpleNamespace(id=9),
    )
    assert builder.show_counts is True


@pytest.mark.asyncio
async def test_rerender_routes_through_panel_interaction() -> None:
    """The live preview refreshes via the interaction token (works on ephemeral),
    not Message.edit (which silently no-ops on an ephemeral hub message).
    """
    builder = _counter_builder()
    builder._panel_interaction = SimpleNamespace()  # sentinel token holder
    builder.message = SimpleNamespace(edit=AsyncMock())  # must NOT be used
    with patch(
        "views.roles.role_menu_builder.safe_edit",
        new=AsyncMock(return_value=True),
    ) as se:
        await builder._rerender()
    se.assert_awaited_once()
    assert se.await_args.kwargs["view"] is builder
    assert se.await_args.kwargs["embed"] is not None
    builder.message.edit.assert_not_awaited()


@pytest.mark.asyncio
async def test_rerender_falls_back_to_message_edit_without_interaction() -> None:
    builder = _counter_builder()
    builder._panel_interaction = None
    builder.message = SimpleNamespace(edit=AsyncMock())
    await builder._rerender()
    builder.message.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_rerender_falls_back_when_safe_edit_fails() -> None:
    """If the token edit fails (e.g. expired), fall back to Message.edit."""
    builder = _counter_builder()
    builder._panel_interaction = SimpleNamespace()
    builder.message = SimpleNamespace(edit=AsyncMock())
    with patch(
        "views.roles.role_menu_builder.safe_edit",
        new=AsyncMock(return_value=False),
    ):
        await builder._rerender()
    builder.message.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_template_sets_mode_and_counts_from_template() -> None:
    """The Event RSVP template pre-picks button + unique + the live counter."""
    builder = _counter_builder()
    interaction = SimpleNamespace(
        response=SimpleNamespace(edit_message=AsyncMock()),
    )
    await builder._apply_template(interaction, ["event_rsvp"])
    assert builder.style == "button"
    assert builder.mode == "unique"
    assert builder.show_counts is True


def _button_labels(view) -> list[str]:
    return [c.label for c in view.children if isinstance(c, discord.ui.Button)]


def test_lean_builder_keeps_hot_buttons_and_style_first_screen() -> None:
    """The lean layout keeps content + Style top-level and folds the rare knobs."""
    builder = _counter_builder()
    labels = _button_labels(builder)
    for present in (
        "🧩 Template",
        "📦 Packs",
        "🏷️ Roles",
        "🎚️ Style",  # Style stays first-screen (owner directive)
        "📝 Text",
        "🎨 Colours",
        "📍 Channel",
        "⚙️ Advanced",
        "🚀 Post",
    ):
        assert present in labels, present
    # The five rarely-tapped knobs are no longer top-level (folded into Advanced).
    for folded in ("🎭 Theme", "⚙️ Mode", "🔢 Limit", "🖼️ Card", "📊 Counts"):
        assert folded not in labels, folded


def test_advanced_view_holds_exactly_the_folded_controls() -> None:
    builder = _counter_builder()
    labels = set(_button_labels(_AdvancedView(builder)))
    assert labels == {"🎭 Theme", "⚙️ Mode", "🔢 Limit", "🖼️ Card", "📊 Counts"}


@pytest.mark.asyncio
async def test_advanced_counts_toggle_flips_builder_flag() -> None:
    builder = _counter_builder()
    builder.show_counts = False
    adv = _AdvancedView(builder)
    counts = next(c for c in adv.children if getattr(c, "label", None) == "📊 Counts")
    interaction = SimpleNamespace(
        response=SimpleNamespace(edit_message=AsyncMock()),
    )
    await counts.callback(interaction)
    assert builder.show_counts is True
    interaction.response.edit_message.assert_awaited_once()


def test_builder_keeps_every_action_row_within_discords_five_button_cap() -> None:
    """No builder row may exceed Discord's 5-components-per-row limit.

    Regression guard: the builder's button rows are edited by many parallel
    sessions (Roles/Colours/Packs/Template/Card/Theme/Mode/…), and a 6th button
    landing on one row makes ``discord.ui.View`` raise at construction. Pin every
    row ≤ 5 (with a parent, so the ↩ Back button is included on its row too).
    """
    import discord

    guild = SimpleNamespace(id=1)
    parent = SimpleNamespace(build_embed=AsyncMock())
    builder = RoleMenuBuilder(
        SimpleNamespace(id=42),
        guild,
        SimpleNamespace(id=9),
        parent=parent,
    )
    per_row: dict[int | None, int] = {}
    for child in builder.children:
        if isinstance(child, discord.ui.Button):
            per_row[child.row] = per_row.get(child.row, 0) + 1
    assert per_row, "builder has no buttons?"
    assert all(n <= 5 for n in per_row.values()), f"row over Discord's cap: {per_row}"

