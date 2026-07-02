"""Tests for the hook settings template + fill table (plan §5.B, Lane B7)."""

import json

from engine.hooks.settings import full_settings_template, hooks_fill_table
from engine.lib.config import Config

EVENT_TO_CLI = {
    "PreToolUse": "pretooluse",
    "SessionStart": "sessionstart",
    "PostToolUse": "postedit",
    "Stop": "stopcheck",
}


# ---------------------------------------------------------------------------
# full_settings_template
# ---------------------------------------------------------------------------


def test_template_parses_and_wires_all_four_events():
    parsed = json.loads(full_settings_template(Config(interpreter="py3")))
    hooks = parsed["hooks"]
    assert set(hooks) == set(EVENT_TO_CLI)
    for event, cli_event in EVENT_TO_CLI.items():
        command = hooks[event][0]["hooks"][0]["command"]
        assert command == f"py3 bootstrap.py hook {cli_event}"
        assert hooks[event][0]["hooks"][0]["type"] == "command"


def test_template_matchers():
    parsed = json.loads(full_settings_template(Config()))
    hooks = parsed["hooks"]
    assert hooks["PreToolUse"][0]["matcher"] == "*"
    assert hooks["PostToolUse"][0]["matcher"] == "Edit|Write|NotebookEdit"
    assert "matcher" not in hooks["SessionStart"][0]
    assert "matcher" not in hooks["Stop"][0]


def test_template_uses_config_interpreter():
    text = full_settings_template(Config(interpreter="/usr/bin/python3.12"))
    assert "/usr/bin/python3.12 bootstrap.py hook sessionstart" in text


def test_template_is_two_space_indented_json_text():
    text = full_settings_template(Config())
    assert text.endswith("\n")
    assert '\n  "hooks"' in text  # 2-space indent at the first level


# ---------------------------------------------------------------------------
# hooks_fill_table
# ---------------------------------------------------------------------------


def test_fill_table_mentions_every_field():
    text = hooks_fill_table()
    for needle in (
        "interpreter",
        "interpreter_for_checks",
        "bootstrap.py",
        "state_dir",
        "docs_root",
        "sessions_dir",
        "cadence",
    ):
        assert needle in text


def test_fill_table_has_the_contract_header_row():
    text = hooks_fill_table()
    assert "| field | what must match your repo |" in text


def test_fill_table_carries_the_install_instruction():
    text = hooks_fill_table()
    assert ".claude/settings.json" in text
    assert "stages" in text  # the kit stages, never writes .claude/
