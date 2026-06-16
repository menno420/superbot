"""Tests for ``scripts/hermes/idea_spotlight.py``.

Guards the deterministic idea-of-the-day selector: active/terminal filtering, a
stable per-day pick that rotates through the whole backlog, and the parse/render
shapes the ``superbot-idea-spotlight`` skill reasons over.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = REPO_ROOT / "scripts" / "hermes" / "idea_spotlight.py"

_spec = importlib.util.spec_from_file_location("idea_spotlight", _SCRIPT)
assert _spec and _spec.loader
spotlight = importlib.util.module_from_spec(_spec)
# Register before exec so @dataclass can resolve the module via sys.modules
# (mirrors tests/unit/scripts/test_build_skills.py).
sys.modules["idea_spotlight"] = spotlight
_spec.loader.exec_module(spotlight)


def _write_backlog(tmp_path: Path) -> Path:
    ideas = tmp_path / "ideas"
    ideas.mkdir()
    (ideas / "active1.md").write_text(
        "# Idea: alpha\n\n"
        "> **Status:** `ideas` — captured 2026-06-16.\n\n"
        "## The idea\n\n"
        "This is the alpha idea body explaining what it does.\n\n"
        "→ relates `services/foo.py`\n",
        encoding="utf-8",
    )
    (ideas / "active2.md").write_text(
        "# Beta idea\n\n> **Status:** `raw`\n\nBeta body paragraph.\n",
        encoding="utf-8",
    )
    (ideas / "active3.md").write_text(
        "# Gamma idea\n\nNo status badge here — still an active capture.\n",
        encoding="utf-8",
    )
    (ideas / "done1.md").write_text(
        "# Old shipped idea\n\n> **Status:** `historical` — EXECUTED (#123).\n\nbody\n",
        encoding="utf-8",
    )
    (ideas / "done2.md").write_text(
        "# Bad idea\n\n> **Status:** `rejected`\n\nbody\n", encoding="utf-8"
    )
    # README must be excluded from the backlog.
    (ideas / "README.md").write_text("# Index\n\n- [a](./active1.md)\n", encoding="utf-8")
    return ideas


def test_parse_extracts_title_status_summary_relates(tmp_path: Path) -> None:
    ideas = _write_backlog(tmp_path)
    idea = spotlight.parse_idea(ideas / "active1.md")
    assert idea.title == "Idea: alpha"
    assert idea.status == "ideas"
    assert idea.summary == "This is the alpha idea body explaining what it does."
    assert "relates" in idea.relates and "services/foo.py" in idea.relates
    assert idea.is_active is True


def test_active_filter_drops_terminal_badges(tmp_path: Path) -> None:
    ideas = spotlight.load_ideas(_write_backlog(tmp_path))
    active = spotlight.active_ideas(ideas)
    titles = {i.title for i in active}
    assert titles == {"Idea: alpha", "Beta idea", "Gamma idea"}
    # README, historical and rejected are excluded.
    assert "Old shipped idea" not in titles
    assert "Bad idea" not in titles


def test_no_status_badge_counts_as_active(tmp_path: Path) -> None:
    ideas = spotlight.load_ideas(_write_backlog(tmp_path))
    gamma = next(i for i in ideas if i.title == "Gamma idea")
    assert gamma.status == ""
    assert gamma.is_active is True


def test_select_is_deterministic_per_day(tmp_path: Path) -> None:
    ideas = spotlight.load_ideas(_write_backlog(tmp_path))
    day = dt.date(2026, 6, 16)
    first = spotlight.select(ideas, day)
    second = spotlight.select(ideas, day)
    assert first == second
    idx, idea = first
    assert idea is not None and 0 <= idx < 3


def test_select_rotates_through_whole_backlog(tmp_path: Path) -> None:
    ideas = spotlight.load_ideas(_write_backlog(tmp_path))
    base = dt.date(2026, 6, 16)
    picked = {
        spotlight.select(ideas, base + dt.timedelta(days=d))[1].title  # type: ignore[union-attr]
        for d in range(3)
    }
    # Three active ideas → three consecutive days cover all of them.
    assert picked == {"Idea: alpha", "Beta idea", "Gamma idea"}


def test_select_empty_backlog(tmp_path: Path) -> None:
    empty = tmp_path / "ideas"
    empty.mkdir()
    idx, idea = spotlight.select(spotlight.load_ideas(empty), dt.date(2026, 6, 16))
    assert idx == -1 and idea is None


def test_to_dict_and_markdown_shapes(tmp_path: Path) -> None:
    ideas = spotlight.load_ideas(_write_backlog(tmp_path))
    day = dt.date(2026, 6, 16)
    idx, idea = spotlight.select(ideas, day)
    payload = spotlight.to_dict(idea, idx, len(spotlight.active_ideas(ideas)), day)
    assert payload["date"] == "2026-06-16"
    assert payload["total_active"] == 3
    assert payload["idea"]["title"] == idea.title  # type: ignore[union-attr]

    md = spotlight.render_markdown(idea, idx, 3, day)
    assert "💡 Idea spotlight — 2026-06-16" in md
    assert idea.title in md  # type: ignore[union-attr]


def test_markdown_empty_backlog_is_friendly() -> None:
    md = spotlight.render_markdown(None, -1, 0, dt.date(2026, 6, 16))
    assert "No active ideas" in md


def test_repo_backlog_builds_a_real_pick() -> None:
    """Smoke test against the live docs/ideas backlog (not a fixture)."""
    ideas = spotlight.load_ideas(spotlight.IDEAS_DIR)
    assert ideas, "expected real idea files"
    idx, idea = spotlight.select(ideas, dt.date(2026, 6, 16))
    # The live backlog always has at least one active idea.
    assert idea is not None and idea.is_active
