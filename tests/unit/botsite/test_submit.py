"""Unit tests for the public ``/submit`` intake (unit P4).

Skipped automatically when the web deps are absent (CI installs only the bot's
``requirements.txt``), so it never reddens CI; run locally after
``pip install -r botsite/requirements.txt``.

The INSERT path is **mocked** — these tests never open a DB connection. They cover the
behaviour P4 owns: the honeypot silently drops bots, server-side validation rejects
bad/empty input with a friendly (non-leaky) message, a valid post reaches the
INSERT-only ``insert_pending`` with sanitised args and redirects (PRG), the per-IP
rate-limit trips, and the form renders the empty / thank-you / dormant states.
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

_FORM_HEADERS = {"content-type": "application/x-www-form-urlencoded"}


@pytest.fixture(scope="module")
def app_module():
    # load_web_app puts botsite/ first on sys.path and isolates its bare sibling
    # imports (`submit` / `submissions_db` / `ratelimit`) from the dashboard's
    # same-named modules, so the load is correct regardless of test run order.
    return load_web_app(_APP, "botsite_app_ut")


@pytest.fixture
def submit_mod(app_module):
    import submit

    return submit


@pytest.fixture
def db_mod(app_module):
    import submissions_db

    return submissions_db


@pytest.fixture
def client(app_module, submit_mod, db_mod, monkeypatch):
    """A TestClient with the store forced 'configured' and the limiters reset.

    The INSERT is replaced by an async spy that records its kwargs and never touches
    a DB; ``is_configured`` is forced True so the live path is exercised. Each test
    starts with empty rate-limit windows.

    The spy stays **faithful to the real contract**: ``insert_pending`` validates +
    sanitises via ``build_insert`` before writing, so the spy runs ``build_insert``
    too — that raises ``SubmissionValidationError`` on bad input exactly as the real
    path does (and records the *sanitised* values), without opening a connection. This
    is what lets the validation tests exercise the route's real exception handling.
    """
    monkeypatch.setattr(db_mod, "is_configured", lambda: True)

    calls: list[dict] = []

    async def _fake_insert(**kwargs):
        # Same validation/sanitisation the real insert_pending performs first.
        db_mod.build_insert(**kwargs)
        calls.append(kwargs)
        return 1

    monkeypatch.setattr(db_mod, "insert_pending", _fake_insert)

    submit_mod._SUBMIT_LIMITER_MINUTE.reset()
    submit_mod._SUBMIT_LIMITER_HOUR.reset()

    test_client = TestClient(app_module.app)
    test_client.inserts = calls  # type: ignore[attr-defined]
    return test_client


# ---------------------------------------------------------------------------
# GET — the form renders, and its states
# ---------------------------------------------------------------------------


def test_get_renders_form_with_all_fields(client):
    resp = client.get("/submit")
    assert resp.status_code == 200
    body = resp.text
    # Every non-defaulted submissions column is represented (plan §2.3 field list).
    assert 'name="kind"' in body
    assert 'name="title"' in body
    assert 'name="body"' in body
    assert 'name="surface"' in body
    assert 'name="contact"' in body
    # The honeypot field is present (hidden) so bots fill it.
    assert 'name="website"' in body
    # Friendly "reviewed, not all ship" copy + an accurate privacy note.
    assert "reviewed" in body.lower()
    assert "salted" in body.lower()
    # And it must NOT claim "no personal data is collected".
    assert "no personal data" not in body.lower()


def test_get_thank_you_state(client):
    resp = client.get("/submit?submitted=1")
    assert resp.status_code == 200
    assert "queued for review" in resp.text.lower()


def test_get_dormant_state(client, db_mod, monkeypatch):
    monkeypatch.setattr(db_mod, "is_configured", lambda: False)
    resp = client.get("/submit")
    assert resp.status_code == 200
    assert "isn't accepting submissions" in resp.text.lower()


# ---------------------------------------------------------------------------
# POST — honeypot drops bots
# ---------------------------------------------------------------------------


def test_honeypot_filled_is_silently_dropped(client):
    resp = client.post(
        "/submit",
        content="kind=bug&title=spam&body=spam&website=i-am-a-bot",
        headers=_FORM_HEADERS,
        follow_redirects=False,
    )
    # Looks like success to the bot (no hint it was caught)…
    assert resp.status_code == 303
    assert resp.headers["location"] == "/submit?submitted=1"
    # …but nothing was written.
    assert client.inserts == []


# ---------------------------------------------------------------------------
# POST — server-side validation
# ---------------------------------------------------------------------------


def test_missing_title_is_rejected(client):
    resp = client.post(
        "/submit",
        content="kind=bug&title=&body=something",
        headers=_FORM_HEADERS,
    )
    assert resp.status_code == 400
    assert client.inserts == []
    # Friendly message, never the raw validation detail.
    assert "title" in resp.text.lower()
    assert "SubmissionValidationError" not in resp.text


def test_missing_body_is_rejected(client):
    resp = client.post(
        "/submit",
        content="kind=suggestion&title=Idea&body=",
        headers=_FORM_HEADERS,
    )
    assert resp.status_code == 400
    assert client.inserts == []


def test_bad_kind_is_rejected(client):
    resp = client.post(
        "/submit",
        content="kind=malware&title=t&body=b",
        headers=_FORM_HEADERS,
    )
    assert resp.status_code == 400
    assert client.inserts == []


def test_validation_repopulates_entered_values(client):
    # A rejected post re-renders the form with what the user typed (so they don't
    # retype). Body is missing here; the title should survive.
    resp = client.post(
        "/submit",
        content="kind=bug&title=My+real+title&body=",
        headers=_FORM_HEADERS,
    )
    assert resp.status_code == 400
    assert "My real title" in resp.text


# ---------------------------------------------------------------------------
# POST — the happy path reaches the INSERT-only seam with sanitised args
# ---------------------------------------------------------------------------


def test_valid_submission_inserts_and_redirects(client):
    resp = client.post(
        "/submit",
        content="kind=bug&title=It+broke&body=Steps+here&surface=bot&contact=me%40x.io",
        headers=_FORM_HEADERS,
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/submit?submitted=1"
    assert len(client.inserts) == 1
    call = client.inserts[0]
    assert call["kind"] == "bug"
    assert call["title"] == "It broke"
    assert call["body"] == "Steps here"
    assert call["surface"] == "bot"
    assert call["contact"] == "me@x.io"
    # The raw IP is passed to the store (which hashes it) — and source_ip is present.
    assert "source_ip" in call


def test_optional_fields_pass_none_when_blank(client):
    resp = client.post(
        "/submit",
        content="kind=suggestion&title=Add+a+thing&body=Please&surface=&contact=",
        headers=_FORM_HEADERS,
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert len(client.inserts) == 1
    call = client.inserts[0]
    assert call["surface"] is None
    assert call["contact"] is None


def test_real_insert_path_validates_without_a_db(client, db_mod):
    # Sanity: the store's pure validation/sanitisation (build_insert) is what the
    # route relies on — confirm it rejects a bad kind and sanitises, no DB needed.
    with pytest.raises(db_mod.SubmissionValidationError):
        db_mod.build_insert(kind="nope", title="t", body="b")
    sql, params = db_mod.build_insert(
        kind="bug", title="  hi  ", body="world", surface="bot"
    )
    assert "status" not in sql.lower().split("values")[1] or "'pending'" in sql.lower()
    assert params[0] == "bug"
    assert params[1] == "hi"  # trimmed


# ---------------------------------------------------------------------------
# POST — rate limiting
# ---------------------------------------------------------------------------


def test_rate_limit_trips_after_the_minute_cap(client, submit_mod):
    cap = submit_mod._SUBMIT_LIMITER_MINUTE.max_events
    body = "kind=bug&title=t&body=b"
    for _ in range(cap):
        ok = client.post(
            "/submit", content=body, headers=_FORM_HEADERS, follow_redirects=False
        )
        assert ok.status_code == 303
    # The next one within the window is rejected with 429 and writes nothing more.
    blocked = client.post(
        "/submit", content=body, headers=_FORM_HEADERS, follow_redirects=False
    )
    assert blocked.status_code == 429
    assert len(client.inserts) == cap


# ---------------------------------------------------------------------------
# POST — dormant store is a friendly state, not a crash
# ---------------------------------------------------------------------------


def test_post_when_dormant_is_friendly(client, db_mod, monkeypatch):
    monkeypatch.setattr(db_mod, "is_configured", lambda: False)
    resp = client.post(
        "/submit",
        content="kind=bug&title=t&body=b",
        headers=_FORM_HEADERS,
    )
    assert resp.status_code == 503
    assert client.inserts == []
    assert "unavailable" in resp.text.lower()


# ---------------------------------------------------------------------------
# structural — the router is now real, and decoupling holds
# ---------------------------------------------------------------------------


def test_submit_route_is_reachable_now(client):
    # P4 fills the stub, so /submit now resolves (200, not the stub-era 404). We check
    # reachability rather than introspecting app.routes: this FastAPI version mounts an
    # included router lazily (app.routes shows an _IncludedRouter with no .path until
    # the router is built at request time), so the route only shows up via a request.
    assert client.get("/submit").status_code == 200
    # And the router itself carries the two routes (the stub had none).
    import submit

    methods = {tuple(sorted(r.methods)) for r in submit.router.routes}
    assert ("GET",) in methods and ("POST",) in methods


def test_submit_module_does_not_import_disbot(submit_mod):
    src = Path(submit_mod.__file__).read_text(encoding="utf-8")
    assert "import disbot" not in src
    assert "from disbot" not in src
