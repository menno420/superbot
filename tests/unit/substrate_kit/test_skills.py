"""Tests for the skills layer + the skill/stance precedence model (section 3c)."""

from engine import cli
from engine.interview.question_bank import QUESTIONS
from engine.lib.config import Config, save_config
from engine.lib.state import JsonStateBackend, default_state
from engine.render import find_placeholders
from engine.skills.skills import (
    SKILLS,
    action_permitted,
    get_skill,
    skill_capabilities,
    skill_document,
    skill_frontmatter,
    skill_names,
    skill_permits,
    skill_relpath,
)
from engine.stances.stances import EDIT, READ, RUN


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


def test_starter_pack_present_and_ordered():
    assert skill_names() == [
        "session-close",
        "quality-gate",
        "review",
        "repo-health",
        "deep-research",
        "question",
        "analysis",
    ]


def test_every_skill_is_well_formed():
    required = {"name", "description", "capabilities", "body"}
    for skill in SKILLS:
        assert required <= set(skill), skill.get("name")
        assert skill["description"], skill["name"]
        assert skill["body"], skill["name"]


def test_get_skill_known_and_unknown():
    assert get_skill("quality-gate")["name"] == "quality-gate"
    assert get_skill("nope") is None


def test_skill_capabilities_include_implicit_read():
    assert skill_capabilities("session-close") == [READ, EDIT, RUN]
    assert skill_capabilities("question") == [READ]  # read-only skill
    assert skill_capabilities("unknown") == []


def test_skill_bodies_only_reference_known_bank_slots():
    bank = {q["slot"] for q in QUESTIONS}
    for skill in SKILLS:
        unknown = find_placeholders(skill["body"]) - bank
        assert not unknown, f"{skill['name']} references non-bank slots: {unknown}"


# ---------------------------------------------------------------------------
# Precedence — a skill's declared capability overrides the ambient stance
# ---------------------------------------------------------------------------


def test_skill_permits_declared_only():
    assert skill_permits("session-close", EDIT)
    assert not skill_permits(
        "quality-gate", EDIT
    )  # quality-gate declares run, not edit


def test_skill_capability_overrides_stance():
    # The headline §3c rule: review stance forbids edits, but an invoked
    # session-close (which declares it edits) may write even so.
    assert action_permitted("review", EDIT) is False
    assert action_permitted("review", EDIT, "session-close") is True
    # A skill grants only what it declared — quality-gate (run-only) cannot edit.
    assert action_permitted("review", EDIT, "quality-gate") is False
    # With no skill, the stance's own tool-scope rules.
    assert action_permitted("debug", EDIT) is True


# ---------------------------------------------------------------------------
# Emission — native SKILL.md (metadata-first frontmatter + body)
# ---------------------------------------------------------------------------


def test_frontmatter_is_native_and_quoted():
    fm = skill_frontmatter(get_skill("review"))
    assert fm.startswith("---\nname: review\n")
    assert 'description: "' in fm and fm.rstrip().endswith("---")


def test_skill_relpath_shape():
    assert skill_relpath(get_skill("analysis")) == "skills/analysis/SKILL.md"


def test_skill_document_wraps_body():
    doc = skill_document(get_skill("question"), "BODY TEXT")
    assert doc.startswith("---\nname: question")
    assert "# question\n\nBODY TEXT\n" in doc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_skills_list(tmp_path, capsys):
    rc = cli.cmd_skills(tmp_path, build=False)
    out = capsys.readouterr().out
    assert rc == 0
    for name in skill_names():
        assert name in out
    assert "capabilities" in out


def test_cli_skills_build_writes_native_files(tmp_path):
    _init(tmp_path)
    rc = cli.cmd_skills(tmp_path, build=True)
    assert rc == 0
    emitted = tmp_path / ".substrate" / "skills" / "session-close" / "SKILL.md"
    assert emitted.exists()
    text = emitted.read_text(encoding="utf-8")
    assert text.startswith("---\nname: session-close")
    assert "# session-close" in text


def test_cli_skills_build_via_parser(tmp_path):
    _init(tmp_path)
    rc = cli.main(["skills", "--build", "--target", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / ".substrate" / "skills" / "analysis" / "SKILL.md").exists()
