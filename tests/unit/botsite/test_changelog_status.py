"""Tests for the bot-site changelog + status templates (P3).

Skipped automatically when the web dependencies are not installed (CI installs only
the bot's ``requirements.txt``), so it never reddens CI; run it locally after
``pip install -r botsite/requirements.txt``.

Covers the two user-facing pages this unit ships — ``/changelog`` (a curated,
date-grouped "what's new" timeline) and ``/status`` (an honest, generated-only trust
band). The load-bearing guarantees: the curated data is rendered, the "generated"
freshness posture is honest (no live claim), no raw internal PR number leaks onto the
public changelog, the status band never fabricates server/user totals, and both pages
have friendly empty states.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")  # Starlette's TestClient transport

from fastapi.testclient import TestClient  # noqa: E402
from markupsafe import escape as _md_escape  # noqa: E402  - Jinja2's autoescaper

_REPO_ROOT = Path(__file__).resolve().parents[3]
_APP = _REPO_ROOT / "botsite" / "app.py"


@pytest.fixture(scope="module")
def app_module():
    spec = importlib.util.spec_from_file_location("botsite_app_changelog_ut", _APP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app)


# ---------------------------------------------------------------------------
# /changelog — curated, date-grouped "what's new" timeline
# ---------------------------------------------------------------------------


def test_changelog_renders_curated_entries(client, app_module):
    resp = client.get("/changelog")
    assert resp.status_code == 200
    entries = app_module.data_loader.load_site_data()["bot_changelog"]
    assert entries, "fixture precondition: the committed site.json has changelog entries"
    # The user-facing pieces of each entry are rendered: title, date, summary.
    # Compare against MarkupSafe's escaped form — Jinja2 autoescapes (e.g. an
    # apostrophe becomes &#39;), which is the correct safe behaviour, so the raw
    # string need not appear verbatim. (Use the same escaper Jinja2 uses, not
    # html.escape, which emits &#x27; instead of &#39;.)
    for entry in entries:
        assert str(_md_escape(entry["title"])) in resp.text
        assert entry["date"] in resp.text
        if entry["summary"]:
            assert str(_md_escape(entry["summary"])) in resp.text


def test_changelog_shows_kind_tags(client, app_module):
    # Each entry is tagged feature/fix/improvement; the template maps those kinds to
    # friendly labels. Assert the label for whatever kinds the data actually carries.
    resp = client.get("/changelog")
    assert resp.status_code == 200
    kinds = {e["kind"] for e in app_module.data_loader.load_site_data()["bot_changelog"]}
    label_for = {"feature": "New", "improvement": "Improved", "fix": "Fixed"}
    for kind in kinds:
        if kind in label_for:
            assert label_for[kind] in resp.text


def test_changelog_carries_generated_freshness_badge(client):
    # The page declares its generated lineage honestly (plan §3) — not a live feed.
    resp = client.get("/changelog")
    assert resp.status_code == 200
    assert "generated" in resp.text
    # Honest framing: curated / newest-first, never a real-time claim.
    assert "newest first" in resp.text.lower()


def test_changelog_does_not_leak_raw_pr_numbers(client):
    # Brief / layout guidance: never surface raw internal PR numbers as user-facing
    # identifiers. The curated source has no PR ids; assert none leaked into the page
    # body (e.g. "PR #1109" / "#1109"). We scan the rendered changelog content.
    import re

    resp = client.get("/changelog")
    assert resp.status_code == 200
    # No "PR #<n>" style identifiers anywhere on the user-facing page.
    assert not re.search(r"PR\s*#\d+", resp.text)
    # And no bare "#<4+ digit>" tokens (the internal PR-number shape) in the changelog body.
    assert not re.search(r"#\d{3,}", resp.text)


def _patch_empty_data(app_module, tmp_path, monkeypatch):
    """Make the page routes load the safe empty shape (no committed artifact).

    ``load_site_data`` binds ``DATA_FILE`` as a *default argument* at definition
    time, so patching the module attribute alone has no effect. Instead wrap the
    loader to call the real implementation against a missing path — that exercises
    the genuine missing-artifact fallback rather than faking a return value.
    """
    dl = app_module.data_loader
    real = dl.load_site_data
    missing = tmp_path / "absent.json"
    monkeypatch.setattr(dl, "load_site_data", lambda *a, **k: real(missing))


def test_changelog_groups_same_date_entries_under_one_heading(app_module):
    # The committed artifact happens to have one entry per date, so render the
    # template directly with a synthetic multi-entry-per-date payload to lock in the
    # timeline grouping: same-date entries collapse under a single date heading, and
    # newest-first order is preserved.
    import re

    template = app_module.templates.get_template("changelog.html")
    entries = [
        {"date": "2026-06-19", "title": "Alpha", "kind": "feature", "summary": "a"},
        {"date": "2026-06-19", "title": "Beta", "kind": "fix", "summary": "b"},
        {"date": "2026-06-01", "title": "Gamma", "kind": "improvement", "summary": "c"},
        {"date": "2026-05-01", "title": "Delta", "kind": "", "summary": "d"},
    ]
    rendered = template.render(
        {"entries": entries, "page": "changelog", "build": {}, "site_counts": {}},
    )
    buckets = re.findall(r'<time datetime="([0-9-]+)">', rendered)
    # 4 entries / 3 distinct dates → 3 timeline buckets, newest-first.
    assert buckets == ["2026-06-19", "2026-06-01", "2026-05-01"]
    assert buckets.count("2026-06-19") == 1  # the two same-date entries share a heading
    assert "Alpha" in rendered and "Beta" in rendered
    # An empty kind renders the neutral "Update" label (never blank/broken).
    assert ">Update<" in rendered


def test_changelog_empty_state_is_friendly(client, app_module, tmp_path, monkeypatch):
    # With no curated entries, the page shows a friendly message — never an error or
    # a blank page (cross-cutting guidance).
    _patch_empty_data(app_module, tmp_path, monkeypatch)
    resp = client.get("/changelog")
    assert resp.status_code == 200
    assert "No changelog entries yet" in resp.text


# ---------------------------------------------------------------------------
# /status — honest, generated-only user trust band
# ---------------------------------------------------------------------------


def test_status_renders_build_trust_band(client, app_module):
    resp = client.get("/status")
    assert resp.status_code == 200
    build = app_module.data_loader.build_meta(app_module.data_loader.load_site_data())
    assert build.get("commit"), "fixture precondition: committed site.json has a build sha"
    # The deployed build sha is surfaced (it is public — matches the OSS repo).
    assert build["commit"] in resp.text
    # The build date, when present, is shown.
    if build.get("committed_at"):
        assert build["committed_at"] in resp.text


def test_status_is_honest_generated_not_live(client):
    # The trust band must label itself "as of last deploy" with a "generated" badge,
    # and must make NO live/real-time claim (plan §3 hard rule — the public site never
    # reads the bot's private control API).
    resp = client.get("/status")
    assert resp.status_code == 200
    assert "generated" in resp.text
    assert "as of the last deploy" in resp.text.lower()
    lowered = resp.text.lower()
    for forbidden in ("real-time", "live status", "currently online", "uptime:"):
        assert forbidden not in lowered


def test_status_does_not_fabricate_server_or_user_totals(client):
    # v1 must never render server/user numbers (those need the deferred live source).
    resp = client.get("/status")
    assert resp.status_code == 200
    lowered = resp.text.lower()
    for forbidden in ("servers using", "active users", "members across", "users online"):
        assert forbidden not in lowered


def test_status_empty_state_is_friendly(client, app_module, tmp_path, monkeypatch):
    # With no build meta, the band degrades to a friendly "unavailable" message and a
    # slate (not green) dot — never an error.
    _patch_empty_data(app_module, tmp_path, monkeypatch)
    resp = client.get("/status")
    assert resp.status_code == 200
    assert "Status unavailable" in resp.text
    assert "isn't available right now" in resp.text
