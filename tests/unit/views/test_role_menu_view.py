"""Tests for views.roles.role_menu_view — the member-facing persistent menu."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from utils import role_menu_presentation as presentation
from views.roles import role_menu_view as rmv


class FakeRole:
    def __init__(self, rid: int, name: str = "Role") -> None:
        self.id = rid
        self.name = name

    @property
    def mention(self) -> str:
        return f"<@&{self.id}>"


class FakeGuild:
    def __init__(self, roles: list[FakeRole]) -> None:
        self._roles = {r.id: r for r in roles}

    def get_role(self, rid: int) -> FakeRole | None:
        return self._roles.get(rid)


def _menu(style: str = "dropdown", mode: str = "normal", max_roles: int = 0) -> dict:
    return {
        "menu_id": 1,
        "title": "Pick your roles",
        "description": "desc",
        "style": style,
        "mode": mode,
        "max_roles": max_roles,
        "theme": "neon",
        "channel_id": 9,
        "message_id": 555,
    }


def _opts() -> list[dict]:
    return [
        {"role_id": 10, "label": "Gamer", "emoji": None},
        {"role_id": 20, "label": "Artist", "emoji": None},
    ]


def test_no_arg_construction_is_empty_and_safe():
    """The registry / manifest may instantiate the class with no args."""
    view = rmv.RoleMenuView()
    assert len(view.children) == 0


def test_dropdown_menu_builds_single_select_with_scoped_custom_id():
    view = rmv.RoleMenuView(_menu("dropdown"), _opts())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1
    assert selects[0].custom_id == "role_menu:1:select"
    assert selects[0].max_values == 2  # both roles selectable


def test_button_menu_builds_one_button_per_role():
    view = rmv.RoleMenuView(_menu("button"), _opts())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert {b.custom_id for b in buttons} == {
        "role_menu:1:role:10",
        "role_menu:1:role:20",
    }


def _roster_ids(view) -> list[str]:
    return [
        c.custom_id
        for c in view.children
        if getattr(c, "custom_id", "") == "role_menu:1:roster"
    ]


def test_no_roster_button_without_show_counts():
    assert _roster_ids(rmv.RoleMenuView(_menu("dropdown"), _opts())) == []


def test_dropdown_with_counts_adds_roster_button():
    menu = _menu("dropdown")
    menu["show_counts"] = True
    assert _roster_ids(rmv.RoleMenuView(menu, _opts())) == ["role_menu:1:roster"]


def test_button_menu_with_counts_adds_roster_button():
    menu = _menu("button")
    menu["show_counts"] = True
    assert _roster_ids(rmv.RoleMenuView(menu, _opts())) == ["role_menu:1:roster"]


def test_full_button_menu_skips_roster_for_component_budget():
    menu = _menu("button")
    menu["show_counts"] = True
    opts = [{"role_id": 100 + i, "label": f"R{i}", "emoji": None} for i in range(25)]
    view = rmv.RoleMenuView(menu, opts)
    # 25 role buttons exhaust Discord's 25-component cap → roster is omitted.
    assert len(view.children) == 25
    assert _roster_ids(view) == []


@pytest.mark.asyncio
async def test_handle_roster_sends_ephemeral_embed():
    menu = _menu("dropdown")
    menu["show_counts"] = True
    view = rmv.RoleMenuView(menu, _opts())
    sentinel = discord.Embed(title="roster")
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()
    with patch.object(
        rmv.role_menu_counter,
        "build_roster_embed",
        return_value=sentinel,
    ) as build:
        await rmv._handle_roster(interaction, view)
    build.assert_called_once()
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs["embed"] is sentinel
    assert kwargs["ephemeral"] is True


def test_select_bounds_honour_mode():
    assert rmv._select_bounds("unique", 0, 5) == (0, 1)
    assert rmv._select_bounds("normal", 3, 10) == (0, 3)
    assert rmv._select_bounds("normal", 0, 40) == (0, rmv.MAX_MENU_ROLES)


def test_build_menu_embed_uses_theme_colour():
    guild = FakeGuild([FakeRole(10, "Gamer"), FakeRole(20, "Artist")])
    embed = rmv.build_menu_embed(_menu(), _opts(), guild)
    assert embed.title == "Pick your roles"
    assert embed.color == presentation.theme_color("neon")
    # Roles field lists the live mentions.
    roles_field = next(f for f in embed.fields if f.name == "Roles")
    assert "<@&10>" in roles_field.value


class _MemberWithRoles:
    def __init__(self, *role_ids: int) -> None:
        self.roles = [FakeRole(r) for r in role_ids]


class _GuildWithMembers(FakeGuild):
    def __init__(self, roles: list[FakeRole], members: list[_MemberWithRoles]) -> None:
        super().__init__(roles)
        self.members = members


def test_build_menu_embed_without_show_counts_has_no_counter():
    guild = FakeGuild([FakeRole(10, "Gamer"), FakeRole(20, "Artist")])
    embed = rmv.build_menu_embed(_menu(), _opts(), guild)
    roles_field = next(f for f in embed.fields if f.name == "Roles")
    assert "👥" not in roles_field.value
    assert "signed up" not in (embed.footer.text or "")


def test_build_menu_embed_with_show_counts_renders_per_role_and_total():
    guild = _GuildWithMembers(
        [FakeRole(10, "Going"), FakeRole(20, "Maybe")],
        # role 10 held by 2 members (one of them also holds 20); role 20 by 1.
        # Distinct members holding any menu role = 2 (never double-counted).
        [_MemberWithRoles(10), _MemberWithRoles(10, 20)],
    )
    menu = _menu()
    menu["show_counts"] = True
    embed = rmv.build_menu_embed(menu, _opts(), guild)
    roles_field = next(f for f in embed.fields if f.name == "Roles")
    lines = roles_field.value.splitlines()
    # Each option line carries its own live holder count …
    assert lines[0].endswith("👥 2")  # role 10 → 2 holders
    assert lines[1].endswith("👥 1")  # role 20 → 1 holder
    # … and the footer shows the distinct-member total (no double count).
    assert "👥 2 people signed up" in embed.footer.text


def test_build_menu_message_without_card_has_no_files_or_image():
    guild = FakeGuild([FakeRole(10, "Gamer")])
    embed, files = rmv.build_menu_message(_menu(), _opts(), guild)
    assert files == []
    assert embed.image.url is None  # no attachment referenced


def test_render_menu_card_none_when_no_template():
    assert rmv.render_menu_card(_menu()) is None


def test_render_menu_card_none_for_unknown_template():
    menu = _menu()
    menu["card_template"] = "bogus"
    assert rmv.render_menu_card(menu) is None


def test_build_menu_message_with_card_attaches_file_and_sets_image():
    pytest.importorskip("PIL")
    guild = FakeGuild([FakeRole(10, "Gamer")])
    menu = _menu()
    menu["card_template"] = "banner"
    menu["card_text"] = "Choose below"
    embed, files = rmv.build_menu_message(menu, _opts(), guild)
    assert len(files) == 1
    assert files[0].filename == rmv._CARD_FILENAME
    assert embed.image.url == f"attachment://{rmv._CARD_FILENAME}"


def test_render_menu_card_degrades_to_none_without_pillow(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def _fail_pil(name, *args, **kwargs):
        if name.startswith("PIL"):
            raise ImportError("no pillow")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fail_pil)
    menu = _menu()
    menu["card_template"] = "banner"
    assert rmv.render_menu_card(menu) is None


def test_view_is_persistent_but_not_in_anchor_registry():
    """A role menu is a public data-driven message re-bound by reattach_role_menus,
    not a per-user anchor panel — so it is intentionally NOT register()'d (which
    would collide with RoleHubPanelView's SUBSYSTEM='role' and trip the
    identity-contract SUBSYSTEMS parity check).
    """
    from core.runtime import persistent_views

    assert issubclass(rmv.RoleMenuView, persistent_views.PersistentView)
    # Not registered, and must not have hijacked the 'role' hub's registry slot.
    assert persistent_views.get_view_class("role_menu") is None
    assert persistent_views.get_view_class("role") is not rmv.RoleMenuView


@pytest.mark.asyncio
async def test_reattach_binds_each_posted_menu():
    rmv.reset_reattach_state()
    bot = MagicMock()
    menus = [_menu()]
    options = [
        __import__(
            "services.reaction_role_service",
            fromlist=["RoleOption"],
        ).RoleOption(10),
    ]
    with (
        patch(
            "services.reaction_role_service.list_posted_menus",
            new=AsyncMock(return_value=menus),
        ),
        patch(
            "services.reaction_role_service.get_menu_options",
            new=AsyncMock(return_value=options),
        ),
    ):
        count = await rmv.reattach_role_menus(bot)
    assert count == 1
    bot.add_view.assert_called_once()
    assert bot.add_view.call_args.kwargs["message_id"] == 555


@pytest.mark.asyncio
async def test_reattach_is_idempotent():
    rmv.reset_reattach_state()
    bot = MagicMock()
    with patch(
        "services.reaction_role_service.list_posted_menus",
        new=AsyncMock(return_value=[]),
    ):
        await rmv.reattach_role_menus(bot)
        second = await rmv.reattach_role_menus(bot)  # guarded no-op
    assert second == 0
