"""Tests for the dashboard's Discord OAuth helpers (``dashboard/auth.py``).

Pure-logic + dormant-by-default coverage (stdlib only, so these run in CI). The
live Discord token/identity HTTP calls are integration-tested manually once the
OAuth app is configured; here we pin the config gating, the consent URL, and the
admin-guild filter.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DASHBOARD = Path(__file__).resolve().parents[3] / "dashboard"
if str(_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD))

import auth  # noqa: E402

_OAUTH_ENV = (
    "DISCORD_OAUTH_CLIENT_ID",
    "DISCORD_OAUTH_CLIENT_SECRET",
    "DISCORD_OAUTH_REDIRECT_URI",
)


def _configure(monkeypatch):
    monkeypatch.setenv("DISCORD_OAUTH_CLIENT_ID", "appid123")
    monkeypatch.setenv("DISCORD_OAUTH_CLIENT_SECRET", "s3cret")
    monkeypatch.setenv(
        "DISCORD_OAUTH_REDIRECT_URI",
        "https://superbot-dashboard.up.railway.app/auth/callback",
    )


def test_oauth_dormant_by_default(monkeypatch):
    for var in _OAUTH_ENV:
        monkeypatch.delenv(var, raising=False)
    assert auth.oauth_config() is None
    assert auth.is_configured() is False
    assert auth.authorize_url("state") is None


def test_oauth_requires_all_three_vars(monkeypatch):
    for var in _OAUTH_ENV:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("DISCORD_OAUTH_CLIENT_ID", "appid123")
    # client secret + redirect still missing → still dormant.
    assert auth.is_configured() is False


def test_oauth_configured(monkeypatch):
    _configure(monkeypatch)
    assert auth.is_configured() is True
    cid, secret, redirect = auth.oauth_config()
    assert cid == "appid123"
    assert secret == "s3cret"
    assert redirect.endswith("/auth/callback")


def test_authorize_url_carries_state_scopes_and_redirect(monkeypatch):
    _configure(monkeypatch)
    url = auth.authorize_url("xyz-state")
    assert url.startswith("https://discord.com/oauth2/authorize?")
    assert "client_id=appid123" in url
    assert "state=xyz-state" in url
    assert "scope=identify+guilds" in url
    assert "response_type=code" in url
    assert "auth%2Fcallback" in url  # the redirect uri, url-encoded


def test_admin_guilds_filters_to_owner_or_administrator():
    guilds = [
        {"id": "1", "name": "Owned", "owner": True, "permissions": "0"},
        {"id": "2", "name": "Admin", "owner": False, "permissions": "8"},  # 0x8 = ADMIN
        {"id": "3", "name": "Member", "owner": False, "permissions": "0"},
        {"id": "4", "name": "Manager", "owner": False, "permissions": "32"},  # MANAGE_GUILD only
        {"id": "5", "name": "AdminPlus", "owner": False, "permissions": "8589934592"},
    ]
    keep = {g["id"] for g in auth.admin_guilds(guilds)}
    assert keep == {"1", "2"}  # owner OR administrator bit only


def test_admin_guilds_tolerates_bad_shapes():
    guilds = [
        {"id": "1", "owner": True},  # no permissions key → owner still kept
        "not-a-dict",
        {"id": "2", "permissions": "not-an-int"},  # bad perms → coerced to 0, dropped
    ]
    keep = {g["id"] for g in auth.admin_guilds(guilds)}
    assert keep == {"1"}


@pytest.mark.asyncio
async def test_exchange_code_requires_configuration(monkeypatch):
    for var in _OAUTH_ENV:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError):
        await auth.exchange_code("any-code")
