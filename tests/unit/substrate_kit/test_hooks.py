"""Tests for the PreToolUse stance guard (plan section 3b — enforcement)."""

import io
import json

from engine import cli
from engine.hooks.stance_guard import (
    TOOL_ACTIONS,
    evaluate_tool,
    settings_snippet,
    tool_from_payload,
    tool_to_action,
)
from engine.lib.config import Config, save_config
from engine.lib.state import JsonStateBackend, default_state
from engine.stances.stances import ACTIONS


def _init(target, stance=None):
    config = Config()
    save_config(target, config)
    state_path = target / config.state_dir / "state.json"
    backend = JsonStateBackend(state_path)
    with backend.transaction():
        for key, value in default_state(config.project_id).items():
            backend.set(key, value)
        if stance is not None:
            backend.set("stance", stance)
    return state_path


# ---------------------------------------------------------------------------
# Tool -> action mapping
# ---------------------------------------------------------------------------


def test_tool_actions_are_valid_categories():
    assert set(TOOL_ACTIONS.values()) <= set(ACTIONS)


def test_tool_to_action_known_and_unknown():
    assert tool_to_action("Edit") == "edit"
    assert tool_to_action("Read") == "read"
    assert tool_to_action("Bash") == "run"
    assert tool_to_action("Task") is None  # carries no stance opinion → fail open


# ---------------------------------------------------------------------------
# Payload parsing (fails open)
# ---------------------------------------------------------------------------


def test_tool_from_payload():
    assert tool_from_payload('{"tool_name": "Edit"}') == "Edit"
    assert tool_from_payload("") == ""
    assert tool_from_payload("not json") == ""
    assert tool_from_payload("[1, 2]") == ""  # non-dict
    assert tool_from_payload('{"tool_name": 5}') == ""  # non-str


# ---------------------------------------------------------------------------
# evaluate_tool — the enforcement decision
# ---------------------------------------------------------------------------


def test_edit_out_of_stance_in_review_warns():
    msg = evaluate_tool("review", "Edit")
    assert msg and "out-of-stance" in msg and "review" in msg


def test_edit_in_debug_is_silent():
    assert evaluate_tool("debug", "Edit") is None


def test_run_out_of_stance_in_question_warns():
    assert evaluate_tool("question", "Bash") is not None


def test_read_is_in_every_stance():
    assert all(evaluate_tool(s, "Read") is None for s in ("question", "review", "plan"))


def test_unknown_tool_and_stance_fail_open():
    assert evaluate_tool("review", "Task") is None  # tool has no opinion
    assert evaluate_tool("bogus-stance", "Edit") is None  # unknown stance → no warn


# ---------------------------------------------------------------------------
# settings_snippet
# ---------------------------------------------------------------------------


def test_settings_snippet_is_valid_pretooluse_json():
    text = settings_snippet("py bootstrap.py hook pretooluse")
    parsed = json.loads(text)
    pre = parsed["hooks"]["PreToolUse"]
    assert pre[0]["hooks"][0]["command"] == "py bootstrap.py hook pretooluse"
    assert pre[0]["matcher"] == "*"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_hooks_list(tmp_path, capsys):
    assert cli.cmd_hooks(tmp_path, build=False) == 0
    out = capsys.readouterr().out
    assert "pretooluse" in out and "wiring command" in out


def test_cli_hooks_build_writes_snippet(tmp_path):
    _init(tmp_path)
    assert cli.cmd_hooks(tmp_path, build=True) == 0
    snippet = tmp_path / ".substrate" / "hooks" / "settings.snippet.json"
    assert snippet.exists()
    assert json.loads(snippet.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]


def test_cli_hook_warns_out_of_stance(tmp_path, monkeypatch, capsys):
    _init(tmp_path, stance="review")
    monkeypatch.setattr("sys.stdin", io.StringIO('{"tool_name": "Edit"}'))
    rc = cli.cmd_hook(tmp_path, "pretooluse")
    err = capsys.readouterr().err
    assert rc == 0  # advisory — never blocks
    assert "out-of-stance" in err


def test_cli_hook_silent_in_stance(tmp_path, monkeypatch, capsys):
    _init(tmp_path, stance="debug")
    monkeypatch.setattr("sys.stdin", io.StringIO('{"tool_name": "Edit"}'))
    assert cli.cmd_hook(tmp_path, "pretooluse") == 0
    assert capsys.readouterr().err == ""


def test_cli_hook_no_state_fails_open(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO('{"tool_name": "Edit"}'))
    assert cli.cmd_hook(tmp_path, "pretooluse") == 0
    assert capsys.readouterr().err == ""


def test_cli_hook_ignores_other_events(tmp_path):
    # A non-pretooluse event returns 0 without touching stdin.
    assert cli.cmd_hook(tmp_path, "stop") == 0


def test_cli_hook_postedit_advises_on_notebook_path(tmp_path, monkeypatch, capsys):
    # The PostToolUse matcher wires NotebookEdit, whose payload carries
    # `notebook_path` (not `file_path`). The advisor must key on it too — else a
    # generated notebook edited via NotebookEdit is matched but never advised.
    _init(tmp_path)
    art = tmp_path / Config().state_dir / "rendered" / "board.ipynb"
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("{}", encoding="utf-8")
    payload = json.dumps(
        {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": str(art)}},
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    assert cli.cmd_hook(tmp_path, "postedit") == 0
    assert "generated artifact" in capsys.readouterr().err


def test_cli_hook_postedit_still_advises_on_file_path(tmp_path, monkeypatch, capsys):
    # Regression guard: the Edit/Write file_path path must keep working.
    _init(tmp_path)
    art = tmp_path / Config().state_dir / "rendered" / "current-state.md"
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("# x\n", encoding="utf-8")
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(art)}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    assert cli.cmd_hook(tmp_path, "postedit") == 0
    assert "generated artifact" in capsys.readouterr().err
