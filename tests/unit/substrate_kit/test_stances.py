"""Tests for the task-stance capability layer (plan section 3b)."""

from pathlib import Path

from engine import cli
from engine.lib.config import Config, save_config
from engine.lib.state import JsonStateBackend, default_state
from engine.stances.stances import (
    ACTIONS,
    DEFAULT_STANCE,
    EDIT,
    READ,
    STANCES,
    action_allowed,
    get_stance,
    is_out_of_stance,
    stance_briefing,
    stance_names,
)


def _init(target: Path) -> Path:
    """Write a default config + state under ``target``; return the state path."""
    config = Config()
    save_config(target, config)
    state_path = target / config.state_dir / "state.json"
    backend = JsonStateBackend(state_path)
    with backend.transaction():
        for key, value in default_state(config.project_id).items():
            backend.set(key, value)
    return state_path


# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------


def test_stance_names_in_declared_order():
    assert stance_names() == ["question", "analysis", "debug", "review", "plan"]


def test_get_stance_known_and_unknown():
    assert get_stance("debug")["name"] == "debug"
    assert get_stance("nope") is None


def test_every_stance_is_well_formed():
    required = {"name", "role", "when_to_use", "reading_route", "tools", "output"}
    for stance in STANCES:
        assert required <= set(stance), stance.get("name")
        assert stance["reading_route"], stance["name"]
        assert stance["tools"], stance["name"]
        assert set(stance["tools"]) <= set(ACTIONS), stance["name"]


def test_default_stance_matches_default_state():
    # Cross-module invariant: the stub field in default_state and the framework's
    # DEFAULT_STANCE must agree, or `stance` (no-arg) misreports a fresh install.
    assert DEFAULT_STANCE in stance_names()
    assert default_state("proj")["stance"] == DEFAULT_STANCE


# ---------------------------------------------------------------------------
# Tool-scope / conformance — the safety-bearing part
# ---------------------------------------------------------------------------


def test_only_debug_permits_edits():
    # The "zero out-of-stance writes" guarantee, pinned at the definition level:
    # exactly one stance may edit files.
    editors = [s["name"] for s in STANCES if EDIT in s["tools"]]
    assert editors == ["debug"]


def test_read_allowed_in_every_stance():
    assert all(action_allowed(name, READ) for name in stance_names())


def test_action_allowed_matrix():
    assert action_allowed("analysis", "run")
    assert not action_allowed("question", "run")
    assert action_allowed("review", "comment")
    assert not action_allowed("debug", "comment")
    assert not action_allowed("unknown-stance", "read")  # unknown → nothing allowed


def test_is_out_of_stance_flags_edit_outside_debug():
    assert is_out_of_stance("review", EDIT)
    assert is_out_of_stance("question", EDIT)
    assert not is_out_of_stance("debug", EDIT)
    # Unknown stance fails OPEN — a misconfigured name never blocks an action.
    assert not is_out_of_stance("unknown-stance", EDIT)


# ---------------------------------------------------------------------------
# Briefing (the orientation-injection primitive)
# ---------------------------------------------------------------------------


def test_briefing_contains_route_tools_and_output():
    text = stance_briefing("debug")
    assert "debug" in text
    assert "runtime_contracts.md" in text  # reading-route
    assert "edit" in text  # tool-scope
    assert "targeted fix" in text  # output contract


def test_briefing_unknown_stance_is_helpful():
    text = stance_briefing("bogus")
    assert "Unknown stance" in text and "question" in text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_set_stance_persists(tmp_path):
    state_path = _init(tmp_path)
    rc = cli.cmd_stance(tmp_path, "debug")
    assert rc == 0
    assert JsonStateBackend(state_path).get("stance") == "debug"


def test_cli_invalid_stance_returns_2(tmp_path):
    _init(tmp_path)
    assert cli.cmd_stance(tmp_path, "bogus") == 2


def test_cli_no_state_returns_1(tmp_path):
    assert cli.cmd_stance(tmp_path, "debug") == 1


def test_cli_show_active_lists_available(tmp_path, capsys):
    _init(tmp_path)
    rc = cli.cmd_stance(tmp_path, None)
    out = capsys.readouterr().out
    assert rc == 0
    assert DEFAULT_STANCE in out
    assert "available:" in out
    for name in stance_names():
        assert name in out


def test_cli_stance_round_trips_via_parser(tmp_path):
    _init(tmp_path)
    rc = cli.main(["stance", "plan", "--target", str(tmp_path)])
    assert rc == 0
    assert JsonStateBackend(tmp_path / ".substrate" / "state.json").get("stance") == "plan"
