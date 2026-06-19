"""Tests for ``dashboard/github_mirror.py`` — the approve-side GitHub-issue mirror.

No live token / no network: the pure body/label/title builders are tested directly, the
dormant guard is tested via the env, and the ``create_issue`` POST path runs against a
tiny fake ``httpx`` injected through ``sys.modules`` (the same stub pattern the
``test_submissions_db.py`` suite uses for ``asyncpg``). Loaded by file path (the module
is a plain file under ``dashboard/``).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE = _REPO_ROOT / "dashboard" / "github_mirror.py"


@pytest.fixture(scope="module")
def mirror():
    spec = importlib.util.spec_from_file_location("dashboard_github_mirror_ut", _MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# dormant-by-default
# ---------------------------------------------------------------------------


def test_is_configured_reflects_token_env(mirror, monkeypatch):
    monkeypatch.delenv("GITHUB_ISSUE_MIRROR_TOKEN", raising=False)
    assert mirror.is_configured() is False
    assert mirror.token() is None
    monkeypatch.setenv("GITHUB_ISSUE_MIRROR_TOKEN", "ghp_x")
    assert mirror.is_configured() is True
    assert mirror.token() == "ghp_x"


def test_blank_token_is_dormant(mirror, monkeypatch):
    # A whitespace-only value is treated as unset (same as the other env helpers).
    monkeypatch.setenv("GITHUB_ISSUE_MIRROR_TOKEN", "   ")
    assert mirror.is_configured() is False


async def test_create_issue_raises_when_dormant(mirror, monkeypatch):
    monkeypatch.delenv("GITHUB_ISSUE_MIRROR_TOKEN", raising=False)
    with pytest.raises(mirror.MirrorNotConfiguredError):
        await mirror.create_issue({"kind": "bug", "title": "x", "body": "y"})


# ---------------------------------------------------------------------------
# pure builders — title / labels / body shaped from the ISSUE_TEMPLATE families
# ---------------------------------------------------------------------------


def test_issue_labels_map_kind_to_template_label(mirror):
    # bug_report.yml -> "bug"; feature_request.yml -> "enhancement".
    assert mirror.issue_labels({"kind": "bug"}) == ["bug"]
    assert mirror.issue_labels({"kind": "suggestion"}) == ["enhancement"]
    # An unknown kind gets no special label (fails safe, never invents one).
    assert mirror.issue_labels({"kind": "other"}) == []
    assert mirror.issue_labels({}) == []


def test_issue_title_prefixes_kind_and_clamps_length(mirror):
    assert mirror.issue_title({"kind": "bug", "title": "It broke"}) == "🐞 It broke"
    assert (
        mirror.issue_title({"kind": "suggestion", "title": "Add X"}) == "💡 Add X"
    )
    # No title -> a safe placeholder, never empty.
    assert "(no title)" in mirror.issue_title({"kind": "bug", "title": "  "})
    # Pathologically long title is clamped (<= 240 chars + emoji/space prefix budget).
    long = mirror.issue_title({"kind": "bug", "title": "z" * 500})
    assert len(long) <= 244


def test_issue_body_bug_shape_includes_surface(mirror):
    body = mirror.issue_body(
        {"kind": "bug", "body": "steps then boom", "surface": "Discord bot"},
    )
    assert "### Where did it happen?" in body
    assert "Discord bot" in body
    assert "steps then boom" in body
    # The mirrored-from-submission provenance footer.
    assert "Mirrored from a moderated public submission" in body


def test_issue_body_suggestion_shape_has_no_surface_header(mirror):
    body = mirror.issue_body({"kind": "suggestion", "body": "please add dark mode"})
    assert "### Proposal" in body
    assert "### Where did it happen?" not in body
    assert "please add dark mode" in body


def test_issue_body_escapes_untrusted_user_input(mirror):
    # The submitted body is public/untrusted -> HTML-escaped before going into the issue
    # markdown (plan §4.2), so a raw <script>/<img> can't pass through verbatim.
    body = mirror.issue_body(
        {"kind": "suggestion", "body": "<script>alert(1)</script> & <b>x</b>"},
    )
    assert "<script>" not in body
    assert "&lt;script&gt;" in body
    assert "&amp;" in body


def test_issue_body_handles_empty_body(mirror):
    body = mirror.issue_body({"kind": "bug", "body": "", "surface": ""})
    assert "no description provided" in body
    assert "_(not specified)_" in body  # empty surface placeholder


# ---------------------------------------------------------------------------
# create_issue POST path against a fake httpx
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Captures the single POST and returns a canned response."""

    def __init__(self, record, response, **_kwargs):
        self._record = record
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, *, json, headers):
        self._record["url"] = url
        self._record["json"] = json
        self._record["headers"] = headers
        return self._response


def _install_fake_httpx(monkeypatch, record, response):
    import types

    fake = types.ModuleType("httpx")

    def _client(**kwargs):
        return _FakeAsyncClient(record, response, **kwargs)

    fake.AsyncClient = _client  # type: ignore[attr-defined]
    monkeypatch.setenv("GITHUB_ISSUE_MIRROR_TOKEN", "ghp_secret")
    monkeypatch.setitem(sys.modules, "httpx", fake)


async def test_create_issue_posts_to_scoped_repo_and_returns_url(mirror, monkeypatch):
    record: dict = {}
    resp = _FakeResponse(
        201,
        {"html_url": "https://github.com/menno420/superbot/issues/7"},
    )
    _install_fake_httpx(monkeypatch, record, resp)

    url = await mirror.create_issue(
        {"kind": "bug", "title": "boom", "body": "it broke", "surface": "Discord bot"},
    )
    assert url == "https://github.com/menno420/superbot/issues/7"
    # Posts to EXACTLY the hardcoded, repo-scoped endpoint (never env-redirectable).
    assert record["url"] == "https://api.github.com/repos/menno420/superbot/issues"
    # Bearer auth with the configured least-privilege token + the API-version pin.
    assert record["headers"]["Authorization"] == "Bearer ghp_secret"
    assert record["headers"]["X-GitHub-Api-Version"] == "2022-11-28"
    # The payload carries the template-shaped title/body/label.
    assert record["json"]["title"] == "🐞 boom"
    assert record["json"]["labels"] == ["bug"]
    assert "it broke" in record["json"]["body"]


async def test_create_issue_omits_labels_for_unknown_kind(mirror, monkeypatch):
    record: dict = {}
    resp = _FakeResponse(201, {"html_url": "https://example/issues/1"})
    _install_fake_httpx(monkeypatch, record, resp)

    await mirror.create_issue({"kind": "other", "title": "t", "body": "b"})
    # No label key at all when the kind has no template label (never an empty/invalid one).
    assert "labels" not in record["json"]


async def test_create_issue_raises_mirror_error_on_non_2xx(mirror, monkeypatch):
    record: dict = {}
    resp = _FakeResponse(422, {"message": "Validation Failed"})
    _install_fake_httpx(monkeypatch, record, resp)

    with pytest.raises(mirror.MirrorError, match="422"):
        await mirror.create_issue({"kind": "bug", "title": "t", "body": "b"})


async def test_create_issue_raises_when_no_html_url(mirror, monkeypatch):
    record: dict = {}
    resp = _FakeResponse(201, {"id": 99})  # success status but no html_url
    _install_fake_httpx(monkeypatch, record, resp)

    with pytest.raises(mirror.MirrorError, match="html_url"):
        await mirror.create_issue({"kind": "bug", "title": "t", "body": "b"})
