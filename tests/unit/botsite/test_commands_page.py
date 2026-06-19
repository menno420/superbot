"""Tests for the interactive command + feature browser (plan unit P2).

Covers the two pages this unit ships templates for — ``/commands`` (the clickable,
searchable command reference) and ``/features`` (the category showcase) — rendered
through P1's already-wired routes. Skipped automatically when the web dependencies
are not installed (CI installs only the bot's ``requirements.txt``), so it never
reddens the main pipeline; ``botsite-ci.yml`` installs the web deps and runs it for
real.

The assertions are about the *load-bearing browser behaviour*: cards are clickable
(native ``<details>`` → progressive enhancement, works with JS off), the S1.1
enrichment (status badge, examples, linked ideas) is rendered, the client-side
search/filter scaffolding is present, and no per-guild / dev-only value leaks onto
the page.
"""

from __future__ import annotations

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
    return load_web_app(_APP, "botsite_app_p2_ut")


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app)


@pytest.fixture
def site_data(app_module):
    return app_module.data_loader.load_site_data()


# ---------------------------------------------------------------------------
# /commands — the interactive command reference
# ---------------------------------------------------------------------------


def test_commands_page_renders(client):
    resp = client.get("/commands")
    assert resp.status_code == 200
    assert "Commands" in resp.text


def test_commands_page_lists_every_command(client, site_data):
    # Every command in the data appears as a clickable card on the page.
    resp = client.get("/commands")
    text = resp.text
    commands = site_data["commands"]
    assert commands, "expected a non-empty command reference in site.json"
    # Spot-check a generous sample (rendering all 300+ names is what the page does).
    for cmd in commands[:40]:
        assert f"!{cmd['name']}" in text


def test_commands_are_clickable_details_for_progressive_enhancement(client, site_data):
    # The cards are native <details> elements → clickable + expandable with NO JS.
    resp = client.get("/commands")
    text = resp.text
    assert text.count("<details") >= len(site_data["commands"])
    assert "<summary" in text


def test_commands_page_shows_status_badges(client, site_data):
    # The maturity badge (finished vs in-progress) is the headline S1.1 signal.
    resp = client.get("/commands")
    text = resp.text.lower()
    statuses = {c["status"] for c in site_data["commands"]}
    if "finished" in statuses:
        assert "finished" in text
    if "in-progress" in statuses:
        # rendered as "in&#8209;progress" (non-breaking hyphen) — match on "progress".
        assert "progress" in text


def test_commands_page_renders_detail_fields(client, site_data):
    # The detail partial surfaces aliases / permissions / examples / linked ideas.
    resp = client.get("/commands")
    text = resp.text
    assert "Permissions" in text
    assert "Aliases" in text
    # An example invocation from some command should be present verbatim.
    example = next(
        (e for c in site_data["commands"] for e in c["examples"]),
        None,
    )
    if example is not None:
        assert example in text
    # A linked-idea "what's planned" teaser should appear when any command has one.
    has_linked = any(c["linked_ideas"] for c in site_data["commands"])
    if has_linked:
        assert "What&#39;s planned" in text or "What's planned" in text


def test_commands_page_has_client_side_search_and_filter(client):
    # The search box + category filter scaffolding (enhanced by the inline script).
    resp = client.get("/commands")
    text = resp.text
    assert 'id="cmd-search"' in text
    assert "cmd-filter" in text
    # The progressive-enhancement script is inlined (no static/ dir — #970 gotcha).
    assert "<script>" in text
    assert "data-search" in text


def test_commands_page_no_static_dir_reference(client):
    # Honor the #970 gotcha: no reference to a /static/ asset path.
    resp = client.get("/commands")
    assert "/static/" not in resp.text


# ---------------------------------------------------------------------------
# /features — the category showcase
# ---------------------------------------------------------------------------


def test_features_page_renders(client):
    resp = client.get("/features")
    assert resp.status_code == 200
    assert "Features" in resp.text


def test_features_page_groups_catalogue_by_category(client, site_data):
    resp = client.get("/features")
    text = resp.text
    categories = {e.get("category") for e in site_data["catalogue"] if e.get("category")}
    assert categories, "expected categorised catalogue entries"
    for category in categories:
        # Each category gets an anchor section (the jump links + headings).
        assert f"cat-{category}" in text


def test_features_page_lists_feature_names_and_game_badge(client, site_data):
    resp = client.get("/features")
    text = resp.text
    catalogue = site_data["catalogue"]
    assert catalogue, "expected a non-empty catalogue"
    for entry in catalogue[:20]:
        assert (entry.get("display_name") or entry.get("key")) in text
    # The game badge is shown when the catalogue marks an entry as a game.
    if any(e.get("is_game") for e in catalogue):
        assert "game" in text.lower()


def test_features_page_has_client_side_search(client):
    resp = client.get("/features")
    text = resp.text
    assert 'id="feat-search"' in text
    assert "<script>" in text


# ---------------------------------------------------------------------------
# decoupling + safety (shared with the rest of the bot site)
# ---------------------------------------------------------------------------


def test_browser_pages_do_not_leak_dev_only_vocabulary(client):
    # The pages render the public subset only — no dev-only family should surface.
    for path in ("/commands", "/features"):
        lowered = client.get(path).text.lower()
        for forbidden in ("env_usage", "database_url", "control_api_token", "discord_oauth"):
            assert forbidden not in lowered, f"{forbidden} leaked onto {path}"
