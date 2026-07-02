"""Tests for the one-step adopt flow (Lane B8).

Covers: every ADOPT_PLAN target planted; re-adopt keeps (never clobbers)
hand-edited files; the .claude/ opt-in gate; the staged <state_dir> tree;
the planted ledger parsing through ``engine.ledger``; the guardrail refusal;
badge-cleanliness of the freshly planted doc tree; and the CI snippet.

``engine.adopt`` imports ``engine.hooks.settings`` (built by lane B7 in
parallel); until that module lands these tests skip rather than red the suite.
"""

import json
from pathlib import Path

import pytest

pytest.importorskip("engine.hooks.settings")

from engine.adopt import ADOPT_PLAN, adopt, ci_snippet
from engine.agents.agents import AGENTS
from engine.checks.check_docs import run_doc_checks
from engine.ledger import parse_ledger
from engine.lib.config import Config
from engine.lib.guardrail import UnsafeTargetError
from engine.lib.state import JsonStateBackend, default_state
from engine.skills.skills import SKILLS


def _make_backend(root: Path, config: Config, answers: dict | None = None):
    backend = JsonStateBackend(root / config.state_dir / "state.json")
    with backend.transaction():
        for key, value in default_state(config.project_id).items():
            backend.set(key, value)
        for slot, value in (answers or {}).items():
            slots = backend.get("slots", {})
            slots[slot] = "filled"
            backend.set("slots", slots)
            values = backend.get("slot_values", {})
            values[slot] = {"value": value, "status": "confirmed"}
            backend.set("slot_values", values)
    return backend


def _adopt_into(tmp_path: Path, *, include_claude: bool = False, config=None):
    root = tmp_path / "repo"
    config = config or Config()
    backend = _make_backend(root, config)
    lines = adopt(
        root,
        config,
        backend,
        kit_root=tmp_path / "kit",
        include_claude=include_claude,
    )
    return root, config, lines


# ---------------------------------------------------------------------------
# Planting
# ---------------------------------------------------------------------------


def test_every_plan_target_planted(tmp_path):
    root, _, lines = _adopt_into(tmp_path)
    for _, rel in ADOPT_PLAN:
        assert (root / rel).is_file(), rel
        assert f"planted: {rel}" in lines
    assert (root / ".sessions" / "README.md").is_file()
    assert (root / "project.index.json").is_file()


def test_claude_md_is_staged_not_planted(tmp_path):
    root, config, _ = _adopt_into(tmp_path)
    assert not (root / "CLAUDE.md").exists()
    assert (root / config.state_dir / "claude" / "CLAUDE.md").is_file()
    assert "CLAUDE.md.tmpl" not in {name for name, _ in ADOPT_PLAN}


def test_unfilled_placeholders_stay_visible(tmp_path):
    root, _, _ = _adopt_into(tmp_path)
    text = (root / "CONSTITUTION.md").read_text(encoding="utf-8")
    assert "${project_name}" in text


def test_filled_slot_renders_into_planted_doc(tmp_path):
    root = tmp_path / "repo"
    config = Config()
    backend = _make_backend(root, config, {"project_name": "demobot"})
    adopt(root, config, backend, kit_root=tmp_path / "kit")
    text = (root / "CONSTITUTION.md").read_text(encoding="utf-8")
    assert "demobot" in text
    assert "${project_name}" not in text


def test_readopt_reports_kept_and_does_not_clobber(tmp_path):
    root, config, _ = _adopt_into(tmp_path)
    edited = root / "docs" / "architecture.md"
    edited.write_text("# hand-edited\nkeep me\n", encoding="utf-8")
    backend = JsonStateBackend(root / config.state_dir / "state.json")
    lines = adopt(root, config, backend, kit_root=tmp_path / "kit")
    assert "kept: docs/architecture.md" in lines
    assert edited.read_text(encoding="utf-8") == "# hand-edited\nkeep me\n"
    for _, rel in ADOPT_PLAN:
        assert f"kept: {rel}" in lines
        assert f"planted: {rel}" not in lines


def test_docs_root_remap(tmp_path):
    root = tmp_path / "repo"
    config = Config(docs_root="documentation")
    backend = _make_backend(root, config)
    lines = adopt(root, config, backend, kit_root=tmp_path / "kit")
    assert (root / "documentation" / "decisions.md").is_file()
    assert not (root / "docs").exists()
    assert "planted: documentation/decisions.md" in lines


# ---------------------------------------------------------------------------
# .claude/ opt-in gate
# ---------------------------------------------------------------------------


def test_claude_tree_not_written_without_opt_in(tmp_path):
    root, _, _ = _adopt_into(tmp_path)
    assert not (root / ".claude").exists()


def test_include_claude_writes_live_tree_skip_if_exists(tmp_path):
    root, _, lines = _adopt_into(tmp_path, include_claude=True)
    assert (root / ".claude" / "CLAUDE.md").is_file()
    assert (root / ".claude" / "settings.json").is_file()
    assert "planted: .claude/CLAUDE.md" in lines
    json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    # Re-adopt keeps a hand-edited live file.
    (root / ".claude" / "CLAUDE.md").write_text("mine\n", encoding="utf-8")
    config = Config()
    backend = JsonStateBackend(root / config.state_dir / "state.json")
    lines = adopt(
        root, config, backend, kit_root=tmp_path / "kit", include_claude=True
    )
    assert "kept: .claude/CLAUDE.md" in lines
    assert (root / ".claude" / "CLAUDE.md").read_text(encoding="utf-8") == "mine\n"


# ---------------------------------------------------------------------------
# Staged tree
# ---------------------------------------------------------------------------


def test_staged_tree_contains_all_packs(tmp_path):
    root, config, lines = _adopt_into(tmp_path)
    state = root / config.state_dir
    assert (state / "claude" / "CLAUDE.md").is_file()
    assert len(list(state.glob("skills/*/SKILL.md"))) == len(SKILLS)
    assert len(list(state.glob("agents/*.md"))) == len(AGENTS)
    assert (state / "hooks" / "settings.template.json").is_file()
    assert (state / "hooks" / "README.md").is_file()
    assert (state / "ci" / "quality.yml.example").is_file()
    staged = [line for line in lines if line.startswith("staged: ")]
    assert f"staged: {config.state_dir}/claude/CLAUDE.md" in staged
    assert f"staged: {config.state_dir}/ci/quality.yml.example" in staged
    settings_text = (state / "hooks" / "settings.template.json").read_text(
        encoding="utf-8"
    )
    json.loads(settings_text)


def test_report_ends_with_next_steps(tmp_path):
    _, _, lines = _adopt_into(tmp_path)
    assert lines[-1].startswith("next steps:")
    assert "bootstrap ask" in lines[-1]
    assert "mode" in lines[-1]


# ---------------------------------------------------------------------------
# Planted content quality
# ---------------------------------------------------------------------------


def test_planted_decisions_ledger_parses_with_an_entry(tmp_path):
    root, _, _ = _adopt_into(tmp_path)
    text = (root / "docs" / "decisions.md").read_text(encoding="utf-8")
    entries = parse_ledger(text)
    assert len(entries) >= 1
    assert entries[0]["id"] == "D-0001"


def test_planted_docs_have_no_badge_findings(tmp_path):
    root, config, _ = _adopt_into(tmp_path)
    findings = run_doc_checks(
        root / config.docs_root,
        config.badge_tokens,
        config.readpath_docs,
    )
    badge = [f for f in findings if f.kind == "badge"]
    assert badge == [], badge


def test_sessions_readme_names_convention_and_markers(tmp_path):
    root, config, _ = _adopt_into(tmp_path)
    text = (root / config.sessions_dir / "README.md").read_text(encoding="utf-8")
    assert "born-red" in text
    for marker in config.session_markers:
        assert marker["label"] in text


def test_planted_index_skeleton_is_valid_json(tmp_path):
    root, _, _ = _adopt_into(tmp_path)
    data = json.loads((root / "project.index.json").read_text(encoding="utf-8"))
    assert data["areas"][0]["name"] == "example-area"


# ---------------------------------------------------------------------------
# Guardrail
# ---------------------------------------------------------------------------


def test_adopt_refuses_the_kits_own_tree():
    kit_root = Path("/srv/substrate-kit")
    config = Config()
    backend = JsonStateBackend(kit_root / config.state_dir / "state.json")
    with pytest.raises(UnsafeTargetError):
        adopt(kit_root, config, backend, kit_root=kit_root)


# ---------------------------------------------------------------------------
# ci_snippet
# ---------------------------------------------------------------------------


def test_ci_snippet_is_fully_commented_and_runs_strict_check():
    text = ci_snippet()
    assert "bootstrap.py check --strict" in text
    needles = ("docs", "session-log", "namespace", "seam", "orientation", "ledger")
    for needle in needles:
        assert needle in text, needle
    assert all(line.startswith("#") for line in text.splitlines() if line.strip())
