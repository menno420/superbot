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
        "/functions",
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


def test_aliases_page_renders_suggestion_form(client):
    resp = client.get("/aliases")
    assert resp.status_code == 200
    # The form + the embedded collision data the JS needs.
    assert "Suggest a command alias" in resp.text
    assert 'id="taken-data"' in resp.text
    assert 'id="cmd-list"' in resp.text


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


def test_healthz_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
