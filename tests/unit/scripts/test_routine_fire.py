"""Tests for ``scripts/hermes/routine_fire.py`` — the robust dispatch helper (Q-0141)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "hermes" / "routine_fire.py"

_spec = importlib.util.spec_from_file_location("routine_fire", _MOD)
assert _spec
assert _spec.loader
rf = importlib.util.module_from_spec(_spec)
sys.modules["routine_fire"] = rf
_spec.loader.exec_module(rf)


# --- config resolution ------------------------------------------------------------------


def test_load_config_from_environ() -> None:
    cfg = rf.load_config(
        environ={"CLAUDE_ROUTINE_FIRE_URL": "u", "CLAUDE_ROUTINE_TOKEN": "t"},
        env_file=Path("/nonexistent"),
    )
    assert cfg["CLAUDE_ROUTINE_FIRE_URL"] == "u"
    assert cfg["CLAUDE_ROUTINE_TOKEN"] == "t"


def test_load_config_falls_back_to_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / "routine.env"
    env_file.write_text(
        '# comment\nCLAUDE_ROUTINE_FIRE_URL=fileurl\nCLAUDE_ROUTINE_TOKEN="filetok"\n',
        encoding="utf-8",
    )
    cfg = rf.load_config(environ={}, env_file=env_file)
    assert cfg["CLAUDE_ROUTINE_FIRE_URL"] == "fileurl"
    assert cfg["CLAUDE_ROUTINE_TOKEN"] == "filetok"  # quotes stripped


# --- request building -------------------------------------------------------------------


def test_build_request_carries_token_and_payload() -> None:
    cfg = {
        "CLAUDE_ROUTINE_FIRE_URL": "https://x/fire",
        "CLAUDE_ROUTINE_TOKEN": "SEKRET",
    }
    req = rf.build_request(cfg, "multi\nline\nwork order")
    assert req.method == "POST"
    assert req.full_url == "https://x/fire"
    assert json.loads(req.data.decode())["text"] == "multi\nline\nwork order"
    assert "SEKRET" in (req.get_header("Authorization") or "")


def test_redacted_headers_masks_only_authorization() -> None:
    out = rf.redacted_headers(
        {"Authorization": "Bearer SEKRET", "Content-type": "application/json"},
    )
    assert "SEKRET" not in json.dumps(out)
    assert out["Authorization"] == "Bearer ***redacted***"
    assert out["Content-type"] == "application/json"


# --- main / CLI behaviour ---------------------------------------------------------------


def test_dry_run_never_leaks_the_token(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.setattr(
        rf,
        "load_config",
        lambda *a, **k: {
            "CLAUDE_ROUTINE_FIRE_URL": "https://x/fire",
            "CLAUDE_ROUTINE_TOKEN": "SUPERSEKRET",
            "CLAUDE_ROUTINE_BETA": "beta",
        },
    )
    wo = tmp_path / "wo.txt"
    wo.write_text("do the thing", encoding="utf-8")
    assert rf.main(["--file", str(wo), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "SUPERSEKRET" not in out  # the whole point
    assert "***redacted***" in out
    assert "do the thing" in out  # payload is shown


def test_missing_config_exits_1(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(rf, "load_config", lambda *a, **k: {})
    wo = tmp_path / "wo.txt"
    wo.write_text("x", encoding="utf-8")
    assert rf.main(["--file", str(wo)]) == 1


def test_empty_work_order_exits_2(tmp_path: Path) -> None:
    wo = tmp_path / "empty.txt"
    wo.write_text("   \n", encoding="utf-8")
    assert rf.main(["--file", str(wo)]) == 2
