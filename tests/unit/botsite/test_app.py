"""Smoke test for the public bot-site FastAPI app (P1).

Skipped automatically when the web dependencies are not installed (CI installs only
the bot's ``requirements.txt``), so it never reddens CI; run it locally after
``pip install -r botsite/requirements.txt``.

Covers the two surfaces this unit fully ships templates for — ``/`` and ``/healthz``
— plus the structural guarantees P1 owns: every route is wired, the submit stub
mounts cleanly, and the app never imports ``disbot``.
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
_APP = _REPO_ROOT / "botsite" / "app.py"


@pytest.fixture(scope="module")
def app_module():
    spec = importlib.util.spec_from_file_location("botsite_app_ut", _APP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def test_index_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "SuperBot" in resp.text
    # The marketing landing's load-bearing pieces.
    assert "Add to Discord" in resp.text
    assert "How it works" in resp.text


def test_index_shows_honest_catalogue_counts_not_server_totals(client, app_module):
    # The capability band renders catalogue counts (commands/features/games) — never
    # server/user totals (plan layout note: those need the deferred live source).
    resp = client.get("/")
    assert resp.status_code == 200
    counts = app_module.data_loader.load_site_data()["counts"]
    assert str(counts["commands"]) in resp.text
    assert "feature areas" in resp.text
    # No server/user vocabulary leaked onto the public landing.
    lowered = resp.text.lower()
    for forbidden in ("servers using", "active users", "members across"):
        assert forbidden not in lowered


def test_footer_shows_generated_freshness_badge(client):
    # The "generated" lineage badge (plan §3) — honest, never a live claim.
    resp = client.get("/")
    assert resp.status_code == 200
    assert "generated" in resp.text


# ---------------------------------------------------------------------------
# structural guarantees P1 owns (routing, the submit stub, decoupling)
# ---------------------------------------------------------------------------


def _route_paths(app) -> set[str]:
    """Registered route paths (some entries — e.g. an included empty router — have
    no ``.path``, so read it defensively)."""
    return {p for route in app.routes if (p := getattr(route, "path", None))}


def test_every_route_is_wired(app_module):
    # P1 wires every route up front; the back-half units only fill templates/behaviour.
    paths = _route_paths(app_module.app)
    for expected in ("/", "/commands", "/features", "/changelog", "/status", "/healthz"):
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
    assert not any(name == "disbot" or name.startswith("disbot.") for name in sys.modules)


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
