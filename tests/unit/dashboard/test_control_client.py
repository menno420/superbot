"""Tests for the dashboard's bot control-API client (``dashboard/control_client.py``).

Pure config gating + the dormant paths (stdlib only — no httpx import on these
paths — so they run in CI). Live HTTP calls are exercised by the bot-side
``test_control_api.py`` + manual integration once the token is configured.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DASHBOARD = Path(__file__).resolve().parents[3] / "dashboard"
if str(_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD))

import control_client  # noqa: E402


def test_dormant_without_token(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    assert control_client.control_config() is None
    assert control_client.is_configured() is False


def test_configured_defaults_base_url(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", "shared-secret")
    monkeypatch.delenv("CONTROL_API_URL", raising=False)
    base, token = control_client.control_config()
    assert token == "shared-secret"
    assert base == "http://worker.railway.internal:8080"  # default private host
    assert control_client.is_configured() is True


def test_configured_custom_base_url_is_trimmed(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", "shared-secret")
    monkeypatch.setenv("CONTROL_API_URL", "http://bot.internal:9000/")
    base, _token = control_client.control_config()
    assert base == "http://bot.internal:9000"  # trailing slash stripped


@pytest.mark.asyncio
async def test_post_dormant_returns_503(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    status, body = await control_client.post("/control/settings", {"x": 1})
    assert status == 503
    assert "not configured" in body["error"]


@pytest.mark.asyncio
async def test_get_authority_dormant_returns_none(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    assert await control_client.get_authority(111, 222) is None


@pytest.mark.asyncio
async def test_get_dormant_returns_503(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    status, body = await control_client.get("/control/settings/current", {"guild_id": 1})
    assert status == 503
    assert "not configured" in body["error"]


@pytest.mark.asyncio
async def test_get_manifest_dormant_returns_none(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    assert await control_client.get_manifest() is None


@pytest.mark.asyncio
async def test_get_manifest_returns_body_on_200(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", "shared-secret")

    async def _fake_get(path, params=None):
        assert path == "/control/manifest"
        return 200, {"ok": True, "commands": {"version": 1}, "panels": {"version": 1}}

    monkeypatch.setattr(control_client, "get", _fake_get)
    body = await control_client.get_manifest()
    assert body is not None
    assert body["commands"]["version"] == 1


@pytest.mark.asyncio
async def test_get_manifest_returns_none_on_error(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", "shared-secret")

    async def _fake_get(path, params=None):
        return 502, {"error": "unreachable"}

    monkeypatch.setattr(control_client, "get", _fake_get)
    assert await control_client.get_manifest() is None
