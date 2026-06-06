"""Tests for utils.role_feasibility (PR2 shared role-feasibility model)."""

from __future__ import annotations

from types import SimpleNamespace

from utils import role_feasibility as rf


def _role(rid, name="R", position=1, default=False, managed=False):
    return SimpleNamespace(
        id=rid,
        name=name,
        position=position,
        is_default=lambda: default,
        managed=managed,
    )


def _member(*, manage_roles=True, top_position=10):
    return SimpleNamespace(
        guild_permissions=SimpleNamespace(manage_roles=manage_roles),
        top_role=SimpleNamespace(position=top_position),
    )


def test_everyone_is_not_selectable():
    v = rf.evaluate_role(_role(1, "@everyone", default=True))
    assert not v.ok
    assert v.code == rf.EVERYONE
    assert v.reason  # non-empty human reason


def test_managed_role_blocked():
    v = rf.evaluate_role(_role(2, "Booster", managed=True))
    assert not v.ok
    assert v.code == rf.MANAGED


def test_bot_missing_manage_roles():
    v = rf.evaluate_role(
        _role(3, "Member", position=1),
        bot_member=_member(manage_roles=False),
    )
    assert not v.ok
    assert v.code == rf.BOT_MISSING_MANAGE_ROLES


def test_role_above_bot_top():
    v = rf.evaluate_role(
        _role(4, "Admin", position=20),
        bot_member=_member(top_position=10),
    )
    assert not v.ok
    assert v.code == rf.ABOVE_BOT


def test_role_above_actor_top():
    # Bot can manage (top 30), but the acting member's top (5) is below role (10).
    v = rf.evaluate_role(
        _role(5, "Staff", position=10),
        bot_member=_member(top_position=30),
        actor=SimpleNamespace(top_role=SimpleNamespace(position=5)),
    )
    assert not v.ok
    assert v.code == rf.ABOVE_ACTOR


def test_selectable_when_all_clear():
    v = rf.evaluate_role(
        _role(6, "Member", position=1),
        bot_member=_member(top_position=10),
    )
    assert v.ok
    assert v.code == rf.SELECTABLE
    assert v.reason == ""


def _member_with_top(*, top_position, top_id, manage_roles=True):
    return SimpleNamespace(
        guild_permissions=SimpleNamespace(manage_roles=manage_roles),
        top_role=SimpleNamespace(position=top_position, id=top_id),
    )


def test_tied_position_role_created_after_bot_is_manageable():
    """Discord role positions are NOT unique. A role at the SAME position as the
    bot's top role but created AFTER it (larger id) ranks BELOW the bot, so it is
    manageable — the raw `position >=` check wrongly flagged it (the live
    'testrole2 at pos 1, bot Galaxy Bot also pos 1' case).
    """
    bot = _member_with_top(top_position=1, top_id=100)
    v = rf.evaluate_role(_role(200, "testrole2", position=1), bot_member=bot)
    assert v.ok
    assert v.code == rf.SELECTABLE


def test_tied_position_role_created_before_bot_is_above():
    """At equal position the OLDER role (smaller id) outranks the bot."""
    bot = _member_with_top(top_position=1, top_id=200)
    v = rf.evaluate_role(_role(100, "OldAdmin", position=1), bot_member=bot)
    assert not v.ok
    assert v.code == rf.ABOVE_BOT


def test_strictly_higher_position_is_above_regardless_of_id():
    """A higher position always outranks, even with a larger (newer) id."""
    bot = _member_with_top(top_position=5, top_id=100)
    v = rf.evaluate_role(_role(999, "Admin", position=9), bot_member=bot)
    assert not v.ok
    assert v.code == rf.ABOVE_BOT


def test_precedence_everyone_before_managed():
    v = rf.evaluate_role(_role(7, "x", default=True, managed=True))
    assert v.code == rf.EVERYONE


def test_manageable_roles_partitions():
    roles = [
        _role(1, "@everyone", default=True),
        _role(2, "Admin", position=20),
        _role(3, "Member", position=1),
    ]
    manageable, excluded = rf.manageable_roles(
        roles,
        bot_member=_member(top_position=10),
    )
    assert [r.id for r in manageable] == [3]
    assert {f.code for f in excluded} == {rf.EVERYONE, rf.ABOVE_BOT}


def test_not_everyone_filter():
    assert rf.not_everyone(_role(1, "Member")) is True
    assert rf.not_everyone(_role(2, "@everyone", default=True)) is False


def test_summarize_exclusions():
    excluded = [
        rf.RoleFeasibility(1, "@everyone", False, rf.EVERYONE, "x"),
        rf.RoleFeasibility(2, "A", False, rf.ABOVE_BOT, "y"),
        rf.RoleFeasibility(3, "B", False, rf.ABOVE_BOT, "y"),
    ]
    s = rf.summarize_exclusions(excluded)
    assert s.startswith("3 hidden:")
    assert "@everyone" in s
    assert "above my top role" in s


def test_summarize_empty_is_blank():
    assert rf.summarize_exclusions([]) == ""
