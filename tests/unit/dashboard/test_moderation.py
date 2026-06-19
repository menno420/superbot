"""Tests for the dev-site submission moderation UI (plan §5 unit P5).

Covers the owner gate, the dormant-by-default states, the rendered (escaped) pending
queue, and the approve / reject POST flows — approve being the guarded
mirror → attach-url → set_status('approved') sequence, reject the set_status('rejected')
flip. The submissions DB and the GitHub mirror are monkeypatched (no live Postgres / no
GitHub token), the same way ``test_app.py`` stubs the control client.

Skipped automatically when the dashboard web deps are absent (CI installs only the bot's
requirements.txt), so it never reddens the main CI; the Dashboard CI workflow installs
fastapi/httpx and runs it for real.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")  # Starlette's TestClient transport

from fastapi.testclient import TestClient  # noqa: E402
from tests.support.web_app_loader import load_web_app  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[3]
_APP = _REPO_ROOT / "dashboard" / "app.py"

if str(_APP.parent) not in sys.path:
    sys.path.insert(0, str(_APP.parent))
import websession  # noqa: E402

_TEST_CSRF = "test-csrf-token"
_OWNER_ID = "42"


def _login_cookie(user_id=_OWNER_ID):
    """A signed session cookie carrying a known csrf token + the given user id."""
    session = {
        "user": {"id": user_id, "username": "owner", "global_name": "Owner"},
        "guilds": [{"id": "111", "name": "My Server", "owner": True}],
        "csrf": _TEST_CSRF,
    }
    return {websession.COOKIE_NAME: websession.encode(session)}


@pytest.fixture(scope="module")
def app_module():
    # load_web_app isolates the dashboard's bare sibling imports (`submissions_db` /
    # `ratelimit`) from the bot-site's same-named modules, so the dashboard app is
    # loaded correctly even when the bot-site tests ran first (the shared-sys.modules
    # collision that made these moderation tests order-dependent).
    return load_web_app(_APP, "dashboard_app_mod_ut")


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app)


@pytest.fixture
def as_owner(monkeypatch):
    """The signed-in user (id 42) IS the configured bot owner for this test."""
    monkeypatch.setenv("BOT_OWNER_USER_ID", _OWNER_ID)


# ---------------------------------------------------------------------------
# owner gate
# ---------------------------------------------------------------------------


def test_moderation_requires_login(client):
    resp = client.get("/admin/moderation", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin"


def test_moderation_non_owner_sees_owner_only(client, monkeypatch):
    # Logged in as 42, but the owner is someone else → "owner only", never the queue.
    monkeypatch.setenv("BOT_OWNER_USER_ID", "999")
    resp = client.get("/admin/moderation", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "Owner only" in resp.text
    # The dormant/queue affordances must NOT render for a non-owner.
    assert "pending submission" not in resp.text.lower()


def test_moderation_route_not_shadowed_by_guild_route(client, monkeypatch, as_owner):
    # Regression: `/admin/moderation` must be matched by the moderation route, NOT the
    # dynamic `/admin/{guild_id}` route (which would treat "moderation" as a guild id and
    # redirect to /admin). Owner + store dormant → the moderation page renders 200.
    monkeypatch.delenv("SUBMISSIONS_DB_DSN", raising=False)
    resp = client.get("/admin/moderation", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "Submission moderation" in resp.text


# ---------------------------------------------------------------------------
# dormant-by-default
# ---------------------------------------------------------------------------


def test_moderation_dormant_store_shows_setup(client, monkeypatch, as_owner):
    monkeypatch.delenv("SUBMISSIONS_DB_DSN", raising=False)
    resp = client.get("/admin/moderation", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "Submissions store not configured" in resp.text
    assert "SUBMISSIONS_DB_DSN" in resp.text


def test_moderation_lists_pending_escaped(client, monkeypatch, as_owner, app_module):
    # Store configured + a pending row whose body contains HTML → it is rendered ESCAPED.
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    monkeypatch.setattr(app_module.github_mirror, "is_configured", lambda: True)
    monkeypatch.setattr(
        app_module.submissions_db,
        "list_pending",
        AsyncMock(
            return_value=[
                {
                    "id": 7,
                    "kind": "bug",
                    "title": "Title <b>x</b>",
                    "body": "<script>alert(1)</script> broke it",
                    "surface": "Discord bot",
                    "contact": "me@example.com",
                    "submitted_at": "2026-06-19T00:00:00Z",
                    "github_issue_url": None,
                },
            ],
        ),
    )
    resp = client.get("/admin/moderation", cookies=_login_cookie())
    assert resp.status_code == 200
    # User input is escaped, never injected as live HTML.
    assert "<script>alert(1)</script>" not in resp.text
    assert "&lt;script&gt;" in resp.text
    assert "Discord bot" in resp.text
    # Approve + reject forms target the per-id endpoints.
    assert 'action="/admin/moderation/7/approve"' in resp.text
    assert 'action="/admin/moderation/7/reject"' in resp.text


def test_moderation_approve_hidden_when_mirror_dormant(
    client, monkeypatch, as_owner, app_module
):
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    monkeypatch.setattr(app_module.github_mirror, "is_configured", lambda: False)
    monkeypatch.setattr(
        app_module.submissions_db, "list_pending", AsyncMock(return_value=[])
    )
    resp = client.get("/admin/moderation", cookies=_login_cookie())
    assert resp.status_code == 200
    assert "Approve is disabled" in resp.text
    assert "GITHUB_ISSUE_MIRROR_TOKEN" in resp.text


# ---------------------------------------------------------------------------
# reject flow
# ---------------------------------------------------------------------------


def test_reject_flips_status(client, monkeypatch, as_owner, app_module):
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    set_status = AsyncMock(return_value=True)
    monkeypatch.setattr(app_module.submissions_db, "set_status", set_status)
    app_module._MODERATION_LIMITER.reset()

    resp = client.post(
        "/admin/moderation/7/reject",
        data={"csrf_token": _TEST_CSRF},
        cookies=_login_cookie(),
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/admin/moderation"
    set_status.assert_awaited_once_with(7, "rejected", moderated_by="42")
    app_module._MODERATION_LIMITER.reset()


def test_reject_requires_owner(client, monkeypatch, app_module):
    monkeypatch.setenv("BOT_OWNER_USER_ID", "999")  # signed-in 42 is not the owner
    set_status = AsyncMock(return_value=True)
    monkeypatch.setattr(app_module.submissions_db, "set_status", set_status)
    resp = client.post(
        "/admin/moderation/7/reject",
        data={"csrf_token": _TEST_CSRF},
        cookies=_login_cookie(),
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303, 307)
    assert resp.headers["location"] == "/admin"
    set_status.assert_not_awaited()  # the gate blocks before any DB write


def test_reject_rejects_bad_csrf(client, monkeypatch, as_owner, app_module):
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    set_status = AsyncMock(return_value=True)
    monkeypatch.setattr(app_module.submissions_db, "set_status", set_status)
    app_module._MODERATION_LIMITER.reset()
    resp = client.post(
        "/admin/moderation/7/reject",
        data={"csrf_token": "wrong"},
        cookies=_login_cookie(),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "stale" in resp.text.lower() or "expired" in resp.text.lower()
    set_status.assert_not_awaited()
    app_module._MODERATION_LIMITER.reset()


# ---------------------------------------------------------------------------
# approve flow — the guarded mirror → attach-url → set_status sequence
# ---------------------------------------------------------------------------


def test_approve_mirrors_then_attaches_then_approves(
    client, monkeypatch, as_owner, app_module
):
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    monkeypatch.setattr(app_module.github_mirror, "is_configured", lambda: True)
    row = {
        "id": 7,
        "kind": "bug",
        "title": "boom",
        "body": "it broke",
        "surface": "Discord bot",
        "contact": None,
        "submitted_at": "2026-06-19T00:00:00Z",
        "github_issue_url": None,
    }
    monkeypatch.setattr(
        app_module.submissions_db, "list_pending", AsyncMock(return_value=[row])
    )
    issue_url = "https://github.com/menno420/superbot/issues/7"
    create_issue = AsyncMock(return_value=issue_url)
    attach = AsyncMock(return_value=True)
    set_status = AsyncMock(return_value=True)
    monkeypatch.setattr(app_module.github_mirror, "create_issue", create_issue)
    monkeypatch.setattr(app_module.submissions_db, "attach_issue_url", attach)
    monkeypatch.setattr(app_module.submissions_db, "set_status", set_status)
    app_module._MODERATION_LIMITER.reset()

    resp = client.post(
        "/admin/moderation/7/approve",
        data={"csrf_token": _TEST_CSRF},
        cookies=_login_cookie(),
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/admin/moderation"
    # The exact guarded sequence: create the issue from the row, store its URL, approve.
    create_issue.assert_awaited_once_with(row)
    attach.assert_awaited_once_with(7, issue_url)
    set_status.assert_awaited_once_with(7, "approved", moderated_by="42")
    app_module._MODERATION_LIMITER.reset()


def test_approve_leaves_pending_when_mirror_fails(
    client, monkeypatch, as_owner, app_module
):
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    monkeypatch.setattr(app_module.github_mirror, "is_configured", lambda: True)
    row = {"id": 7, "kind": "bug", "title": "t", "body": "b", "github_issue_url": None}
    monkeypatch.setattr(
        app_module.submissions_db, "list_pending", AsyncMock(return_value=[row])
    )
    create_issue = AsyncMock(side_effect=RuntimeError("github down"))
    attach = AsyncMock(return_value=True)
    set_status = AsyncMock(return_value=True)
    monkeypatch.setattr(app_module.github_mirror, "create_issue", create_issue)
    monkeypatch.setattr(app_module.submissions_db, "attach_issue_url", attach)
    monkeypatch.setattr(app_module.submissions_db, "set_status", set_status)
    app_module._MODERATION_LIMITER.reset()

    resp = client.post(
        "/admin/moderation/7/approve",
        data={"csrf_token": _TEST_CSRF},
        cookies=_login_cookie(),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "failed" in resp.text.lower() and "pending" in resp.text.lower()
    # The row must NOT be marked approved when the mirror failed (so the owner retries).
    attach.assert_not_awaited()
    set_status.assert_not_awaited()
    app_module._MODERATION_LIMITER.reset()


def test_approve_idempotent_when_already_moderated(
    client, monkeypatch, as_owner, app_module
):
    # The row is no longer in the pending list (double-click / already moderated) → the
    # approve is a no-op: no issue created, no status write.
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    monkeypatch.setattr(app_module.github_mirror, "is_configured", lambda: True)
    monkeypatch.setattr(
        app_module.submissions_db, "list_pending", AsyncMock(return_value=[])
    )
    create_issue = AsyncMock()
    set_status = AsyncMock()
    monkeypatch.setattr(app_module.github_mirror, "create_issue", create_issue)
    monkeypatch.setattr(app_module.submissions_db, "set_status", set_status)
    app_module._MODERATION_LIMITER.reset()

    resp = client.post(
        "/admin/moderation/7/approve",
        data={"csrf_token": _TEST_CSRF},
        cookies=_login_cookie(),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "no longer pending" in resp.text.lower()
    create_issue.assert_not_awaited()
    set_status.assert_not_awaited()
    app_module._MODERATION_LIMITER.reset()


def test_approve_disabled_when_mirror_dormant(client, monkeypatch, as_owner, app_module):
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    monkeypatch.setattr(app_module.github_mirror, "is_configured", lambda: False)
    create_issue = AsyncMock()
    monkeypatch.setattr(app_module.github_mirror, "create_issue", create_issue)
    app_module._MODERATION_LIMITER.reset()
    resp = client.post(
        "/admin/moderation/7/approve",
        data={"csrf_token": _TEST_CSRF},
        cookies=_login_cookie(),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "approve is disabled" in resp.text.lower()
    create_issue.assert_not_awaited()
    app_module._MODERATION_LIMITER.reset()


def test_moderation_action_is_rate_limited(client, monkeypatch, as_owner, app_module):
    monkeypatch.setattr(app_module.submissions_db, "is_configured", lambda: True)
    monkeypatch.setattr(
        app_module.submissions_db, "set_status", AsyncMock(return_value=True)
    )
    app_module._MODERATION_LIMITER.reset()
    monkeypatch.setattr(app_module._MODERATION_LIMITER, "max_events", 1)
    data = {"csrf_token": _TEST_CSRF}
    first = client.post(
        "/admin/moderation/7/reject",
        data=data,
        cookies=_login_cookie(),
        follow_redirects=False,
    )
    assert first.status_code == 303
    second = client.post(
        "/admin/moderation/8/reject",
        data=data,
        cookies=_login_cookie(),
        follow_redirects=True,
    )
    assert second.status_code == 200
    assert "too many" in second.text.lower() or "slow down" in second.text.lower()
    app_module._MODERATION_LIMITER.reset()
