"""Tests for the read-only guild introspection service and its AI tools.

Pins:

* overview / roles / channels shape and the privacy tiering (member
  count + per-role member counts + member lookup only when opted in).
* channel listing is filtered by the asking member's visibility.
* ``build_registry`` exposes the server tools only when a live guild is
  supplied, and gates the member tools behind the opt-in flag.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from core.runtime.ai.contracts import AIScope
from services import ai_tools, guild_introspection_service as gintro


def _perms(**flags):
    return SimpleNamespace(**flags)


def _role(name, position, *, admin=False, members=(), hoist=False):
    return SimpleNamespace(
        name=name,
        position=position,
        hoist=hoist,
        mentionable=False,
        permissions=_perms(administrator=admin, manage_guild=False, manage_roles=False,
                           manage_channels=False, ban_members=False, kick_members=False,
                           manage_messages=False),
        members=list(members),
    )


def _channel(name, *, kind="text", category=None, topic=None, viewer_can_view=True):
    def permissions_for(_member):
        return _perms(view_channel=viewer_can_view)

    return SimpleNamespace(
        name=name,
        category=SimpleNamespace(name=category) if category else None,
        topic=topic,
        permissions_for=permissions_for,
    )


def _guild(**kw):
    base = dict(
        name="My Server",
        description="A test guild",
        owner=SimpleNamespace(display_name="Alice"),
        owner_id=1,
        created_at=datetime(2021, 6, 1, tzinfo=timezone.utc),
        premium_tier=2,
        premium_subscription_count=7,
        member_count=42,
        text_channels=[],
        voice_channels=[],
        categories=[],
        roles=[],
        members=[],
    )
    base.update(kw)
    return SimpleNamespace(**base)


# --- overview ----------------------------------------------------------


def test_overview_excludes_member_count_by_default():
    guild = _guild(
        text_channels=[_channel("general"), _channel("memes")],
        voice_channels=[_channel("voice", kind="voice")],
        roles=[_role("@everyone", 0), _role("Admin", 5, admin=True)],
    )
    out = gintro.server_overview(guild)
    assert out["name"] == "My Server"
    assert out["owner"] == "Alice"
    assert out["created"] == "2021-06-01"
    assert out["counts"] == {
        "text_channels": 2,
        "voice_channels": 1,
        "categories": 0,
        "roles": 1,  # @everyone dropped
    }
    assert "member_count" not in out


def test_overview_includes_member_count_when_opted_in():
    out = gintro.server_overview(_guild(), include_members=True)
    assert out["member_count"] == 42


# --- roles -------------------------------------------------------------


def test_list_roles_sorted_high_to_low_with_privilege_summary():
    guild = _guild(
        roles=[
            _role("@everyone", 0),
            _role("Member", 1, members=["a", "b"]),
            _role("Admin", 9, admin=True, members=["a"]),
        ],
    )
    out = gintro.list_roles(guild)
    names = [r["name"] for r in out["roles"]]
    assert names == ["Admin", "Member"]  # @everyone excluded, highest first
    assert out["roles"][0]["privileges"] == "administrator"
    # Member counts omitted unless opted in.
    assert "member_count" not in out["roles"][0]


def test_list_roles_member_counts_when_opted_in():
    guild = _guild(roles=[_role("@everyone", 0), _role("Member", 1, members=["a", "b"])])
    out = gintro.list_roles(guild, include_member_counts=True)
    assert out["roles"][0]["member_count"] == 2


# --- channels ----------------------------------------------------------


def test_list_channels_filters_by_member_visibility():
    guild = _guild(
        text_channels=[
            _channel("general", topic="hi", viewer_can_view=True),
            _channel("staff-only", viewer_can_view=False),
        ],
    )
    out = gintro.list_channels(guild, member=SimpleNamespace())
    names = [c["name"] for c in out["channels"]]
    assert names == ["general"]
    assert out["channels"][0]["topic"] == "hi"


def test_list_channels_lists_all_when_no_member():
    guild = _guild(
        text_channels=[_channel("a", viewer_can_view=False), _channel("b")],
    )
    out = gintro.list_channels(guild, member=None)
    assert {c["name"] for c in out["channels"]} == {"a", "b"}


# --- member lookup -----------------------------------------------------


def test_lookup_member_matches_by_substring():
    members = [
        SimpleNamespace(display_name="Bob", name="bob123", global_name=None,
                        joined_at=datetime(2022, 1, 2, tzinfo=timezone.utc),
                        bot=False, id=2, roles=[_role("@everyone", 0), _role("Mod", 3)]),
        SimpleNamespace(display_name="Carol", name="carol", global_name=None,
                        joined_at=None, bot=False, id=3, roles=[]),
    ]
    out = gintro.lookup_member(_guild(members=members), "bob")
    assert out["found"] is True
    assert len(out["matches"]) == 1
    assert out["matches"][0]["display_name"] == "Bob"
    assert out["matches"][0]["roles"] == ["Mod"]
    assert out["matches"][0]["joined"] == "2022-01-02"


def test_lookup_member_empty_query():
    out = gintro.lookup_member(_guild(), "")
    assert out["found"] is False


# --- registry wiring ---------------------------------------------------


def test_registry_omits_server_tools_without_guild():
    reg = ai_tools.build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "get_server_overview" not in set(reg.handlers)


def test_registry_includes_server_tools_with_guild(monkeypatch):
    # Member-data opt-in off (default): server structure tools present,
    # member lookup absent.
    monkeypatch.delenv("AI_SERVER_MEMBER_LOOKUP_ENABLED", raising=False)
    reg = ai_tools.build_registry(
        scope=AIScope.USER, guild_id=1, actor_id=2, guild=_guild(), member=SimpleNamespace(),
    )
    names = set(reg.handlers)
    assert {"get_server_overview", "list_server_roles", "list_server_channels"} <= names
    # Member lookup stays gated off by default.
    assert "lookup_member" not in names


def test_registry_member_lookup_appears_when_flag_on(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    monkeypatch.setenv("AI_SERVER_MEMBER_LOOKUP_ENABLED", "1")
    reg = ai_tools.build_registry(
        scope=AIScope.USER, guild_id=1, actor_id=2, guild=_guild(), member=SimpleNamespace(),
    )
    assert "lookup_member" in set(reg.handlers)


async def test_overview_handler_via_registry_includes_member_count_when_flag_on(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    monkeypatch.setenv("AI_SERVER_MEMBER_LOOKUP_ENABLED", "1")
    reg = ai_tools.build_registry(
        scope=AIScope.USER, guild_id=1, actor_id=2, guild=_guild(), member=SimpleNamespace(),
    )
    out = await reg.handlers["get_server_overview"]({})
    assert out["member_count"] == 42
