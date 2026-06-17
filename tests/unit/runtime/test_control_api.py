"""Tests for the private control API (``disbot/control_api.py``).

Covers the three safety-critical properties of the live-editor foundation:
dormant-by-default, shared-secret auth, and the identity→authority bridge
resolving the live member's tier. Pure-function + handler tests with stubbed
bot/guild/member (mirrors ``test_healthserver.py``).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

import control_api

TOKEN = "s3cret-control-token"

# Sentinel: a request whose .json() raises (no/invalid body).
_NO_BODY = object()


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


def _request(*, headers=None, query=None, bot=None, body=_NO_BODY):
    req = MagicMock()
    req.headers = headers or {}
    req.query = query or {}
    req.app = {"bot": bot}

    async def _json():
        if body is _NO_BODY:
            raise ValueError("no JSON body")
        return body

    req.json = _json
    return req


def _auth(extra=None):
    """Authorization header carrying the test token (+ optional extra headers)."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if extra:
        headers.update(extra)
    return headers


def _bot_with_member(*, guild_id=111, user_id=222, owner_id=999, administrator=True):
    """A bot whose single guild contains one resolvable member."""
    member = _member(user_id, administrator=administrator)
    guild = _guild(guild_id, owner_id=owner_id, members={user_id: member})
    return _bot(guilds={guild_id: guild}), guild, member


@pytest.fixture(autouse=True)
def _reset_control_write_limiter():
    """Isolate the in-process write rate limiter across tests (R3 hardening)."""
    control_api._reset_rate_limiter_for_tests()
    yield
    control_api._reset_rate_limiter_for_tests()


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
    # Phase E read endpoints register alongside the writes (still token-gated).
    assert "/control/settings/current" in paths
    assert "/control/help/catalogue" in paths
    # Mutation endpoints register alongside the reads (still token-gated).
    assert "/control/settings" in paths
    assert "/control/help/overlay" in paths
    assert "/control/help/home" in paths
    assert "/control/help/reset" in paths
    assert "/control/routing" in paths


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


# ---------------------------------------------------------------------------
# Mutation: shared write-context (auth / parse / resolution)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mutation_requires_auth(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member()
    # No Authorization header → 401, before any body parsing.
    resp = await control_api._settings_set_handler(
        _request(body={"guild_id": 111, "user_id": 222}, bot=bot),
    )
    assert resp.status == 401


@pytest.mark.asyncio
async def test_mutation_rejects_non_json_body(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member()
    resp = await control_api._settings_set_handler(
        _request(headers=_auth(), bot=bot),  # _NO_BODY → .json() raises
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_mutation_requires_guild_and_user_ids(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member()
    resp = await control_api._settings_set_handler(
        _request(headers=_auth(), body={"subsystem": "x", "name": "y"}, bot=bot),
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_mutation_guild_not_found_is_404(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    resp = await control_api._settings_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "subsystem": "x",
                "name": "y",
                "value": 1,
            },
            bot=_bot(),  # bot is in no guilds
        ),
    )
    assert resp.status == 404


@pytest.mark.asyncio
async def test_mutation_member_not_found_is_403(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    guild = _guild(111, owner_id=999, members={})  # user 222 is not a member
    bot = _bot(guilds={111: guild})
    resp = await control_api._settings_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "subsystem": "x",
                "name": "y",
                "value": 1,
            },
            bot=bot,
        ),
    )
    assert resp.status == 403


# ---------------------------------------------------------------------------
# Mutation: settings → SettingsMutationPipeline.set_value
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_rate_limit_returns_429(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    # Tighten the per-(guild, user) write budget to 1 for the test.
    monkeypatch.setattr(control_api._write_limiter, "max_events", 1)
    bot, _g, _m = _bot_with_member(administrator=True)
    body = {
        "guild_id": 111,
        "user_id": 222,
        "subsystem": "moderation",
        "name": "warn_threshold",
        "value": 1,
    }
    # Stub the seam so the first (allowed) write succeeds without a DB.
    result = SimpleNamespace(
        mutation_id="m1",
        subsystem="moderation",
        name="warn_threshold",
        settings_key="WARN_THRESHOLD",
        old_value=1,
        new_value=1,
    )
    pipeline = MagicMock()
    pipeline.set_value = AsyncMock(return_value=result)
    monkeypatch.setattr(
        "services.settings_mutation.SettingsMutationPipeline",
        lambda: pipeline,
    )
    first = await control_api._settings_set_handler(
        _request(headers=_auth(), body=body, bot=bot),
    )
    assert first.status == 200
    second = await control_api._settings_set_handler(
        _request(headers=_auth(), body=body, bot=bot),
    )
    assert second.status == 429
    assert "rate limit" in json.loads(second.text)["error"]


@pytest.mark.asyncio
async def test_settings_set_happy_path(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, guild, member = _bot_with_member()
    result = SimpleNamespace(
        mutation_id="m1",
        subsystem="moderation",
        name="warn_threshold",
        settings_key="WARN_THRESHOLD",
        old_value=3,
        new_value=5,
    )
    set_value = AsyncMock(return_value=result)
    pipeline = MagicMock()
    pipeline.set_value = set_value
    monkeypatch.setattr(
        "services.settings_mutation.SettingsMutationPipeline",
        lambda: pipeline,
    )

    resp = await control_api._settings_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "subsystem": "moderation",
                "name": "warn_threshold",
                "value": 5,
            },
            bot=bot,
        ),
    )
    assert resp.status == 200
    payload = json.loads(resp.text)
    assert payload["ok"] is True
    assert payload["new_value"] == 5
    # The live guild + resolved member are passed to the seam (not raw ids).
    set_value.assert_awaited_once_with(guild, "moderation", "warn_threshold", 5, member)


@pytest.mark.asyncio
async def test_settings_missing_value_is_400(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member()
    resp = await control_api._settings_set_handler(
        _request(
            headers=_auth(),
            body={"guild_id": 111, "user_id": 222, "subsystem": "m", "name": "n"},
            bot=bot,
        ),
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_settings_maps_unauthorized_to_403(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    from services.settings_mutation import UnauthorizedSettingsMutationError

    bot, _g, _m = _bot_with_member(administrator=False)
    pipeline = MagicMock()
    pipeline.set_value = AsyncMock(
        side_effect=UnauthorizedSettingsMutationError("missing capability"),
    )
    monkeypatch.setattr(
        "services.settings_mutation.SettingsMutationPipeline",
        lambda: pipeline,
    )
    resp = await control_api._settings_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "subsystem": "m",
                "name": "n",
                "value": 1,
            },
            bot=bot,
        ),
    )
    assert resp.status == 403
    assert json.loads(resp.text)["kind"] == "UnauthorizedSettingsMutationError"


@pytest.mark.asyncio
async def test_settings_maps_validation_to_400(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    from services.settings_mutation import SettingsValidationError

    bot, _g, _m = _bot_with_member()
    pipeline = MagicMock()
    pipeline.set_value = AsyncMock(side_effect=SettingsValidationError("out of range"))
    monkeypatch.setattr(
        "services.settings_mutation.SettingsMutationPipeline",
        lambda: pipeline,
    )
    resp = await control_api._settings_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "subsystem": "m",
                "name": "n",
                "value": 999,
            },
            bot=bot,
        ),
    )
    assert resp.status == 400


# ---------------------------------------------------------------------------
# Mutation: help overlay / home / reset → help_overlay_mutation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_overlay_forwards_only_present_fields(monkeypatch):
    """Omitted override fields must NOT be passed (so the seam leaves them UNSET)."""
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, member = _bot_with_member()
    result = SimpleNamespace(
        mutation_id="h1",
        entity_kind="hub",
        entity_key="games",
        new={"display_hidden": True, "display_name": None, "description": None},
    )
    fake = AsyncMock(return_value=result)
    monkeypatch.setattr("services.help_overlay_mutation.set_overlay_fields", fake)

    resp = await control_api._help_overlay_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "entity_kind": "hub",
                "entity_key": "games",
                "display_hidden": True,  # only this one sent
            },
            bot=bot,
        ),
    )
    assert resp.status == 200
    _args, kwargs = fake.await_args
    assert kwargs["actor"] is member
    assert kwargs["display_hidden"] is True
    # display_name / description omitted → not forwarded → seam keeps them UNSET.
    assert "display_name" not in kwargs
    assert "description" not in kwargs


@pytest.mark.asyncio
async def test_help_overlay_requires_entity(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member()
    resp = await control_api._help_overlay_handler(
        _request(
            headers=_auth(),
            body={"guild_id": 111, "user_id": 222, "display_hidden": True},
            bot=bot,
        ),
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_help_overlay_maps_unauthorized_to_403(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    from services.help_overlay_mutation import UnauthorizedHelpOverlayMutationError

    bot, _g, _m = _bot_with_member(administrator=False)
    monkeypatch.setattr(
        "services.help_overlay_mutation.set_overlay_fields",
        AsyncMock(side_effect=UnauthorizedHelpOverlayMutationError("not admin")),
    )
    resp = await control_api._help_overlay_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "entity_kind": "hub",
                "entity_key": "games",
                "display_hidden": True,
            },
            bot=bot,
        ),
    )
    assert resp.status == 403


@pytest.mark.asyncio
async def test_help_home_and_reset_happy_paths(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member()

    home_result = SimpleNamespace(mutation_id="hm1", new={"title": "Welcome"})
    monkeypatch.setattr(
        "services.help_overlay_mutation.set_home_message",
        AsyncMock(return_value=home_result),
    )
    resp = await control_api._help_home_handler(
        _request(
            headers=_auth(),
            body={"guild_id": 111, "user_id": 222, "title": "Welcome"},
            bot=bot,
        ),
    )
    assert resp.status == 200
    assert json.loads(resp.text)["new"] == {"title": "Welcome"}

    reset_result = SimpleNamespace(mutation_id="r1", prev={"rows_removed": 4})
    monkeypatch.setattr(
        "services.help_overlay_mutation.reset_guild_overlay",
        AsyncMock(return_value=reset_result),
    )
    resp = await control_api._help_reset_handler(
        _request(
            headers=_auth(),
            body={"guild_id": 111, "user_id": 222},
            bot=bot,
        ),
    )
    assert resp.status == 200
    assert json.loads(resp.text)["prev"] == {"rows_removed": 4}


# ---------------------------------------------------------------------------
# Mutation: cog routing → command_routing.set_policy (admin-gated here)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_routing_requires_administrator(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=False)
    resp = await control_api._routing_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "cog_name": "MiningCog",
                "enabled": False,
            },
            bot=bot,
        ),
    )
    assert resp.status == 403


@pytest.mark.asyncio
async def test_routing_happy_path_guild_scope(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, member = _bot_with_member(administrator=True)
    result = SimpleNamespace(
        mutation_id="rt1",
        cog_name="MiningCog",
        scope_type="guild",
        scope_id=None,
        old_enabled=True,
        new_enabled=False,
    )
    fake = AsyncMock(return_value=result)
    monkeypatch.setattr("services.command_routing.set_policy", fake)

    resp = await control_api._routing_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "cog_name": "MiningCog",
                "enabled": False,
            },
            bot=bot,
        ),
    )
    assert resp.status == 200
    assert json.loads(resp.text)["new_enabled"] is False
    _args, kwargs = fake.await_args
    assert kwargs["scope_type"] == "guild"
    assert kwargs["scope_id"] is None  # guild scope forces scope_id None
    assert kwargs["actor_id"] == member.id


@pytest.mark.asyncio
async def test_routing_rejects_bad_scope(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=True)

    # Unknown scope_type → 400.
    resp = await control_api._routing_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "cog_name": "MiningCog",
                "enabled": True,
                "scope_type": "server",
            },
            bot=bot,
        ),
    )
    assert resp.status == 400

    # channel scope without scope_id → 400.
    resp = await control_api._routing_set_handler(
        _request(
            headers=_auth(),
            body={
                "guild_id": 111,
                "user_id": 222,
                "cog_name": "MiningCog",
                "enabled": True,
                "scope_type": "channel",
            },
            bot=bot,
        ),
    )
    assert resp.status == 400


# ---------------------------------------------------------------------------
# Phase E reads: shared read-context (auth / params / resolution)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_requires_auth(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member()
    resp = await control_api._settings_current_handler(
        _request(query={"guild_id": "111", "user_id": "222"}, bot=bot),  # no auth
    )
    assert resp.status == 401


@pytest.mark.asyncio
async def test_read_requires_int_params(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member()
    resp = await control_api._settings_current_handler(
        _request(headers=_auth(), query={"guild_id": "111"}, bot=bot),  # no user_id
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_read_guild_not_found_is_404(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    resp = await control_api._settings_current_handler(
        _request(
            headers=_auth(),
            query={"guild_id": "111", "user_id": "222"},
            bot=_bot(),  # in no guilds
        ),
    )
    assert resp.status == 404


@pytest.mark.asyncio
async def test_read_member_not_found_is_403(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    guild = _guild(111, owner_id=999, members={})  # user 222 not a member
    bot = _bot(guilds={111: guild})
    resp = await control_api._settings_current_handler(
        _request(headers=_auth(), query={"guild_id": "111", "user_id": "222"}, bot=bot),
    )
    assert resp.status == 403


# ---------------------------------------------------------------------------
# Phase E reads: settings/current
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_settings_current_happy_path(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=True)
    grouped = {
        "moderation": [
            {
                "name": "warn_threshold",
                "settings_key": "WARN_THRESHOLD",
                "value": 3,
                "default": 3,
                "provenance": "default",
                "valid": True,
                "value_type": "int",
                "hint": "warnings before action",
                "allowed_values": [],
                "capability_required": "",
            },
        ],
    }
    monkeypatch.setattr(
        control_api,
        "_resolve_guild_settings",
        AsyncMock(return_value=grouped),
    )
    resp = await control_api._settings_current_handler(
        _request(headers=_auth(), query={"guild_id": "111", "user_id": "222"}, bot=bot),
    )
    assert resp.status == 200
    body = json.loads(resp.text)
    assert body["ok"] is True
    assert body["guild_id"] == 111
    assert body["subsystems"]["moderation"][0]["value"] == 3


@pytest.mark.asyncio
async def test_settings_current_requires_admin(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=False)
    # Resolver must never be consulted when the admin gate rejects.
    resolver = AsyncMock(return_value={})
    monkeypatch.setattr(control_api, "_resolve_guild_settings", resolver)
    resp = await control_api._settings_current_handler(
        _request(headers=_auth(), query={"guild_id": "111", "user_id": "222"}, bot=bot),
    )
    assert resp.status == 403
    resolver.assert_not_awaited()


# ---------------------------------------------------------------------------
# Phase E reads: help/overlay
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_overlay_get_happy_path(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=True)
    overlay = SimpleNamespace(
        rows=[
            SimpleNamespace(
                entity_kind="hub",
                entity_key="games",
                display_hidden=True,
                display_name=None,
                description=None,
            ),
        ],
        home=SimpleNamespace(title="Welcome", body="Hi", color=123),
    )
    monkeypatch.setattr(
        "services.help_overlay.get_guild_help_overlay",
        AsyncMock(return_value=overlay),
    )
    resp = await control_api._help_overlay_get_handler(
        _request(headers=_auth(), query={"guild_id": "111", "user_id": "222"}, bot=bot),
    )
    assert resp.status == 200
    body = json.loads(resp.text)
    assert body["rows"][0]["entity_key"] == "games"
    assert body["rows"][0]["display_hidden"] is True
    assert body["home"] == {"title": "Welcome", "body": "Hi", "color": 123}


@pytest.mark.asyncio
async def test_help_overlay_get_empty_home_is_null(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=True)
    overlay = SimpleNamespace(rows=[], home=None)
    monkeypatch.setattr(
        "services.help_overlay.get_guild_help_overlay",
        AsyncMock(return_value=overlay),
    )
    resp = await control_api._help_overlay_get_handler(
        _request(headers=_auth(), query={"guild_id": "111", "user_id": "222"}, bot=bot),
    )
    assert resp.status == 200
    body = json.loads(resp.text)
    assert body["rows"] == []
    assert body["home"] is None


@pytest.mark.asyncio
async def test_help_overlay_get_requires_admin(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=False)
    resp = await control_api._help_overlay_get_handler(
        _request(headers=_auth(), query={"guild_id": "111", "user_id": "222"}, bot=bot),
    )
    assert resp.status == 403


# ---------------------------------------------------------------------------
# Phase E reads: help/catalogue (token-only — global defaults)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_catalogue_token_only(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    catalogue = SimpleNamespace(
        hubs=[
            SimpleNamespace(
                key="games",
                entry=SimpleNamespace(
                    display_name="Games",
                    purpose="Play games",
                    minimum_tier="user",
                ),
                host_subsystem="games",
            ),
        ],
        subsystems=[
            SimpleNamespace(
                key="moderation",
                display_name="Moderation",
                description="Keep order",
                emoji="🛡️",
                visibility_tier="moderator",
                parent_hub="moderation",
                top_level=False,
            ),
        ],
    )
    monkeypatch.setattr(
        "services.help_catalogue.build_help_catalogue",
        lambda: catalogue,
    )
    # No guild/user needed — token alone authorizes the global defaults.
    resp = await control_api._help_catalogue_handler(_request(headers=_auth()))
    assert resp.status == 200
    body = json.loads(resp.text)
    assert body["hubs"][0]["display_name"] == "Games"
    assert body["subsystems"][0]["key"] == "moderation"


@pytest.mark.asyncio
async def test_help_catalogue_requires_token(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    resp = await control_api._help_catalogue_handler(_request(headers={}))
    assert resp.status == 401


# ---------------------------------------------------------------------------
# Phase E reads: routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_routing_get_happy_path(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=True)
    updated = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)
    rows = [
        {
            "scope_type": "guild",
            "scope_id": None,
            "cog_name": "MiningCog",
            "enabled": False,
            "actor_id": 5,
            "updated_at": updated,
        },
    ]
    monkeypatch.setattr(
        "services.command_routing.list_for_guild",
        AsyncMock(return_value=rows),
    )
    resp = await control_api._routing_get_handler(
        _request(headers=_auth(), query={"guild_id": "111", "user_id": "222"}, bot=bot),
    )
    assert resp.status == 200
    body = json.loads(resp.text)
    row = body["rows"][0]
    assert row["cog_name"] == "MiningCog"
    assert row["enabled"] is False
    # datetime is serialised to an ISO string (JSON-safe).
    assert row["updated_at"] == updated.isoformat()


@pytest.mark.asyncio
async def test_routing_get_requires_admin(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", TOKEN)
    bot, _g, _m = _bot_with_member(administrator=False)
    resp = await control_api._routing_get_handler(
        _request(headers=_auth(), query={"guild_id": "111", "user_id": "222"}, bot=bot),
    )
    assert resp.status == 403
