"""Tests for ``scripts/hermes/build_skills.py``.

Guards the docs -> SKILL.md generator: every skill doc must produce a valid
Hermes skill artifact, and the committed artifacts must stay in sync with the
docs (the ``--check`` freshness gate, mirroring the agent-context pack test).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_BUILDER = REPO_ROOT / "scripts" / "hermes" / "build_skills.py"

_spec = importlib.util.spec_from_file_location("hermes_build_skills", _BUILDER)
assert _spec and _spec.loader
build_skills = importlib.util.module_from_spec(_spec)
sys.modules["hermes_build_skills"] = build_skills
_spec.loader.exec_module(build_skills)


def test_every_skill_doc_builds() -> None:
    rendered = build_skills.build_all()
    # One artifact per skill doc (README excluded).
    docs = [
        p
        for p in build_skills.SKILL_DOCS_DIR.glob("*.md")
        if p.name != "README.md"
    ]
    assert len(rendered) == len(docs)
    assert rendered, "expected at least one skill doc to build"


@pytest.mark.parametrize("path,content", list(build_skills.build_all().items()))
def test_required_frontmatter_present(path: Path, content: str) -> None:
    # Frontmatter block exists and carries every Hermes-required field.
    assert content.startswith("---\n")
    head = content.split("---", 2)[1]
    for field in ("name:", "description:", "version:", "author:", "license:"):
        assert field in head, f"{path.name}: missing {field}"
    assert head.count("name: superbot-") == 1
    # Generated marker so nobody hand-edits the artifact.
    assert build_skills.GENERATED_MARKER in content
    # Prompt body is non-empty and read-only by construction.
    body = content.split("-->", 1)[1].strip()
    assert len(body) > 100, f"{path.name}: prompt body looks empty"


def test_morning_briefing_self_schedules() -> None:
    rendered = build_skills.build_all()
    briefing = next(p for p in rendered if p.parent.name == "morning-briefing")
    content = rendered[briefing]
    assert "blueprint:" in content
    assert "schedule:" in content
    assert "deliver: origin" in content


def test_idea_spotlight_self_schedules() -> None:
    rendered = build_skills.build_all()
    spotlight = next(p for p in rendered if p.parent.name == "idea-spotlight")
    content = rendered[spotlight]
    assert "blueprint:" in content and "schedule:" in content


def test_nested_fences_do_not_truncate_prompt() -> None:
    """An indented nested fence in a prompt body must not close the outer fence.

    Guards the skill-author truncation bug: its STEP 3 shows an example skill
    (with its own ``## Prompt`` ``` fences), which used to cut extraction short.
    """
    sample = [
        "# Skill: `superbot-x`",
        "**Purpose:** test.",
        "## Prompt",
        "```",
        "do a thing",
        "      ```",  # indented nested example fence — must NOT close the outer one
        "      nested example body",
        "      ```",
        "do another thing after the nested block",
        "```",
        "## Notes",
    ]
    body = build_skills._extract_prompt(sample)
    assert "do a thing" in body
    assert "nested example body" in body
    assert "do another thing after the nested block" in body  # survived the nested fence


def test_skill_author_keeps_all_steps() -> None:
    """skill-author's generated prompt must include its later steps (regression)."""
    rendered = build_skills.build_all()
    author = next(p for p in rendered if p.parent.name == "skill-author")
    content = rendered[author]
    assert "STEP 4" in content and "STEP 5" in content


def test_committed_artifacts_are_fresh() -> None:
    """Committed SKILL.md files must match a fresh build (run the builder)."""
    rc = build_skills.main(["--check"])
    assert rc == 0, (
        "Generated Hermes skills are stale. "
        "Run: python3.10 scripts/hermes/build_skills.py"
    )
