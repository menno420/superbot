"""Tests for the PR 2 role-menu methods of services.reaction_role_service.

(PR 1's emoji-binding methods are covered by ``test_reaction_role_service.py``.)
Covers, CI-safe with no DB: server-side mode enforcement (normal / unique /
verify / max_roles) for both the button (``toggle_role``) and dropdown
(``apply_selection``) surfaces, and that menu *config* changes emit
``audit.action_recorded`` while member self-assignment does not.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services import reaction_role_service as svc

# ---------------------------------------------------------------------------
# Minimal Discord fakes (positions chosen so the bot can manage every role)
# ---------------------------------------------------------------------------


class FakeRole:
    def __init__(self, rid: int, *, position: int = 1, name: str = "Role") -> None:
        self.id = rid
        self.position = position
        self.name = name
        self.managed = False

    def is_default(self) -> bool:
        return False

    @property
    def mention(self) -> str:
        return f"<@&{self.id}>"


class FakeMember:
    def __init__(self, roles: list[FakeRole]) -> None:
        self.roles = roles
        self.add_roles = AsyncMock()
        self.remove_roles = AsyncMock()


class FakeGuild:
    def __init__(self, roles: list[FakeRole]) -> None:
        self.id = 1
        self._roles = {r.id: r for r in roles}
        # Bot top-role well above the menu roles → everything is manageable.
        self.me = SimpleNamespace(
            top_role=FakeRole(99999, position=100, name="Bot"),
            guild_permissions=SimpleNamespace(manage_roles=True),
        )

    def get_role(self, rid: int) -> FakeRole | None:
        return self._roles.get(rid)


def _menu(mode: str = "normal", max_roles: int = 0) -> dict:
    return {"menu_id": 1, "mode": mode, "max_roles": max_roles, "style": "dropdown"}


def _patch_menu(menu: dict, option_ids: list[int]):
    opts = [{"role_id": rid} for rid in option_ids]
    return (
        patch.object(svc.menus_db, "get_menu", new=AsyncMock(return_value=menu)),
        patch.object(svc.menus_db, "get_options", new=AsyncMock(return_value=opts)),
    )


# ---------------------------------------------------------------------------
# toggle_role — the button surface
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_toggle_adds_role_when_absent():
    guild = FakeGuild([FakeRole(10), FakeRole(20)])
    member = FakeMember(roles=[])
    p1, p2 = _patch_menu(_menu("normal"), [10, 20])
    with p1, p2:
        out = await svc.toggle_role(
            menu_id=1,
            member=member,
            guild=guild,
            clicked_role_id=10,
        )
    assert out.added == (10,)
    assert out.removed == ()
    member.add_roles.assert_awaited_once()


@pytest.mark.asyncio
async def test_toggle_removes_role_when_held():
    held = FakeRole(10)
    guild = FakeGuild([held, FakeRole(20)])
    member = FakeMember(roles=[held])
    p1, p2 = _patch_menu(_menu("normal"), [10, 20])
    with p1, p2:
        out = await svc.toggle_role(
            menu_id=1,
            member=member,
            guild=guild,
            clicked_role_id=10,
        )
    assert out.removed == (10,)
    assert out.added == ()
    member.remove_roles.assert_awaited_once()


@pytest.mark.asyncio
async def test_toggle_unique_clears_sibling():
    a, b = FakeRole(10), FakeRole(20)
    guild = FakeGuild([a, b])
    member = FakeMember(roles=[a])  # already holds the sibling
    p1, p2 = _patch_menu(_menu("unique"), [10, 20])
    with p1, p2:
        out = await svc.toggle_role(
            menu_id=1,
            member=member,
            guild=guild,
            clicked_role_id=20,
        )
    assert out.added == (20,)
    assert out.removed == (10,)  # sibling cleared


@pytest.mark.asyncio
async def test_toggle_verify_never_removes():
    held = FakeRole(10)
    guild = FakeGuild([held])
    member = FakeMember(roles=[held])
    p1, p2 = _patch_menu(_menu("verify"), [10])
    with p1, p2:
        out = await svc.toggle_role(
            menu_id=1,
            member=member,
            guild=guild,
            clicked_role_id=10,
        )
    assert out.added == ()
    assert out.removed == ()
    assert "verify" in out.note.lower()
    member.remove_roles.assert_not_awaited()


@pytest.mark.asyncio
async def test_toggle_max_roles_blocks_extra_pick():
    a, b = FakeRole(10), FakeRole(20)
    guild = FakeGuild([a, b])
    member = FakeMember(roles=[a])  # already at the cap of 1
    p1, p2 = _patch_menu(_menu("normal", max_roles=1), [10, 20])
    with p1, p2:
        out = await svc.toggle_role(
            menu_id=1,
            member=member,
            guild=guild,
            clicked_role_id=20,
        )
    assert out.added == ()
    assert out.blocked == (20,)
    member.add_roles.assert_not_awaited()


@pytest.mark.asyncio
async def test_toggle_unknown_role_is_rejected():
    guild = FakeGuild([FakeRole(10)])
    member = FakeMember(roles=[])
    p1, p2 = _patch_menu(_menu("normal"), [10])
    with p1, p2:
        out = await svc.toggle_role(
            menu_id=1,
            member=member,
            guild=guild,
            clicked_role_id=999,
        )
    assert not out.changed
    member.add_roles.assert_not_awaited()


# ---------------------------------------------------------------------------
# apply_selection — the dropdown surface
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_selection_reconciles_add_and_remove():
    a, b, c = FakeRole(10), FakeRole(20), FakeRole(30)
    guild = FakeGuild([a, b, c])
    member = FakeMember(roles=[a])  # holds A
    p1, p2 = _patch_menu(_menu("normal"), [10, 20, 30])
    with p1, p2:
        out = await svc.apply_selection(
            menu_id=1,
            member=member,
            guild=guild,
            selected_ids=[20, 30],
        )
    assert set(out.added) == {20, 30}
    assert out.removed == (10,)  # A deselected


@pytest.mark.asyncio
async def test_apply_selection_verify_only_adds():
    a, b = FakeRole(10), FakeRole(20)
    guild = FakeGuild([a, b])
    member = FakeMember(roles=[a])
    p1, p2 = _patch_menu(_menu("verify"), [10, 20])
    with p1, p2:
        out = await svc.apply_selection(
            menu_id=1,
            member=member,
            guild=guild,
            selected_ids=[20],
        )
    assert out.added == (20,)
    assert out.removed == ()  # verify never removes the held role


@pytest.mark.asyncio
async def test_apply_selection_unique_keeps_one():
    a, b = FakeRole(10), FakeRole(20)
    guild = FakeGuild([a, b])
    member = FakeMember(roles=[])
    p1, p2 = _patch_menu(_menu("unique"), [10, 20])
    with p1, p2:
        out = await svc.apply_selection(
            menu_id=1,
            member=member,
            guild=guild,
            selected_ids=[10, 20],
        )
    # Unique caps the desired set to one role.
    assert len(out.added) == 1


# ---------------------------------------------------------------------------
# Config writes are audited; member assignment is not
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_menu_emits_audit_and_validates():
    with (
        patch.object(
            svc.menus_db,
            "create_menu",
            new=AsyncMock(return_value=7),
        ) as create,
        patch.object(svc.menus_db, "replace_options", new=AsyncMock()) as setopts,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit,
    ):
        menu_id = await svc.create_menu(
            guild_id=1,
            channel_id=2,
            title="Roles",
            description=None,
            style="bogus",  # invalid → coerced
            mode="weird",  # invalid → coerced
            max_roles=-5,  # clamped to 0
            options=[svc.RoleOption(10), svc.RoleOption(20)],
            actor_id=99,
        )
    assert menu_id == 7
    setopts.assert_awaited_once()
    # invalid style/mode coerced; negative limit clamped.
    assert create.await_args.kwargs["style"] == "dropdown"
    assert create.await_args.kwargs["mode"] == "normal"
    assert create.await_args.kwargs["max_roles"] == 0
    audit.assert_awaited_once()
    kw = audit.await_args.kwargs
    assert kw["subsystem"] == "role"
    assert kw["mutation_type"] == "create_role_menu"
    assert kw["target"] == "role_menu:7"
    assert kw["guild_id"] == 1
    assert kw["actor_id"] == 99


@pytest.mark.asyncio
async def test_create_menu_threads_card_fields_to_db():
    """Banner-card fields (PR 6, §4.6d) pass through create → db, blanks → None."""
    with (
        patch.object(
            svc.menus_db,
            "create_menu",
            new=AsyncMock(return_value=8),
        ) as create,
        patch.object(svc.menus_db, "replace_options", new=AsyncMock()),
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ),
    ):
        await svc.create_menu(
            guild_id=1,
            channel_id=2,
            title="Roles",
            description=None,
            style="dropdown",
            mode="normal",
            max_roles=0,
            options=[svc.RoleOption(10)],
            card_template="banner",
            card_text="Choose below",
            actor_id=99,
        )
        await svc.create_menu(
            guild_id=1,
            channel_id=2,
            title="Roles",
            description=None,
            style="dropdown",
            mode="normal",
            max_roles=0,
            options=[svc.RoleOption(10)],
            card_template="",  # blank coerced to None (no card)
            card_text="",
            actor_id=99,
        )
    assert create.await_args_list[0].kwargs["card_template"] == "banner"
    assert create.await_args_list[0].kwargs["card_text"] == "Choose below"
    assert create.await_args_list[1].kwargs["card_template"] is None
    assert create.await_args_list[1].kwargs["card_text"] is None


@pytest.mark.asyncio
async def test_update_menu_threads_card_fields_to_db():
    with (
        patch.object(
            svc.menus_db,
            "get_menu",
            new=AsyncMock(
                return_value={
                    "title": "T",
                    "style": "dropdown",
                    "mode": "normal",
                    "max_roles": 0,
                },
            ),
        ),
        patch.object(svc.menus_db, "get_options", new=AsyncMock(return_value=[])),
        patch.object(svc.menus_db, "update_menu", new=AsyncMock()) as update,
        patch.object(svc.menus_db, "replace_options", new=AsyncMock()),
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ),
    ):
        await svc.update_menu(
            menu_id=5,
            guild_id=1,
            title="Roles",
            description=None,
            style="dropdown",
            mode="normal",
            max_roles=0,
            options=[svc.RoleOption(10)],
            card_template="gradient",
            card_text=None,
            actor_id=99,
        )
    assert update.await_args.kwargs["card_template"] == "gradient"
    assert update.await_args.kwargs["card_text"] is None


@pytest.mark.asyncio
async def test_create_menu_threads_show_counts_to_db():
    """The sign-up-counter flag passes through create → db (default False)."""
    with (
        patch.object(
            svc.menus_db,
            "create_menu",
            new=AsyncMock(return_value=8),
        ) as create,
        patch.object(svc.menus_db, "replace_options", new=AsyncMock()),
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit,
    ):
        await svc.create_menu(
            guild_id=1,
            channel_id=2,
            title="RSVP",
            description=None,
            style="button",
            mode="unique",
            max_roles=0,
            options=[svc.RoleOption(10)],
            show_counts=True,
            actor_id=99,
        )
        await svc.create_menu(
            guild_id=1,
            channel_id=2,
            title="Plain",
            description=None,
            style="dropdown",
            mode="normal",
            max_roles=0,
            options=[svc.RoleOption(10)],
            actor_id=99,
        )
    assert create.await_args_list[0].kwargs["show_counts"] is True
    assert create.await_args_list[1].kwargs["show_counts"] is False
    # The audit summary records that counts are on for the first menu.
    assert "counts" in audit.await_args_list[0].kwargs["new_value"]
    assert "counts" not in audit.await_args_list[1].kwargs["new_value"]


@pytest.mark.asyncio
async def test_update_menu_threads_show_counts_to_db():
    with (
        patch.object(
            svc.menus_db,
            "get_menu",
            new=AsyncMock(
                return_value={
                    "title": "T",
                    "style": "dropdown",
                    "mode": "normal",
                    "max_roles": 0,
                    "show_counts": False,
                },
            ),
        ),
        patch.object(svc.menus_db, "get_options", new=AsyncMock(return_value=[])),
        patch.object(svc.menus_db, "update_menu", new=AsyncMock()) as update,
        patch.object(svc.menus_db, "replace_options", new=AsyncMock()),
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ),
    ):
        await svc.update_menu(
            menu_id=5,
            guild_id=1,
            title="RSVP",
            description=None,
            style="button",
            mode="unique",
            max_roles=0,
            options=[svc.RoleOption(10)],
            show_counts=True,
            actor_id=99,
        )
    assert update.await_args.kwargs["show_counts"] is True


@pytest.mark.asyncio
async def test_delete_menu_emits_audit():
    with (
        patch.object(
            svc.menus_db,
            "get_menu",
            new=AsyncMock(return_value={"menu_id": 5, "title": "Old"}),
        ),
        patch.object(svc.menus_db, "delete_menu", new=AsyncMock()) as delete,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit,
    ):
        await svc.delete_menu(menu_id=5, guild_id=1, actor_id=99)
    delete.assert_awaited_once_with(5)
    kw = audit.await_args.kwargs
    assert kw["mutation_type"] == "delete_role_menu"
    assert kw["new_value"] is None


@pytest.mark.asyncio
async def test_toggle_does_not_emit_audit():
    """Member self-assignment is high-volume + opt-in — never auto-audited (§9)."""
    guild = FakeGuild([FakeRole(10)])
    member = FakeMember(roles=[])
    p1, p2 = _patch_menu(_menu("normal"), [10])
    with p1, p2, patch("services.audit_events.emit_audit_action") as audit:
        await svc.toggle_role(menu_id=1, member=member, guild=guild, clicked_role_id=10)
    audit.assert_not_called()


@pytest.mark.asyncio
async def test_set_menu_location_passes_through_without_audit():
    """Repost records the new channel + message; config is unchanged → no audit."""
    with (
        patch.object(svc.menus_db, "set_menu_location", new=AsyncMock()) as loc,
        patch("services.audit_events.emit_audit_action") as audit,
    ):
        await svc.set_menu_location(7, 222, 333)
    loc.assert_awaited_once_with(7, 222, 333)
    audit.assert_not_called()


# ---------------------------------------------------------------------------
# Colour-role auto-create (owner direction, 2026-06-21)
# ---------------------------------------------------------------------------

# Opaque colour sentinels — RoleLifecycleService.apply is mocked, so colours just
# pass through and are compared by identity.
_PRIMARY = object()
_SECONDARY = object()
_TERTIARY = object()


def test_supports_role_gradients_matches_feature_variants():
    assert svc.supports_role_gradients(
        SimpleNamespace(features=["ENHANCED_ROLE_COLORS"]),
    )
    # Defensive substring match survives a rollout rename.
    assert svc.supports_role_gradients(
        SimpleNamespace(features=["GUILD_ROLE_COLOURS_X"]),
    )
    assert not svc.supports_role_gradients(SimpleNamespace(features=["COMMUNITY"]))
    assert not svc.supports_role_gradients(SimpleNamespace(features=[]))


def _applied(target_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        applied=[SimpleNamespace(target_id=target_id)],
        first_error="",
    )


def _failed(reason: str = "400") -> SimpleNamespace:
    return SimpleNamespace(applied=[], first_error=reason)


@pytest.mark.asyncio
async def test_ensure_color_role_reuses_existing_same_name_role():
    guild = SimpleNamespace(id=1, features=[])
    with patch(
        "core.runtime.resources.resolve_role",
        return_value=SimpleNamespace(id=555),
    ):
        role_id, created, note = await svc.ensure_color_role(
            guild,
            name="Red",
            color=_PRIMARY,
            actor=SimpleNamespace(id=9),
        )
    assert (role_id, created, note) == (555, False, "")


@pytest.mark.asyncio
async def test_ensure_color_role_creates_solid_when_no_gradient():
    guild = SimpleNamespace(id=1, features=[])
    apply_mock = AsyncMock(return_value=_applied(777))
    with (
        patch("core.runtime.resources.resolve_role", return_value=None),
        patch(
            "services.role_lifecycle_service.RoleLifecycleService.apply",
            new=apply_mock,
        ),
    ):
        role_id, created, _ = await svc.ensure_color_role(
            guild,
            name="Sunset",
            color=_PRIMARY,
            actor=SimpleNamespace(id=9),
        )
    assert (role_id, created) == (777, True)
    req = apply_mock.await_args.args[1]  # (guild, request, actor) — mock is unbound
    assert req.secondary_color is None
    assert req.tertiary_color is None


@pytest.mark.asyncio
async def test_ensure_color_role_drops_gradient_without_perk():
    guild = SimpleNamespace(id=1, features=[])  # no Enhanced Role Styles
    apply_mock = AsyncMock(return_value=_applied(777))
    with (
        patch("core.runtime.resources.resolve_role", return_value=None),
        patch(
            "services.role_lifecycle_service.RoleLifecycleService.apply",
            new=apply_mock,
        ),
    ):
        await svc.ensure_color_role(
            guild,
            name="Grad",
            color=_PRIMARY,
            secondary=_SECONDARY,
            tertiary=_TERTIARY,
            actor=SimpleNamespace(id=9),
        )
    req = apply_mock.await_args.args[1]
    assert req.secondary_color is None  # guild lacks the perk → solid only


@pytest.mark.asyncio
async def test_ensure_color_role_applies_gradient_with_perk():
    guild = SimpleNamespace(id=1, features=["ENHANCED_ROLE_COLORS"])
    apply_mock = AsyncMock(return_value=_applied(777))
    with (
        patch("core.runtime.resources.resolve_role", return_value=None),
        patch(
            "services.role_lifecycle_service.RoleLifecycleService.apply",
            new=apply_mock,
        ),
    ):
        await svc.ensure_color_role(
            guild,
            name="Grad",
            color=_PRIMARY,
            secondary=_SECONDARY,
            actor=SimpleNamespace(id=9),
        )
    req = apply_mock.await_args.args[1]
    assert req.secondary_color is _SECONDARY


@pytest.mark.asyncio
async def test_ensure_color_role_falls_back_to_solid_on_gradient_failure():
    guild = SimpleNamespace(id=1, features=["ENHANCED_ROLE_COLORS"])
    # First (gradient) create fails; the solid retry succeeds.
    apply_mock = AsyncMock(side_effect=[_failed("400"), _applied(888)])
    with (
        patch("core.runtime.resources.resolve_role", return_value=None),
        patch(
            "services.role_lifecycle_service.RoleLifecycleService.apply",
            new=apply_mock,
        ),
    ):
        role_id, created, note = await svc.ensure_color_role(
            guild,
            name="Grad",
            color=_PRIMARY,
            secondary=_SECONDARY,
            actor=SimpleNamespace(id=9),
        )
    assert (role_id, created) == (888, True)
    assert "solid" in note.lower()
    assert apply_mock.await_count == 2
    assert apply_mock.await_args_list[1].args[1].secondary_color is None


# ---------------------------------------------------------------------------
# ensure_role — the general reuse-or-create seam (bulk role packs)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_role_reuses_existing_same_name_role():
    guild = SimpleNamespace(id=1, features=[])
    with patch(
        "core.runtime.resources.resolve_role",
        return_value=SimpleNamespace(id=321),
    ):
        role_id, created, note = await svc.ensure_role(
            guild,
            name="Moderator",
            color=_PRIMARY,
            hoist=True,
            actor=SimpleNamespace(id=9),
        )
    assert (role_id, created, note) == (321, False, "")


@pytest.mark.asyncio
async def test_ensure_role_creates_with_hoist_and_no_gradient():
    guild = SimpleNamespace(id=1, features=[])
    apply_mock = AsyncMock(return_value=_applied(654))
    with (
        patch("core.runtime.resources.resolve_role", return_value=None),
        patch(
            "services.role_lifecycle_service.RoleLifecycleService.apply",
            new=apply_mock,
        ),
    ):
        role_id, created, _ = await svc.ensure_role(
            guild,
            name="Valorant",
            color=_PRIMARY,
            hoist=True,
            actor=SimpleNamespace(id=9),
        )
    assert (role_id, created) == (654, True)
    req = apply_mock.await_args.args[1]
    assert req.operation == "create"
    assert req.name == "Valorant"
    assert req.hoist is True
    assert req.secondary_color is None


@pytest.mark.asyncio
async def test_ensure_role_blank_name_falls_back():
    guild = SimpleNamespace(id=1, features=[])
    apply_mock = AsyncMock(return_value=_applied(1))
    with (
        patch("core.runtime.resources.resolve_role", return_value=None),
        patch(
            "services.role_lifecycle_service.RoleLifecycleService.apply",
            new=apply_mock,
        ),
    ):
        await svc.ensure_role(
            guild,
            name="   ",
            color=_PRIMARY,
            actor=SimpleNamespace(id=9),
        )
    assert apply_mock.await_args.args[1].name == "role"
