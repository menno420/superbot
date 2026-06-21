"""Rendering + custom_id wiring for the public role menu (PR 2)."""

from __future__ import annotations

import re
from types import SimpleNamespace

from utils.role_menu_presets import resolve_theme
from views.roles.role_menu_view import (
    _BTN_TEMPLATE,
    _SEL_TEMPLATE,
    RoleMenuSelect,
    RoleMenuToggleButton,
    render_role_menu,
)


class _FakeGuild:
    def __init__(self, roles: dict[int, str]) -> None:
        self._roles = {
            rid: SimpleNamespace(id=rid, name=name, mention=f"<@&{rid}>")
            for rid, name in roles.items()
        }

    def get_role(self, role_id: int):
        return self._roles.get(role_id)


def _menu(**over):
    base = {
        "menu_id": 7,
        "title": "Pick your roles",
        "description": "Choose below",
        "style": "dropdown",
        "mode": "normal",
        "max_roles": 0,
        "theme": "game",
    }
    base.update(over)
    return base


def test_dropdown_renders_single_select_with_theme_colour():
    guild = _FakeGuild({10: "Gamer", 20: "Artist"})
    embed, view = render_role_menu(
        _menu(),
        [{"role_id": 10}, {"role_id": 20}],
        guild,
    )
    selects = [i for i in view.children if isinstance(i, RoleMenuSelect)]
    assert len(selects) == 1
    assert embed.color == resolve_theme("game").color
    # min 0 (clearable), max = number of options (unlimited menu).
    assert selects[0].item.min_values == 0
    assert selects[0].item.max_values == 2


def test_unique_mode_caps_select_to_one():
    guild = _FakeGuild({10: "A", 20: "B", 30: "C"})
    _embed, view = render_role_menu(
        _menu(mode="unique"),
        [{"role_id": 10}, {"role_id": 20}, {"role_id": 30}],
        guild,
    )
    select = next(i for i in view.children if isinstance(i, RoleMenuSelect))
    assert select.item.max_values == 1


def test_button_style_renders_one_button_per_role():
    guild = _FakeGuild({10: "Gamer", 20: "Artist"})
    _embed, view = render_role_menu(
        _menu(style="button"),
        [{"role_id": 10}, {"role_id": 20}],
        guild,
    )
    buttons = [i for i in view.children if isinstance(i, RoleMenuToggleButton)]
    assert len(buttons) == 2
    assert {b.role_id for b in buttons} == {10, 20}


def test_button_custom_id_round_trips_via_template():
    btn = RoleMenuToggleButton(7, 10, label="Gamer")
    assert btn.item.custom_id == "rmenu:btn:7:10"
    m = re.fullmatch(_BTN_TEMPLATE, btn.item.custom_id)
    assert m and int(m["menu_id"]) == 7 and int(m["role_id"]) == 10


def test_select_custom_id_round_trips_via_template():
    sel = RoleMenuSelect(7)
    assert sel.item.custom_id == "rmenu:sel:7"
    m = re.fullmatch(_SEL_TEMPLATE, sel.item.custom_id)
    assert m and int(m["menu_id"]) == 7


def test_view_is_persistent_timeout_none():
    guild = _FakeGuild({10: "A"})
    _embed, view = render_role_menu(_menu(), [{"role_id": 10}], guild)
    assert view.timeout is None


def test_deleted_role_renders_safely():
    guild = _FakeGuild({})  # role 10 no longer exists
    embed, _view = render_role_menu(_menu(), [{"role_id": 10}], guild)
    assert "deleted role 10" in embed.description
