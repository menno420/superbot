"""Tests for the persona (sub-agent) layer (plan section 3c, second half)."""

from engine import cli
from engine.agents.agents import (
    AGENTS,
    agent_document,
    agent_frontmatter,
    agent_names,
    agent_relpath,
    get_agent,
)
from engine.interview.question_bank import QUESTIONS
from engine.lib.config import Config, save_config
from engine.lib.state import JsonStateBackend, default_state
from engine.render import find_placeholders

# Personas are read-only specialists — these are the only tools they may declare.
_READONLY = {"Read", "Grep", "Glob"}


def _init(target):
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


def test_starter_personas_present_and_ordered():
    assert agent_names() == ["architect", "reviewer", "researcher"]


def test_get_agent_known_and_unknown():
    assert get_agent("reviewer")["name"] == "reviewer"
    assert get_agent("nope") is None


def test_every_persona_is_well_formed():
    required = {"name", "description", "tools", "body"}
    for agent in AGENTS:
        assert required <= set(agent), agent.get("name")
        assert agent["description"] and agent["body"], agent["name"]
        assert agent["tools"], agent["name"]


def test_personas_are_read_only():
    # The safety property: a spawned persona declares only read tools — no
    # Edit/Write/Bash ever leaks into a sub-agent.
    for agent in AGENTS:
        assert set(agent["tools"]) <= _READONLY, agent["name"]


def test_persona_bodies_only_reference_known_bank_slots():
    bank = {q["slot"] for q in QUESTIONS}
    for agent in AGENTS:
        unknown = find_placeholders(agent["body"]) - bank
        assert not unknown, f"{agent['name']} references non-bank slots: {unknown}"


# ---------------------------------------------------------------------------
# Emission — native .claude/agents/<name>.md
# ---------------------------------------------------------------------------


def test_frontmatter_has_name_description_tools():
    fm = agent_frontmatter(get_agent("architect"))
    assert fm.startswith("---\nname: architect\n")
    assert 'description: "' in fm
    assert "tools: Read, Grep, Glob" in fm
    assert fm.rstrip().endswith("---")


def test_agent_relpath_is_flat_file():
    assert agent_relpath(get_agent("researcher")) == "agents/researcher.md"


def test_agent_document_is_frontmatter_plus_body():
    doc = agent_document(get_agent("reviewer"), "BODY TEXT")
    assert doc.startswith("---\nname: reviewer")
    assert doc.rstrip().endswith("BODY TEXT")
    # No extra markdown heading — the agent body IS the system prompt.
    assert "\n# reviewer\n" not in doc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_agents_list(tmp_path, capsys):
    rc = cli.cmd_agents(tmp_path, build=False)
    out = capsys.readouterr().out
    assert rc == 0
    for name in agent_names():
        assert name in out


def test_cli_agents_build_writes_native_files(tmp_path):
    _init(tmp_path)
    rc = cli.cmd_agents(tmp_path, build=True)
    assert rc == 0
    emitted = tmp_path / ".substrate" / "agents" / "architect.md"
    assert emitted.exists()
    text = emitted.read_text(encoding="utf-8")
    assert text.startswith("---\nname: architect")
    assert "tools: Read, Grep, Glob" in text


def test_cli_agents_build_via_parser(tmp_path):
    _init(tmp_path)
    rc = cli.main(["agents", "--build", "--target", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / ".substrate" / "agents" / "reviewer.md").exists()
