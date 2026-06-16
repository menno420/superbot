"""Tests for ``scripts/hermes/railway_logs.py`` — the read-only Railway log reader.

Hermetic: the GraphQL transport is either injected (``PostFn``) or the urllib
layer is monkeypatched, so nothing touches the network. We exercise deployment
selection, log formatting, the auth-header choice, GraphQL error surfacing, and
the missing-token / missing-id guard paths.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "hermes" / "railway_logs.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("railway_logs_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _clean_token_env(monkeypatch):
    # Deterministic token resolution regardless of the CI/host environment.
    for var in (
        "RAILWAY_TOKEN",
        "RAILWAY_PROJECT_TOKEN",
        "RAILWAY_API_TOKEN",
        "RAILWAY_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)


# --- token resolution -------------------------------------------------------


def test_railway_token_is_treated_as_project(mod, monkeypatch):
    monkeypatch.setenv("RAILWAY_TOKEN", "pt")
    monkeypatch.setenv("RAILWAY_API_TOKEN", "at")
    assert mod._resolve_token() == ("pt", True)


def test_api_token_is_account_when_no_project(mod, monkeypatch):
    monkeypatch.setenv("RAILWAY_API_TOKEN", "at")
    assert mod._resolve_token() == ("at", False)


def test_api_key_aliases_account_token(mod, monkeypatch):
    # The owner provisioned the credential under RAILWAY_API_KEY (an account
    # token); it must resolve as a (Bearer) account token, not a project token.
    monkeypatch.setenv("RAILWAY_API_KEY", "ak")
    assert mod._resolve_token() == ("ak", False)


def test_explicit_api_token_wins_over_api_key(mod, monkeypatch):
    monkeypatch.setenv("RAILWAY_API_TOKEN", "at")
    monkeypatch.setenv("RAILWAY_API_KEY", "ak")
    assert mod._resolve_token() == ("at", False)


# --- deployment selection ---------------------------------------------------


def _deploys(*nodes: dict) -> dict:
    return {"deployments": {"edges": [{"node": n} for n in nodes]}}


def test_latest_deployment_prefers_active(mod):
    def post(query, variables):
        return _deploys(
            {"id": "d-building", "status": "BUILDING", "createdAt": "t2"},
            {"id": "d-live", "status": "SUCCESS", "createdAt": "t1"},
        )

    node = mod.latest_deployment(post, project_id="p", service_id="s")
    assert node["id"] == "d-live"


def test_latest_deployment_falls_back_to_newest(mod):
    def post(query, variables):
        return _deploys(
            {"id": "d-newest", "status": "FAILED", "createdAt": "t2"},
            {"id": "d-older", "status": "CRASHED", "createdAt": "t1"},
        )

    node = mod.latest_deployment(post, project_id="p", service_id="s")
    assert node["id"] == "d-newest"


def test_latest_deployment_passes_environment_id(mod):
    seen: dict = {}

    def post(query, variables):
        seen.update(variables)
        return _deploys({"id": "d1", "status": "SUCCESS", "createdAt": "t"})

    mod.latest_deployment(post, project_id="p", service_id="s", environment_id="e")
    assert seen["input"] == {"projectId": "p", "serviceId": "s", "environmentId": "e"}


def test_latest_deployment_omits_environment_when_absent(mod):
    seen: dict = {}

    def post(query, variables):
        seen.update(variables)
        return _deploys({"id": "d1", "status": "SUCCESS", "createdAt": "t"})

    mod.latest_deployment(post, project_id="p", service_id="s")
    assert "environmentId" not in seen["input"]


def test_latest_deployment_raises_when_none(mod):
    def post(query, variables):
        return {"deployments": {"edges": []}}

    with pytest.raises(mod.RailwayError):
        mod.latest_deployment(post, project_id="p", service_id="s")


# --- log fetch + formatting -------------------------------------------------


def test_fetch_logs_returns_entries(mod):
    def post(query, variables):
        assert variables == {"deploymentId": "d1", "limit": 50}
        return {"deploymentLogs": [{"message": "hi"}]}

    assert mod.fetch_logs(post, deployment_id="d1", limit=50) == [{"message": "hi"}]


def test_format_logs_renders_fields(mod):
    logs = [
        {"timestamp": "2026-06-14T10:00:00Z", "severity": "error", "message": "boom"},
        {"message": "bare line"},
    ]
    out = mod.format_logs(logs).splitlines()
    assert out[0] == "2026-06-14T10:00:00Z [ERROR] boom"
    assert out[1] == "bare line"


# --- transport: auth header + GraphQL error surfacing -----------------------


class _FakeResp:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._data


def test_build_poster_account_uses_bearer(mod, monkeypatch):
    captured: dict = {}

    def fake_urlopen(req, timeout=None):
        captured["auth"] = req.get_header("Authorization")
        captured["proj"] = req.get_header("Project-access-token")
        return _FakeResp({"data": {"me": {"id": "u1"}}})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    post = mod.build_poster("tok-abc", is_project_token=False)
    data = post(mod.WHOAMI_QUERY, {})
    assert data == {"me": {"id": "u1"}}
    assert captured["auth"] == "Bearer tok-abc"
    assert captured["proj"] is None


def test_build_poster_project_uses_project_header(mod, monkeypatch):
    captured: dict = {}

    def fake_urlopen(req, timeout=None):
        captured["auth"] = req.get_header("Authorization")
        captured["proj"] = req.get_header("Project-access-token")
        return _FakeResp({"data": {}})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    post = mod.build_poster("proj-tok", is_project_token=True)
    post(mod.WHOAMI_QUERY, {})
    assert captured["auth"] is None
    assert captured["proj"] == "proj-tok"


def test_build_poster_sets_non_default_user_agent(mod, monkeypatch):
    # Cloudflare fronts the API and 1010-bans urllib's default UA; the request
    # must carry an explicit non-``Python-urllib`` User-Agent or every call 403s.
    captured: dict = {}

    def fake_urlopen(req, timeout=None):
        captured["ua"] = req.get_header("User-agent")
        return _FakeResp({"data": {}})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    post = mod.build_poster("tok", is_project_token=False)
    post(mod.WHOAMI_QUERY, {})
    assert captured["ua"] == mod.USER_AGENT
    assert "urllib" not in captured["ua"].lower()


def test_post_raises_on_graphql_errors(mod, monkeypatch):
    def fake_urlopen(req, timeout=None):
        return _FakeResp({"errors": [{"message": "Not Authorized"}]})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    post = mod.build_poster("tok", is_project_token=False)
    with pytest.raises(mod.RailwayError, match="Not Authorized"):
        post(mod.WHOAMI_QUERY, {})


# --- transport: retry / backoff on transient failures -----------------------


def _http_error(code: int, *, body: bytes = b"upstream connect error", headers=None):
    return urllib.error.HTTPError(
        "http://x",
        code,
        "transient",
        headers or {},
        io.BytesIO(body),
    )


def test_post_retries_on_503_then_succeeds(mod, monkeypatch):
    calls = {"n": 0}
    slept: list[float] = []

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _http_error(503)
        return _FakeResp({"data": {"me": {"id": "u1"}}})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    post = mod.build_poster("tok", is_project_token=False, sleep=slept.append)
    assert post(mod.WHOAMI_QUERY, {}) == {"me": {"id": "u1"}}
    assert calls["n"] == 2  # one retry
    assert slept == [0.5]  # backoff_base * 2**0


def test_post_raises_after_exhausting_retries(mod, monkeypatch):
    calls = {"n": 0}
    slept: list[float] = []

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise _http_error(503)

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    post = mod.build_poster(
        "tok",
        is_project_token=False,
        max_retries=2,
        sleep=slept.append,
    )
    with pytest.raises(mod.RailwayError, match="HTTP 503"):
        post(mod.WHOAMI_QUERY, {})
    assert calls["n"] == 3  # initial + 2 retries
    assert slept == [0.5, 1.0]  # 0.5*2**0, 0.5*2**1


def test_post_does_not_retry_on_4xx(mod, monkeypatch):
    calls = {"n": 0}
    slept: list[float] = []

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise _http_error(401, body=b"bad token")

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    post = mod.build_poster("tok", is_project_token=False, sleep=slept.append)
    with pytest.raises(mod.RailwayError, match="HTTP 401"):
        post(mod.WHOAMI_QUERY, {})
    assert calls["n"] == 1  # no retry on auth failure
    assert slept == []


def test_post_retries_on_connection_error_then_succeeds(mod, monkeypatch):
    calls = {"n": 0}
    slept: list[float] = []

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise mod.urllib.error.URLError("connection timeout")
        return _FakeResp({"data": {"ok": True}})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    post = mod.build_poster("tok", is_project_token=False, sleep=slept.append)
    assert post(mod.WHOAMI_QUERY, {}) == {"ok": True}
    assert calls["n"] == 2
    assert slept == [0.5]


def test_retry_delay_is_exponential(mod):
    assert mod._retry_delay(0, _http_error(503), 0.5) == 0.5
    assert mod._retry_delay(1, _http_error(503), 0.5) == 1.0
    assert mod._retry_delay(2, _http_error(503), 0.5) == 2.0


def test_retry_delay_honours_retry_after_header(mod):
    exc = _http_error(429, headers={"Retry-After": "7"})
    assert mod._retry_delay(0, exc, 0.5) == 7.0
    # A non-numeric / hostile header falls back to backoff and stays capped.
    assert mod._retry_delay(3, _http_error(429, headers={"Retry-After": "x"}), 0.5) == 4.0
    assert mod._retry_delay(0, _http_error(429, headers={"Retry-After": "9999"}), 0.5) == 30.0


# --- main() guard paths -----------------------------------------------------


def test_main_no_token_exits_2(mod, monkeypatch, capsys):
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)
    assert mod.main([]) == 2
    assert "No Railway token" in capsys.readouterr().err


def test_main_token_but_no_ids_exits_2(mod, monkeypatch, capsys):
    monkeypatch.setenv("RAILWAY_API_TOKEN", "tok")
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_ID", raising=False)
    monkeypatch.delenv("RAILWAY_SERVICE_ID", raising=False)
    assert mod.main([]) == 2
    assert "RAILWAY_PROJECT_ID" in capsys.readouterr().err


def test_main_whoami_happy_path(mod, monkeypatch, capsys):
    monkeypatch.setenv("RAILWAY_API_TOKEN", "tok")
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)

    def fake_urlopen(req, timeout=None):
        return _FakeResp({"data": {"me": {"id": "u1", "email": "a@b.c"}}})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    assert mod.main(["--whoami"]) == 0
    assert "u1" in capsys.readouterr().out


def test_main_whoami_project_token_guides(mod, monkeypatch, capsys):
    # A project token has no `me` identity; --whoami should guide, not error.
    monkeypatch.setenv("RAILWAY_TOKEN", "proj-tok")
    assert mod.main(["--whoami"]) == 0
    out = capsys.readouterr().out
    assert "Project token detected" in out
    assert "railway_vars.py list" in out


def test_main_fetches_and_formats(mod, monkeypatch, capsys):
    monkeypatch.setenv("RAILWAY_PROJECT_TOKEN", "ptok")
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "p")
    monkeypatch.setenv("RAILWAY_SERVICE_ID", "s")
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)

    def fake_urlopen(req, timeout=None):
        body = json.loads(req.data.decode("utf-8"))
        if "deployments" in body["query"]:
            return _FakeResp(
                {"data": _deploys({"id": "d1", "status": "SUCCESS", "createdAt": "t"})}
            )
        return _FakeResp({"data": {"deploymentLogs": [{"message": "running"}]}})

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    assert mod.main(["-n", "10"]) == 0
    assert "running" in capsys.readouterr().out
