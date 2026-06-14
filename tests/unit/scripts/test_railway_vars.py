"""Tests for ``scripts/hermes/railway_vars.py`` — the Railway env-var read/write tool.

Hermetic: the GraphQL transport is replaced (``build_poster`` is monkeypatched to a
recording fake), so nothing touches the network. We exercise id/token resolution,
read (list/get) vs write (set/unset) routing, value masking, the stdin value path,
and the guard exits.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "hermes" / "railway_vars.py"


@pytest.fixture(scope="module")
def mod():
    # railway_vars does `from railway_logs import ...`; ensure the sibling dir is
    # importable the same way running it as a script would make it.
    sys.path.insert(0, str(_SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("railway_vars_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _recording_post(records: list, variables: dict | None = None):
    def post(query: str, variables_in: dict):
        records.append((query, variables_in))
        if "query variables" in query:
            return {"variables": variables or {}}
        return {}

    return post


def _set_env(monkeypatch, **extra):
    monkeypatch.setenv("RAILWAY_API_TOKEN", "tok")
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "p")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_ID", "e")
    monkeypatch.setenv("RAILWAY_SERVICE_ID", "s")
    for key, value in extra.items():
        monkeypatch.setenv(key, value)


# --- pure helpers -----------------------------------------------------------


def test_mask_hides_body(mod):
    assert mod.mask("supersecretvalue").endswith("chars)")
    assert "supersecret" not in mod.mask("supersecretvalue")
    assert mod.mask("ab") == "**** (2 chars)"


def test_get_variables_returns_map(mod):
    records: list = []
    post = _recording_post(records, {"A": "1", "B": "2"})
    out = mod.get_variables(post, project_id="p", environment_id="e", service_id="s")
    assert out == {"A": "1", "B": "2"}
    assert records[0][1] == {"projectId": "p", "environmentId": "e", "serviceId": "s"}


def test_upsert_sends_input(mod):
    records: list = []
    mod.upsert_variable(
        _recording_post(records),
        project_id="p",
        environment_id="e",
        service_id="s",
        name="K",
        value="V",
    )
    assert "variableUpsert" in records[0][0]
    assert records[0][1]["input"] == {
        "projectId": "p",
        "environmentId": "e",
        "serviceId": "s",
        "name": "K",
        "value": "V",
    }


def test_delete_sends_input(mod):
    records: list = []
    mod.delete_variable(
        _recording_post(records),
        project_id="p",
        environment_id="e",
        service_id="s",
        name="K",
    )
    assert "variableDelete" in records[0][0]
    assert records[0][1]["input"]["name"] == "K"


# --- guard paths ------------------------------------------------------------


def test_main_no_token_exits_2(mod, monkeypatch, capsys):
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)
    assert mod.main(["list"]) == 2
    assert "WRITE-capable token" in capsys.readouterr().err


def test_main_missing_ids_exits_2(mod, monkeypatch, capsys):
    monkeypatch.setenv("RAILWAY_API_TOKEN", "tok")
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)
    for key in ("RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID"):
        monkeypatch.delenv(key, raising=False)
    assert mod.main(["list"]) == 2
    assert "RAILWAY_ENVIRONMENT_ID" in capsys.readouterr().err


# --- read commands ----------------------------------------------------------


def test_list_masks_by_default(mod, monkeypatch, capsys):
    _set_env(monkeypatch)
    post = _recording_post([], {"TOKEN": "supersecretvalue"})
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: post)
    assert mod.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "TOKEN=" in out
    assert "supersecretvalue" not in out


def test_list_reveal_shows_values(mod, monkeypatch, capsys):
    _set_env(monkeypatch)
    post = _recording_post([], {"TOKEN": "supersecretvalue"})
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: post)
    assert mod.main(["list", "--reveal"]) == 0
    assert "supersecretvalue" in capsys.readouterr().out


def test_get_prints_one_value(mod, monkeypatch, capsys):
    _set_env(monkeypatch)
    post = _recording_post([], {"DATABASE_URL": "postgres://x"})
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: post)
    assert mod.main(["get", "DATABASE_URL"]) == 0
    assert capsys.readouterr().out.strip() == "postgres://x"


def test_get_missing_var_exits_2(mod, monkeypatch, capsys):
    _set_env(monkeypatch)
    post = _recording_post([], {"A": "1"})
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: post)
    assert mod.main(["get", "NOPE"]) == 2
    assert "No such variable" in capsys.readouterr().err


# --- write commands ---------------------------------------------------------


def test_set_calls_upsert_and_audits_without_leaking(mod, monkeypatch, capsys):
    _set_env(monkeypatch)
    records: list = []
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: _recording_post(records))
    assert mod.main(["set", "API_KEY", "topsecret"]) == 0
    captured = capsys.readouterr()
    assert any("variableUpsert" in q for q, _ in records)
    assert records[0][1]["input"]["value"] == "topsecret"
    assert "SET API_KEY" in captured.err  # audit line on stderr
    assert "topsecret" not in captured.err  # never echo the secret
    assert "topsecret" not in captured.out


def test_set_reads_value_from_stdin(mod, monkeypatch):
    _set_env(monkeypatch)
    records: list = []
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: _recording_post(records))
    monkeypatch.setattr("sys.stdin", io.StringIO("from-stdin\n"))
    assert mod.main(["set", "API_KEY"]) == 0
    assert records[0][1]["input"]["value"] == "from-stdin"


def test_unset_calls_delete(mod, monkeypatch, capsys):
    _set_env(monkeypatch)
    records: list = []
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: _recording_post(records))
    assert mod.main(["unset", "OLD_VAR"]) == 0
    assert any("variableDelete" in q for q, _ in records)
    assert "UNSET OLD_VAR" in capsys.readouterr().err


def test_set_default_triggers_deploy(mod, monkeypatch, capsys):
    _set_env(monkeypatch)
    records: list = []
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: _recording_post(records))
    assert mod.main(["set", "K", "V"]) == 0
    assert "skipDeploys" not in records[0][1]["input"]
    assert "redeploy" in capsys.readouterr().err


def test_set_no_deploy_stages_without_redeploy(mod, monkeypatch, capsys):
    _set_env(monkeypatch)
    records: list = []
    monkeypatch.setattr(mod, "build_poster", lambda token, **kw: _recording_post(records))
    assert mod.main(["set", "K", "V", "--no-deploy"]) == 0
    assert records[0][1]["input"]["skipDeploys"] is True
    assert "no redeploy" in capsys.readouterr().err
