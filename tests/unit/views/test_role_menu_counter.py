"""Tests for views.roles.role_menu_counter — the live sign-up counter.

Covers the two pieces of real logic, CI-safe with no Discord/DB:
* ``collect_counts`` — the one-pass current-holder math (per-role + a distinct
  total that never double-counts a member holding two of the menu's roles).
* the debounced refresh — coalescing a click-burst into one trailing edit, and
  the edit re-reading live counts (bailing cleanly when counts were turned off).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.roles import role_menu_counter as counter


class FakeRole:
    def __init__(self, rid: int, name: str = "Role", members: list | None = None) -> None:
        self.id = rid
        self.name = name
        self.members = members or []


class FakeMember:
    def __init__(self, *role_ids: int) -> None:
        self.roles = [FakeRole(r) for r in role_ids]


class FakeGuild:
    def __init__(self, members: list[FakeMember]) -> None:
        self.members = members


class _RosterMember:
    def __init__(self, uid: int, display_name: str) -> None:
        self.id = uid
        self.display_name = display_name

    @property
    def mention(self) -> str:
        return f"<@{self.id}>"


class _RosterGuild:
    def __init__(self, roles: list[FakeRole]) -> None:
        self._roles = {r.id: r for r in roles}

    def get_role(self, rid: int) -> FakeRole | None:
        return self._roles.get(rid)


# ---------------------------------------------------------------------------
# collect_counts — the one-pass current-holder math
# ---------------------------------------------------------------------------


def test_collect_counts_tallies_each_role():
    guild = FakeGuild([FakeMember(10), FakeMember(10), FakeMember(20)])
    per_role, total = counter.collect_counts(guild, [10, 20])
    assert per_role == {10: 2, 20: 1}
    assert total == 3


def test_collect_counts_distinct_total_never_double_counts():
    # One member holds BOTH menu roles → counted once in the distinct total.
    guild = FakeGuild([FakeMember(10, 20), FakeMember(10)])
    per_role, total = counter.collect_counts(guild, [10, 20])
    assert per_role == {10: 2, 20: 1}
    assert total == 2  # two distinct members, not three role-holdings


def test_collect_counts_role_with_no_holders_is_zero():
    guild = FakeGuild([FakeMember(10)])
    per_role, total = counter.collect_counts(guild, [10, 20, 30])
    assert per_role == {10: 1, 20: 0, 30: 0}
    assert total == 1


def test_collect_counts_ignores_roles_outside_the_menu():
    guild = FakeGuild([FakeMember(10, 999)])  # 999 isn't a menu role
    per_role, total = counter.collect_counts(guild, [10])
    assert per_role == {10: 1}
    assert total == 1


def test_collect_counts_empty_role_list():
    guild = FakeGuild([FakeMember(10)])
    assert counter.collect_counts(guild, []) == ({}, 0)


def test_collect_counts_tolerates_unchunked_guild():
    """A guild with no cached members yields zeros, never an error."""
    per_role, total = counter.collect_counts(SimpleNamespace(members=None), [10])
    assert per_role == {10: 0}
    assert total == 0


# ---------------------------------------------------------------------------
# format helpers
# ---------------------------------------------------------------------------


def test_format_count_badge():
    assert counter.format_count(12) == "👥 12"


def test_format_total_pluralises():
    assert counter.format_total(1) == "👥 1 person signed up"
    assert counter.format_total(0) == "👥 0 people signed up"
    assert counter.format_total(5) == "👥 5 people signed up"


# ---------------------------------------------------------------------------
# build_roster_embed — "who's in" per option
# ---------------------------------------------------------------------------


def _roster_menu() -> dict:
    return {"menu_id": 1, "title": "Event RSVP", "theme": "announcement"}


def test_roster_lists_each_option_with_its_holders():
    going = FakeRole(10, "Going", [_RosterMember(1, "Alice"), _RosterMember(2, "Bob")])
    maybe = FakeRole(20, "Maybe", [])
    guild = _RosterGuild([going, maybe])
    options = [
        {"role_id": 10, "label": "Going", "emoji": None},
        {"role_id": 20, "label": "Maybe", "emoji": None},
    ]
    embed = counter.build_roster_embed(_roster_menu(), options, guild)
    assert embed.title == "👥 Who's in — Event RSVP"
    going_field = next(f for f in embed.fields if f.name.startswith("Going"))
    assert going_field.name == "Going · 2"
    assert "<@1>" in going_field.value and "<@2>" in going_field.value
    maybe_field = next(f for f in embed.fields if f.name.startswith("Maybe"))
    assert maybe_field.name == "Maybe · 0"
    assert maybe_field.value == "—"


def test_roster_skips_deleted_roles():
    going = FakeRole(10, "Going", [_RosterMember(1, "Alice")])
    guild = _RosterGuild([going])  # role 20 was deleted (not resolvable)
    options = [{"role_id": 10, "label": "Going"}, {"role_id": 20, "label": "Gone"}]
    embed = counter.build_roster_embed(_roster_menu(), options, guild)
    assert [f.name for f in embed.fields] == ["Going · 1"]


def test_roster_with_no_live_roles_has_a_description():
    guild = _RosterGuild([])
    embed = counter.build_roster_embed(_roster_menu(), [{"role_id": 99}], guild)
    assert not embed.fields
    assert embed.description


def test_join_members_truncates_with_tail():
    # 200 members of ~6-char mentions blow past the 1024 field cap → truncated.
    members = [_RosterMember(i, f"U{i}") for i in range(200)]
    text = counter._join_members(members)
    assert len(text) <= counter._ROSTER_FIELD_CAP
    assert "more" in text  # the elided-count tail is present


def test_join_members_empty_is_dash():
    assert counter._join_members([]) == "—"


# ---------------------------------------------------------------------------
# schedule_count_refresh — debounced, coalescing
# ---------------------------------------------------------------------------


def test_schedule_refresh_with_no_message_is_noop():
    # No running loop needed — returns before touching asyncio.
    counter.schedule_count_refresh(None, 1)


@pytest.mark.asyncio
async def test_schedule_refresh_coalesces_a_burst():
    """A second click while a refresh is pending does not spawn a second task."""
    counter._pending.clear()
    message = SimpleNamespace(id=555)
    gate = asyncio.Event()

    async def _slow(_message, _menu_id):
        await gate.wait()

    with patch.object(counter, "_run_refresh", side_effect=_slow) as run:
        counter.schedule_count_refresh(message, 7)
        counter.schedule_count_refresh(message, 7)  # coalesced — same window
        await asyncio.sleep(0)
        assert run.call_count == 1
        assert 555 in counter._pending
    gate.set()
    await asyncio.gather(*list(counter._pending.values()), return_exceptions=True)
    counter._pending.clear()


@pytest.mark.asyncio
async def test_run_refresh_edits_message_with_live_counts():
    """The trailing edit re-reads the menu + options and re-renders the embed."""
    counter._pending.clear()
    rendered = discord.Embed(title="rerendered")
    message = MagicMock()
    message.id = 555
    message.guild = SimpleNamespace(members=[])
    message.attachments = []
    message.edit = AsyncMock()

    opt = SimpleNamespace(role_id=10, emoji=None, label="Going")
    with (
        patch("asyncio.sleep", new=AsyncMock()),
        patch(
            "services.reaction_role_service.get_menu",
            new=AsyncMock(return_value={"menu_id": 7, "show_counts": True}),
        ),
        patch(
            "services.reaction_role_service.get_menu_options",
            new=AsyncMock(return_value=[opt]),
        ),
        patch(
            "views.roles.role_menu_view.build_menu_embed",
            return_value=rendered,
        ) as build,
    ):
        await counter._run_refresh(message, 7)

    build.assert_called_once()
    message.edit.assert_awaited_once()
    assert message.edit.await_args.kwargs["embed"] is rendered
    assert 555 not in counter._pending  # cleaned up in finally


@pytest.mark.asyncio
async def test_run_refresh_bails_when_counts_turned_off_midwindow():
    """If show_counts was cleared during the debounce window, don't edit."""
    counter._pending.clear()
    message = MagicMock()
    message.id = 556
    message.guild = SimpleNamespace(members=[])
    message.edit = AsyncMock()
    with (
        patch("asyncio.sleep", new=AsyncMock()),
        patch(
            "services.reaction_role_service.get_menu",
            new=AsyncMock(return_value={"menu_id": 7, "show_counts": False}),
        ),
    ):
        await counter._run_refresh(message, 7)
    message.edit.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_refresh_swallows_edit_failure():
    """A failed edit never propagates — the role mutation already succeeded."""
    counter._pending.clear()
    message = MagicMock()
    message.id = 557
    message.guild = SimpleNamespace(members=[])
    message.attachments = []
    message.edit = AsyncMock(side_effect=RuntimeError("boom"))
    with (
        patch("asyncio.sleep", new=AsyncMock()),
        patch(
            "services.reaction_role_service.get_menu",
            new=AsyncMock(return_value={"menu_id": 7, "show_counts": True}),
        ),
        patch(
            "services.reaction_role_service.get_menu_options",
            new=AsyncMock(return_value=[]),
        ),
        patch("views.roles.role_menu_view.build_menu_embed", return_value=discord.Embed()),
    ):
        await counter._run_refresh(message, 7)  # must not raise
    assert 557 not in counter._pending
