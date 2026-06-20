"""Smoke test for the public bot-site FastAPI app (P1).

Skipped automatically when the web dependencies are not installed (CI installs only
the bot's ``requirements.txt``), so it never reddens CI; run it locally after
``pip install -r botsite/requirements.txt``.

Covers the two surfaces this unit fully ships templates for — ``/`` and ``/healthz``
— plus the structural guarantees P1 owns: every route is wired, the submit stub
mounts cleanly, and the app never imports ``disbot``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")  # Starlette's TestClient transport

from fastapi.testclient import TestClient  # noqa: E402
from tests.support.web_app_loader import load_web_app  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[3]
_APP = _REPO_ROOT / "botsite" / "app.py"


@pytest.fixture(scope="module")
def app_module():
    return load_web_app(_APP, "botsite_app_ut")


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app)


# ---------------------------------------------------------------------------
# the surfaces this unit ships (/ + /healthz)
# ---------------------------------------------------------------------------


def test_healthz_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_index_serves_spa_shell(client):
    # `/` now serves the Claude-Design SPA shell (the public front-end). It is a
    # hash-routed app: the empty <main id="app"> is filled client-side from
    # window.SBDATA, loaded via /data.js then driven by /app.js.
    resp = client.get("/")
    assert resp.status_code == 200
    assert "SuperBot" in resp.text
    assert 'id="app"' in resp.text
    assert "data.js" in resp.text and "app.js" in resp.text


def test_spa_static_assets_served(client):
    # The verbatim design assets are served with sensible content types so the shell
    # actually boots (no static/ dir — they live in botsite/site/).
    js = client.get("/app.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]
    css = client.get("/app.css")
    assert css.status_code == 200 and "css" in css.headers["content-type"]


def test_data_js_is_generated_live_and_truthful(client, app_module):
    # /data.js is the dynamic data seam — generated from the live site.json on each
    # request (owner goal: "all data should dynamically load"). It must honor the SPA
    # data contract and carry the *real* bot data, not the sample.
    resp = client.get("/data.js")
    assert resp.status_code == 200 and "javascript" in resp.headers["content-type"]
    body = resp.text
    # Contract surface the SPA reads.
    assert "window.SBDATA = { ICONS, AREAS, COMMANDS, GAMES, CHANGELOG, STATUS" in body
    for token in (
        "const ICONS",
        "const AREAS",
        "const COMMANDS",
        "const GAMES",
        "const CHANGELOG",
        "const STATUS",
    ):
        assert token in body, f"missing {token}"
    # Real data: a known command name from site.json appears (not the sample bot).
    names = {c["name"] for c in app_module.data_loader.load_site_data()["commands"]}
    assert "blackjack" in names and "blackjack" in body
    # Honest posture: no server/user totals leak into the public data layer.
    lowered = body.lower()
    for forbidden in ("servers using", "active users", "members across"):
        assert forbidden not in lowered


def test_submit_page_shares_chrome_with_working_install_cta(client, app_module):
    # /submit is rendered by submit.py's SEPARATE Jinja env; it must share
    # chrome.site_context so base.html's nav "Add to Discord" button isn't a dead
    # href="" there. (Regression caught on PR #1152: the separate env had no context
    # processor, so the public feedback page shipped a dead install button.)
    resp = client.get("/submit")
    assert resp.status_code == 200
    assert app_module.chrome.ADD_TO_DISCORD_URL in resp.text


# The Jinja fallback pages (/commands, /features, /changelog, /status) keep their
# own honest-counts and "generated" freshness guards in test_commands_page.py /
# test_changelog_status.py; the SPA's honest-data guard lives in
# test_data_js_is_generated_live_and_truthful above.


# ---------------------------------------------------------------------------
# structural guarantees P1 owns (routing, the submit stub, decoupling)
# ---------------------------------------------------------------------------


def _route_paths(app) -> set[str]:
    """Registered route paths (some entries — e.g. an included empty router — have
    no ``.path``, so read it defensively).
    """
    return {p for route in app.routes if (p := getattr(route, "path", None))}


def test_every_route_is_wired(app_module):
    # P1 wires every route up front; the back-half units only fill templates/behaviour.
    paths = _route_paths(app_module.app)
    for expected in (
        "/",
        "/app.js",
        "/app.css",
        "/data.js",  # the SPA shell + dynamic data
        "/commands",
        "/features",
        "/changelog",
        "/status",
        "/healthz",
    ):
        assert expected in paths, f"route {expected} not wired"


def test_submit_router_is_mounted(app_module):
    # app.py mounts the submit router as the single routing owner; unit P4 filled it
    # (the GET/POST /submit form + intake) without touching app.py — the whole point
    # of the included-router seam. (Pre-P4 this asserted the stub was empty.) The
    # /submit behaviour itself is covered by tests/unit/botsite/test_submit.py.
    import submit

    methods = {tuple(sorted(r.methods)) for r in submit.router.routes}
    assert ("GET",) in methods and ("POST",) in methods


def test_app_does_not_import_disbot(app_module):
    # The hard decoupling rule: the web tier must never import disbot.
    src = _APP.read_text(encoding="utf-8")
    assert "import disbot" not in src
    assert "from disbot" not in src
    # And it must not have been pulled in transitively at import time.
    assert not any(
        name == "disbot" or name.startswith("disbot.") for name in sys.modules
    )


def test_no_static_dir(app_module):
    # The #970 gotcha: there must be NO static/ dir (it would never deploy — gitignored).
    assert not (_APP.parent / "static").exists()


# ---------------------------------------------------------------------------
# data_loader — load/validate site.json (robust to a missing/corrupt artifact)
# ---------------------------------------------------------------------------


def test_data_loader_falls_back_to_empty_shape(app_module, tmp_path):
    dl = app_module.data_loader
    missing = tmp_path / "nope.json"
    data = dl.load_site_data(missing)
    # Always carries the whitelisted top-level keys → templates never KeyError.
    assert set(data) == {"meta", "counts", "catalogue", "commands", "bot_changelog"}
    assert data["counts"] == {"commands": 0, "features": 0, "games": 0}


def test_data_loader_handles_corrupt_json(app_module, tmp_path):
    dl = app_module.data_loader
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    data = dl.load_site_data(bad)
    assert data["catalogue"] == []


def test_data_loader_reads_committed_site_json(app_module):
    # The real committed artifact loads and carries the expected families.
    dl = app_module.data_loader
    data = dl.load_site_data()
    assert set(data) >= {"meta", "counts", "catalogue", "commands", "bot_changelog"}
    assert data["counts"]["commands"] == len(data["commands"])
