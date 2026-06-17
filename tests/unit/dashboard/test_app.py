"""Smoke test for the dashboard FastAPI app.

Skipped automatically when the dashboard's web dependencies are not installed
(CI installs only the bot's ``requirements.txt``), so this never reddens CI; run
it locally after ``pip install -r dashboard/requirements.txt httpx``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")  # Starlette's TestClient transport

from fastapi.testclient import TestClient  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[3]
_APP = _REPO_ROOT / "dashboard" / "app.py"

# Put the dashboard dir on sys.path so we can mint a valid signed session cookie
# (the same websession module the app uses → the signature verifies).
if str(_APP.parent) not in sys.path:
    sys.path.insert(0, str(_APP.parent))
import websession  # noqa: E402


def _login_cookie(user_id="42", guild_id="111", guild_name="My Server"):
    """A signed session cookie for a user who administers one guild."""
    session = {
        "user": {"id": user_id, "username": "owner", "global_name": "Owner"},
        "guilds": [{"id": guild_id, "name": guild_name, "owner": True}],
    }
    return {websession.COOKIE_NAME: websession.encode(session)}


@pytest.fixture(scope="module")
def client():
    spec = importlib.util.spec_from_file_location("dashboard_app_ut", _APP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return TestClient(module.app)


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/status",
        "/functions",
        "/games",
        "/commands",
        "/aliases",
        "/settings",
        "/access",
        "/ideas",
        "/bugs",
        "/updates",
        "/env",
    ],
)
def test_pages_render(client, path):
    resp = client.get(path)
    assert resp.status_code == 200
    assert "SuperBot" in resp.text


def test_games_page_shows_player_subsystems(client):
    resp = client.get("/games")
    assert resp.status_code == 200
    assert "Games &amp; economy" in resp.text or "Games & economy" in resp.text


def test_aliases_page_renders_suggestion_form(client):
    resp = client.get("/aliases")
    assert resp.status_code == 200
    # The form + the embedded collision data the JS needs.
    assert "Suggest a command alias" in resp.text
    assert 'id="taken-data"' in resp.text
    assert 'id="cmd-list"' in resp.text


def test_commands_page_has_manage_surface(client):
    resp = client.get("/commands")
    assert resp.status_code == 200
    # A Manage button (on every command and cog) + the slide-over panel.
    assert "manage-btn" in resp.text
    assert "Manage" in resp.text
    assert 'id="drawer"' in resp.text
    # The embedded data the drawer's JS needs: collision map, synonyms, routable.
    assert 'id="taken-data"' in resp.text
    assert 'id="syn-data"' in resp.text
    assert 'id="routable-data"' in resp.text
    # Cog-level routing framing (Q-0160) front-ending the audited seam.
    assert "command_routing.set_policy" in resp.text
    # Manage buttons carry per-command data attributes for the drawer.
    assert 'data-kind="command"' in resp.text
    # Acronym-aware cog->subsystem join: BTD6Cog now resolves to ``btd6``.
    assert 'data-subsystem="btd6"' in resp.text


def test_settings_page_lists_a_known_key(client):
    resp = client.get("/settings")
    assert resp.status_code == 200
    # A known setting constant + the read-only "key names only" framing.
    assert "WARN_THRESHOLD" in resp.text
    assert "key names" in resp.text


def test_access_page_shows_tier_ladder_and_visibility_caveat(client):
    resp = client.get("/access")
    assert resp.status_code == 200
    # The ladder + the visibility-is-not-execution caveat.
    assert "administrator" in resp.text
    assert "not</strong> permission to execute" in resp.text


def test_env_page_shows_usage_map_without_values(client):
    resp = client.get("/env")
    assert resp.status_code == 200
    # Surfaces a known required var name and the read-only disclaimer.
    assert "DATABASE_URL" in resp.text
    assert "never a value" in resp.text


def test_status_page_shows_build_and_health(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    # The headline sections of the status surface.
    assert "Deployed build" in resp.text
    assert "Bug health" in resp.text
    assert "Inventory" in resp.text


def test_healthz_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Control panel — dormant-by-default (no OAuth / control env in the test)
# ---------------------------------------------------------------------------


def test_admin_dormant_shows_setup_instructions(client):
    resp = client.get("/admin")
    assert resp.status_code == 200
    # With OAuth unconfigured, /admin explains how to switch the panel on.
    assert "Login isn't set up yet" in resp.text
    assert "DISCORD_OAUTH_CLIENT_ID" in resp.text
    assert "CONTROL_API_TOKEN" in resp.text


def test_nav_has_no_signin_button_when_dormant(client):
    # login_enabled is False → the nav offers "Control panel", never "Sign in".
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Sign in with Discord" not in resp.text
    assert "Control panel" in resp.text


def test_auth_login_redirects_to_admin_when_dormant(client):
    resp = client.get("/auth/login", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin"


def test_auth_logout_clears_and_redirects_home(client):
    resp = client.get("/auth/logout", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/"


def test_admin_guild_requires_login(client):
    # Not signed in → the per-guild editor bounces back to /admin.
    resp = client.get("/admin/123456789", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin"


def test_admin_guild_post_requires_login(client):
    # A write attempt without a session is rejected (redirect, no control call).
    resp = client.post(
        "/admin/123456789/settings",
        data={"subsystem": "moderation", "name": "warn_threshold", "value": "3"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303, 307)
    assert resp.headers["location"] == "/admin"


# ---------------------------------------------------------------------------
# Control panel — logged-in (signed session cookie) — verifies the editor page
# ---------------------------------------------------------------------------


def test_admin_home_shows_guilds_when_logged_in(client):
    resp = client.get("/admin", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "Servers you administer" in resp.text
    assert "My Server" in resp.text


def test_admin_guild_editor_renders_all_sections(client):
    # The big template: all three editors must render without a Jinja error.
    resp = client.get("/admin/111", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "My Server" in resp.text
    assert "⚙️ Settings" in resp.text
    assert "📖 Help appearance" in resp.text
    assert "Cogs (enable / disable)" in resp.text
    # Forms target the per-guild POST endpoints.
    assert 'action="/admin/111/settings"' in resp.text
    assert 'action="/admin/111/help/overlay"' in resp.text
    assert 'action="/admin/111/routing"' in resp.text
    # Dormant control API → the "not connected" banner is shown, not an error.
    assert "CONTROL_API_TOKEN" in resp.text


def test_admin_guild_see_then_change_renders_current_values(client, monkeypatch):
    # When the bot control API answers (configured + admin), the editor renders
    # live current values instead of the blind forms (Phase E "see-then-change").
    from unittest.mock import AsyncMock

    import control_client

    monkeypatch.setattr(control_client, "is_configured", lambda: True)
    monkeypatch.setattr(
        control_client,
        "get_authority",
        AsyncMock(
            return_value={
                "guild_found": True,
                "member_found": True,
                "is_admin": True,
                "tier": "administrator",
            },
        ),
    )

    async def fake_get(path, params=None):
        if path == "/control/settings/current":
            return 200, {
                "ok": True,
                "subsystems": {
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
                },
            }
        if path == "/control/help/overlay":
            return 200, {"ok": True, "rows": [], "home": None}
        if path == "/control/help/catalogue":
            return 200, {"ok": True, "hubs": [], "subsystems": []}
        if path == "/control/routing":
            return 200, {
                "ok": True,
                "rows": [
                    {
                        "scope_type": "guild",
                        "scope_id": None,
                        "cog_name": "MiningCog",
                        "enabled": False,
                    },
                ],
            }
        return 503, {"error": "unexpected path"}

    monkeypatch.setattr(control_client, "get", fake_get)

    resp = client.get("/admin/111", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "showing live current values" in resp.text
    assert "warn_threshold" in resp.text  # the live setting is rendered
    assert "warnings before action" in resp.text  # its hint is shown


def test_admin_guild_unknown_guild_redirects(client):
    # Logged in, but the guild isn't in the user's admin set → back to /admin.
    resp = client.get("/admin/999", cookies=_login_cookie(), follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin"


def test_admin_setting_post_when_logged_in_dormant_control(client):
    # Logged in + valid guild → the POST is accepted, calls the (dormant) control
    # API, and PRG-redirects back to the editor with a flash.
    resp = client.post(
        "/admin/111/settings",
        data={"subsystem": "moderation", "name": "warn_threshold", "value": "3"},
        cookies=_login_cookie(),
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/admin/111"
