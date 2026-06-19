"""Smoke test for the read-only ``/reviews`` dashboard page (B7, Phase 1).

A new test file (the shared ``test_app.py`` page list is owned by another unit).
Skipped automatically when the dashboard's web dependencies are not installed
(CI installs only the bot's ``requirements.txt``), so this never reddens the main
code-quality job; the dashboard-ci workflow installs fastapi/httpx and runs it.
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

if str(_APP.parent) not in sys.path:
    sys.path.insert(0, str(_APP.parent))


@pytest.fixture(scope="module")
def app_module():
    spec = importlib.util.spec_from_file_location("dashboard_app_reviews_ut", _APP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app)


def test_reviews_page_renders(client):
    resp = client.get("/reviews")
    assert resp.status_code == 200
    assert "Review inbox" in resp.text


def test_reviews_page_renders_with_empty_data(client, app_module, monkeypatch):
    # A missing/empty payload must degrade to the empty state, never 500.
    monkeypatch.setattr(app_module, "load_data", lambda: dict(app_module._EMPTY))
    resp = client.get("/reviews")
    assert resp.status_code == 200
    assert "No open reviews." in resp.text


def test_reviews_page_groups_open_and_resolved(client, app_module, monkeypatch):
    payload = dict(app_module._EMPTY)
    payload["meta"] = {"generated_at": "", "counts": {"reviews": 2, "reviews_open": 1}}
    payload["reviews"] = [
        {"id": "REV-0002", "area": "economy", "status": "OPEN", "summary": "scale it"},
        {
            "id": "REV-0001",
            "area": "help",
            "status": "RESOLVED",
            "summary": "fixed wrap",
        },
    ]
    monkeypatch.setattr(app_module, "load_data", lambda: payload)
    resp = client.get("/reviews")
    assert resp.status_code == 200
    assert "REV-0002" in resp.text  # open
    assert "REV-0001" in resp.text  # resolved
    assert "Resolved" in resp.text
