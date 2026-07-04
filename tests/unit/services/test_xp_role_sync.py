"""Tests for services.xp_role_sync.plan_level_role_assignments (shared planner)."""

from __future__ import annotations

from unittest.mock import patch

from services import xp_role_sync


class FakeRole:
    def __init__(self, rid: int, name: str) -> None:
        self.id = rid
        self.name = name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FakeRole) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)


class FakeMember:
    def __init__(self, mid: int, roles: list[FakeRole]) -> None:
        self.id = mid
        self.roles = roles
        self.display_name = f"member-{mid}"


class FakeGuild:
    def __init__(self, roles: list[FakeRole]) -> None:
        self.id = 1
        self._by_id = {r.id: r for r in roles}


ROLE_A = FakeRole(10, "Level 5")
ROLE_B = FakeRole(20, "Level 10")
GUILD = FakeGuild([ROLE_A, ROLE_B])

XP_ROLES = [
    {"role_id": 10, "role_name": "Level 5", "level_required": 5},
    {"role_id": 20, "role_name": "Level 10", "level_required": 10},
]


def _fake_resolve(guild, *, role_id=None, name=None):
    return guild._by_id.get(role_id)


def _plan(member, new_level, *, stack, exempt=frozenset(), xp_roles=None):
    with patch(
        "services.xp_role_sync.resources.resolve_role",
        side_effect=_fake_resolve,
    ):
        return xp_role_sync.plan_level_role_assignments(
            GUILD,
            member,
            new_level,
            stack=stack,
            exempt_xp_ids=exempt,
            xp_roles=XP_ROLES if xp_roles is None else xp_roles,
            reason="test",
        )


def test_stacking_adds_every_newly_earned_role():
    member = FakeMember(1, roles=[])
    assignments = _plan(member, 10, stack=True)
    added = sorted(a.add_role_id for a in assignments)
    assert added == [10, 20]
    assert all(a.remove_role_ids == () for a in assignments)


def test_stacking_skips_already_held_roles():
    member = FakeMember(1, roles=[ROLE_A])
    assignments = _plan(member, 10, stack=True)
    assert [a.add_role_id for a in assignments] == [20]  # only the new tier


def test_single_role_keeps_highest_and_demotes_others():
    member = FakeMember(1, roles=[ROLE_A])
    assignments = _plan(member, 10, stack=False)
    assert len(assignments) == 1
    a = assignments[0]
    assert a.add_role_id == 20  # promote to highest earned
    assert a.remove_role_ids == (10,)  # demote the lower tier


def test_single_role_noop_when_already_top():
    member = FakeMember(1, roles=[ROLE_B])
    assert _plan(member, 10, stack=False) == []


def test_exempt_member_gets_nothing():
    exempt_role = FakeRole(99, "No XP")
    member = FakeMember(1, roles=[exempt_role])
    assert _plan(member, 10, stack=True, exempt=frozenset({99})) == []


def test_no_qualifying_roles_below_threshold():
    member = FakeMember(1, roles=[])
    assert _plan(member, 3, stack=True) == []  # below the level-5 threshold


def test_unresolvable_role_is_skipped():
    member = FakeMember(1, roles=[])
    ghost = [{"role_id": 30, "role_name": "Ghost", "level_required": 1}]
    assert _plan(member, 10, stack=True, xp_roles=ghost) == []
