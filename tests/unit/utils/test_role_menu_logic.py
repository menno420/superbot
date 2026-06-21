"""Pure role-menu mode enforcement (reaction-roles overhaul PR 2)."""

from __future__ import annotations

from utils.role_menu_logic import reconcile_select, toggle_button

# --- dropdown reconcile -----------------------------------------------------


def test_reconcile_adds_picked_removes_unpicked():
    d = reconcile_select(
        member_role_ids={1, 2},
        menu_role_ids=[1, 2, 3],
        picked_role_ids={2, 3},
        mode="normal",
        max_roles=0,
    )
    assert d.to_add == (3,)
    assert d.to_remove == (1,)
    assert d.rejected is None


def test_reconcile_ignores_roles_outside_this_menu():
    # Member holds role 9 from another menu; it must never be touched.
    d = reconcile_select(
        member_role_ids={9},
        menu_role_ids=[1, 2],
        picked_role_ids={1, 9},
        mode="normal",
        max_roles=0,
    )
    assert d.to_add == (1,)
    assert d.to_remove == ()


def test_reconcile_verify_is_add_only():
    d = reconcile_select(
        member_role_ids={1},
        menu_role_ids=[1, 2],
        picked_role_ids={2},
        mode="verify",
        max_roles=0,
    )
    assert d.to_add == (2,)
    assert d.to_remove == ()  # role 1 not removed despite being unpicked


def test_reconcile_unique_caps_to_one():
    d = reconcile_select(
        member_role_ids=set(),
        menu_role_ids=[1, 2, 3],
        picked_role_ids={2, 3},
        mode="unique",
        max_roles=0,
    )
    assert d.to_add == (2,)  # first in menu order kept
    assert d.rejected is not None


def test_reconcile_respects_max_roles_cap():
    d = reconcile_select(
        member_role_ids=set(),
        menu_role_ids=[1, 2, 3, 4],
        picked_role_ids={1, 2, 3},
        mode="normal",
        max_roles=2,
    )
    assert d.to_add == (1, 2)
    assert d.rejected is not None


# --- button toggle ----------------------------------------------------------


def test_toggle_adds_when_absent():
    d = toggle_button(
        member_role_ids=set(),
        menu_role_ids=[1, 2],
        clicked_role_id=1,
        mode="normal",
        max_roles=0,
    )
    assert d.to_add == (1,)
    assert d.to_remove == ()


def test_toggle_removes_when_present():
    d = toggle_button(
        member_role_ids={1},
        menu_role_ids=[1, 2],
        clicked_role_id=1,
        mode="normal",
        max_roles=0,
    )
    assert d.to_add == ()
    assert d.to_remove == (1,)


def test_toggle_unique_clears_siblings():
    d = toggle_button(
        member_role_ids={1},
        menu_role_ids=[1, 2, 3],
        clicked_role_id=2,
        mode="unique",
        max_roles=0,
    )
    assert d.to_add == (2,)
    assert d.to_remove == (1,)


def test_toggle_verify_refuses_removal():
    d = toggle_button(
        member_role_ids={1},
        menu_role_ids=[1],
        clicked_role_id=1,
        mode="verify",
        max_roles=0,
    )
    assert d.to_add == ()
    assert d.to_remove == ()
    assert d.rejected is not None


def test_toggle_max_roles_refuses_over_cap():
    d = toggle_button(
        member_role_ids={1, 2},
        menu_role_ids=[1, 2, 3],
        clicked_role_id=3,
        mode="normal",
        max_roles=2,
    )
    assert d.to_add == ()
    assert d.rejected is not None
