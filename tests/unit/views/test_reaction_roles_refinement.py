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

import pytest

from views.roles import reaction_panel
from views.roles.role_menu_builder import RoleMenuBuilder


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
