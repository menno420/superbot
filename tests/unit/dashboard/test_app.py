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

_TEST_CSRF = "test-csrf-token"


def _login_cookie(user_id="42", guild_id="111", guild_name="My Server"):
    """A signed session cookie for a user who administers one guild.

    Carries a known ``csrf`` token so POST tests can submit a matching
    ``csrf_token`` field (the R3 CSRF check); GET tests are unaffected.
    """
    session = {
        "user": {"id": user_id, "username": "owner", "global_name": "Owner"},
        "guilds": [{"id": guild_id, "name": guild_name, "owner": True}],
        "csrf": _TEST_CSRF,
    }
    return {websession.COOKIE_NAME: websession.encode(session)}


@pytest.fixture(scope="module")
def app_module():
    spec = importlib.util.spec_from_file_location("dashboard_app_ut", _APP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def client(app_module):
    return TestClient(app_module.app)


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


# ---------------------------------------------------------------------------
# Phase C — the read workspace (/me, /admin/{guild}/overview, authority preview)
# ---------------------------------------------------------------------------


def test_me_requires_login(client):
    # Not signed in → the personal overview bounces back to /admin (sign-in).
    resp = client.get("/me", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin"


def test_me_overview_lists_servers_when_logged_in(client):
    resp = client.get("/me", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "Servers you administer" in resp.text
    assert "My Server" in resp.text
    # Each server card links to both the overview and the editor.
    assert "/admin/111/overview" in resp.text
    assert 'href="/admin/111"' in resp.text


def test_overview_requires_login(client):
    resp = client.get("/admin/111/overview", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin"


def test_overview_unknown_guild_redirects(client):
    resp = client.get(
        "/admin/999/overview",
        cookies=_login_cookie(),
        follow_redirects=False,
    )
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin"


def test_overview_renders_authority_preview_when_dormant(client):
    # Logged in, control API dormant → the page renders with the authority preview
    # and the "not connected" notice, never an error.
    resp = client.get("/admin/111/overview", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "Your authority here" in resp.text
    assert "Setup health" in resp.text
    assert "CONTROL_API_TOKEN" in resp.text


def test_overview_shows_health_metrics_with_live_reads(client, monkeypatch):
    # Configured + admin → the overview renders the live setup-health summary.
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
                "is_owner": False,
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
                        {"name": "warn_threshold", "value": 5, "provenance": "guild", "valid": True},
                        {"name": "mute_role", "value": None, "provenance": "default", "valid": False},
                    ],
                },
            }
        if path == "/control/help/overlay":
            return 200, {"ok": True, "rows": [{"entity_kind": "subsystem", "entity_key": "xp"}], "home": None}
        if path == "/control/help/catalogue":
            return 200, {"ok": True, "hubs": [], "subsystems": []}
        if path == "/control/routing":
            return 200, {
                "ok": True,
                "rows": [
                    {"scope_type": "guild", "scope_id": None, "cog_name": "MiningCog", "enabled": False},
                ],
            }
        return 503, {"error": "unexpected path"}

    monkeypatch.setattr(control_client, "get", fake_get)

    resp = client.get("/admin/111/overview", cookies=_login_cookie())
    assert resp.status_code == 200
    # One customised, one invalid, one help override, one disabled cog.
    assert "customised from default" in resp.text
    assert "invalid → using default" in resp.text
    assert "mute_role" in resp.text  # the invalid setting is named
    assert "MiningCog" in resp.text  # the disabled cog is named


def test_overview_shows_unreachable_when_bot_down(client, monkeypatch):
    # Configured, but the bot control API is unreachable (get_authority → None) →
    # the overview shows an honest "unavailable" banner, never an error.
    from unittest.mock import AsyncMock

    import control_client

    monkeypatch.setattr(control_client, "is_configured", lambda: True)
    monkeypatch.setattr(control_client, "get_authority", AsyncMock(return_value=None))

    resp = client.get("/admin/111/overview", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "couldn't reach the bot's control API" in resp.text


def test_setup_health_projection(app_module):
    current = {
        "settings": {
            "moderation": [
                {"name": "a", "provenance": "guild", "valid": True},
                {"name": "b", "provenance": "default", "valid": True},
                {"name": "c", "provenance": "default", "valid": False},
            ],
        },
        "help_overlay": {"rows": [{"x": 1}, {"x": 2}], "home": {"title": "t"}},
        "routing_map": {"AlphaCog": True, "BetaCog": False},
    }
    health = app_module._setup_health(current)
    assert health["total_settings"] == 3
    assert health["customised"] == 1
    assert health["invalid_count"] == 1
    assert health["invalid"] == [{"subsystem": "moderation", "name": "c"}]
    assert health["help_overrides"] == 2
    assert health["home_customised"] is True
    assert health["disabled_cogs"] == ["BetaCog"]
    assert health["healthy"] is False


def test_setup_health_empty_is_healthy(app_module):
    health = app_module._setup_health(app_module._blank_current())
    assert health["total_settings"] == 0
    assert health["invalid_count"] == 0
    assert health["disabled_cogs"] == []
    assert health["healthy"] is True


def test_authority_preview_admin_vs_member(app_module):
    admin = app_module._authority_preview(
        {"member_found": True, "is_admin": True, "is_owner": False, "tier": "administrator"},
    )
    assert admin["may_read_config"] and admin["may_edit_settings"]
    assert admin["may_edit_help"] and admin["may_edit_routing"]

    member = app_module._authority_preview(
        {"member_found": True, "is_admin": False, "is_owner": False, "tier": "member"},
    )
    assert not member["may_read_config"]
    assert not member["may_edit_settings"]

    none = app_module._authority_preview(None)
    assert none["member_found"] is False
    assert none["tier"] is None


def test_admin_setting_post_when_logged_in_dormant_control(client):
    # Logged in + valid guild + valid CSRF → the POST is accepted, calls the
    # (dormant) control API, and PRG-redirects back to the editor with a flash.
    resp = client.post(
        "/admin/111/settings",
        data={
            "subsystem": "moderation",
            "name": "warn_threshold",
            "value": "3",
            "csrf_token": _TEST_CSRF,
        },
        cookies=_login_cookie(),
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/admin/111"


# ---------------------------------------------------------------------------
# R3 hardening — CSRF + rate limiting
# ---------------------------------------------------------------------------


def test_admin_setting_post_rejects_missing_csrf(client):
    # Logged in but no/blank csrf_token → the edit is refused before any control
    # call; the editor reloads with a "stale form" flash (PRG back to the guild).
    resp = client.post(
        "/admin/111/settings",
        data={"subsystem": "moderation", "name": "warn_threshold", "value": "3"},
        cookies=_login_cookie(),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "stale" in resp.text.lower() or "expired" in resp.text.lower()


def test_admin_setting_post_rejects_wrong_csrf(client):
    resp = client.post(
        "/admin/111/settings",
        data={
            "subsystem": "moderation",
            "name": "warn_threshold",
            "value": "3",
            "csrf_token": "not-the-session-token",
        },
        cookies=_login_cookie(),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "stale" in resp.text.lower() or "expired" in resp.text.lower()


def test_admin_edit_is_rate_limited(client, monkeypatch):
    # Exceeding the per-user edit budget yields a "slow down" flash, not a control call.
    appmod = sys.modules["dashboard_app_ut"]
    appmod._EDIT_LIMITER.reset()
    monkeypatch.setattr(appmod._EDIT_LIMITER, "max_events", 1)
    data = {
        "subsystem": "moderation",
        "name": "warn_threshold",
        "value": "3",
        "csrf_token": _TEST_CSRF,
    }
    first = client.post(
        "/admin/111/settings", data=data, cookies=_login_cookie(), follow_redirects=False
    )
    assert first.status_code == 303  # within budget
    second = client.post(
        "/admin/111/settings", data=data, cookies=_login_cookie(), follow_redirects=True
    )
    assert second.status_code == 200
    assert "too many" in second.text.lower() or "slow down" in second.text.lower()
    appmod._EDIT_LIMITER.reset()
