"""Tests for the private control API (``disbot/control_api.py``).

Covers the three safety-critical properties of the live-editor foundation:
dormant-by-default, shared-secret auth, and the identity→authority bridge
resolving the live member's tier. Pure-function + handler tests with stubbed
bot/guild/member (mirrors ``test_healthserver.py``).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from aiohttp import web

import control_api

TOKEN = "s3cret-control-token"


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


def _perms(*, administrator=False, manage_guild=False, moderate_members=False):
    p = MagicMock()
    p.administrator = administrator
    p.manage_guild = manage_guild
    p.moderate_members = moderate_members
    return p


def _member(user_id, **perm_kwargs):
    m = MagicMock()
    m.id = user_id
    m.guild_permissions = _perms(**perm_kwargs)
    return m


def _guild(guild_id, owner_id, *, name="Guild", members=None):
    members = members or {}
    g = MagicMock()
    g.id = guild_id
    g.owner_id = owner_id
    g.name = name
    g.get_member = lambda uid: members.get(uid)
    return g


def _bot(*, guilds=None):
    guilds = guilds or {}
    b = MagicMock()
    b.get_guild = lambda gid: guilds.get(gid)
    return b


def _request(*, headers=None, query=None, bot=None):
    req = MagicMock()
    req.headers = headers or {}
    req.query = query or {}
    req.app = {"bot": bot}
    return req


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_is_authorized_requires_matching_bearer():
    assert control_api.is_authorized(f"Bearer {TOKEN}", TOKEN) is True
    assert control_api.is_authorized("Bearer wrong", TOKEN) is False
    assert control_api.is_authorized(TOKEN, TOKEN) is False  # missing "Bearer "
    assert control_api.is_authorized(None, TOKEN) is False
    assert control_api.is_authorized("", TOKEN) is False


def test_is_authorized_never_true_when_dormant():
    # No configured token => never authorised, regardless of what is presented.
    assert control_api.is_authorized("Bearer anything", None) is False
    assert control_api.is_authorized("Bearer anything", "") is False


def test_control_token_reads_env(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    assert control_api.control_token() is None
    monkeypatch.setenv("CONTROL_API_TOKEN", "  abc  ")
    assert control_api.control_token() == "abc"  # stripped


# ---------------------------------------------------------------------------
# Dormant-by-default registration
# ---------------------------------------------------------------------------


def _registered_paths(app: web.Application) -> set[str]:
    return {route.resource.canonical for route in app.router.routes()}


def test_routes_dormant_without_token(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    app = web.Application()
    assert control_api.register_control_routes(app, _bot()) is False
    assert "/control/ping" not in _registered_paths(app)


def test_routes_registered_with_token(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    app = web.Application()
    assert control_api.register_control_routes(app, _bot()) is True
    paths = _registered_paths(app)
    assert "/control/ping" in paths
    assert "/control/authority" in paths


# ---------------------------------------------------------------------------
# Authority bridge
# ---------------------------------------------------------------------------


def test_resolve_authority_guild_not_found():
    result = control_api.resolve_authority(_bot(), 111, 222)
    assert result["guild_found"] is False
    assert result["member_found"] is False
    assert result["tier"] is None


def test_resolve_authority_member_not_found():
    guild = _guild(111, owner_id=999, members={})
    result = control_api.resolve_authority(_bot(guilds={111: guild}), 111, 222)
    assert result["guild_found"] is True
    assert result["member_found"] is False
    assert result["guild_name"] == "Guild"
    assert result["tier"] is None


def test_resolve_authority_admin_member():
    member = _member(222, administrator=True)
    guild = _guild(111, owner_id=999, members={222: member})
    result = control_api.resolve_authority(_bot(guilds={111: guild}), 111, 222)
    assert result["member_found"] is True
    assert result["tier"] == "administrator"
    assert result["is_admin"] is True
    assert result["is_owner"] is False


def test_resolve_authority_owner_and_plain_member():
    owner = _member(999)
    plain = _member(222)
    guild = _guild(111, owner_id=999, members={999: owner, 222: plain})
    bot = _bot(guilds={111: guild})

    owner_res = control_api.resolve_authority(bot, 111, 999)
    assert owner_res["tier"] == "owner"
    assert owner_res["is_owner"] is True

    plain_res = control_api.resolve_authority(bot, 111, 222)
    assert plain_res["tier"] == "user"
    assert plain_res["is_admin"] is False


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ping_requires_auth(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    resp = await control_api._ping_handler(_request(headers={}))
    assert resp.status == 401

    resp = await control_api._ping_handler(
        _request(headers={"Authorization": f"Bearer {TOKEN}"}),
    )
    assert resp.status == 200
    assert json.loads(resp.text)["status"] == "ok"


@pytest.mark.asyncio
async def test_authority_handler_happy_path(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    member = _member(222, administrator=True)
    guild = _guild(111, owner_id=999, members={222: member})
    bot = _bot(guilds={111: guild})

    resp = await control_api._authority_handler(
        _request(
            headers={"Authorization": f"Bearer {TOKEN}"},
            query={"guild_id": "111", "user_id": "222"},
            bot=bot,
        ),
    )
    assert resp.status == 200
    body = json.loads(resp.text)
    assert body["tier"] == "administrator"
    assert body["is_admin"] is True


@pytest.mark.asyncio
async def test_authority_handler_rejects_bad_auth_and_bad_params(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)

    # Bad auth → 401 (before any param parsing).
    resp = await control_api._authority_handler(
        _request(headers={"Authorization": "Bearer nope"}, query={"guild_id": "1"}),
    )
    assert resp.status == 401

    # Good auth, missing user_id → 400.
    resp = await control_api._authority_handler(
        _request(
            headers={"Authorization": f"Bearer {TOKEN}"},
            query={"guild_id": "111"},
            bot=_bot(),
        ),
    )
    assert resp.status == 400
