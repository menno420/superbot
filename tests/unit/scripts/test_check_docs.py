"""Tests for ``scripts/check_docs.py`` (doc-hygiene checker)."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_docs.py"


@pytest.fixture(scope="module")
def cd():
    spec = importlib.util.spec_from_file_location("check_docs_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------


def test_badge_valid_passes(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "ok.md", "# Title\n\n> **Status:** `binding`\n\nbody\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    assert cd.check_badges() == []


def test_badge_missing_flagged(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "bare.md", "# Title\n\nbody only, no badge\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    viol = cd.check_badges()
    assert len(viol) == 1
    assert viol[0][1] == "badge" and "missing" in viol[0][2]


def test_badge_invalid_token_flagged(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "weird.md", "# Title\n\n> **Status:** `bogus`\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    viol = cd.check_badges()
    assert len(viol) == 1 and "invalid badge token" in viol[0][2]


def test_adr_is_exempt_from_badge(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "decisions" / "001-no-redis.md", "# ADR-001\n\n**Status:** Accepted\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    assert cd.check_badges() == []


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------


def test_links_dead_flagged_valid_and_external_ok(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "target.md", "# Target\n\n> **Status:** `reference`\n")
    _write(
        docs / "a.md",
        "# A\n\n> **Status:** `reference`\n\n"
        "[good](target.md) [dead](nope.md) "
        "[ext](https://example.com) [anchor](#x)\n",
    )
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    viol = cd.check_links()
    assert len(viol) == 1
    assert "nope.md" in viol[0][2]


# ---------------------------------------------------------------------------
# Pinned read-path references
# ---------------------------------------------------------------------------


def test_pinned_missing_path_flagged_placeholder_skipped(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "real.md", "x")
    _write(
        docs / "AGENT_ORIENTATION.md",
        "# Orientation\n\n> **Status:** `binding`\n\n"
        "real: `docs/real.md` · ghost: `docs/ghost.md` · "
        "placeholder: `docs/subsystems/<area>.md`\n",
    )
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    viol = cd.check_pinned()
    assert len(viol) == 1
    assert "docs/ghost.md" in viol[0][2]


# ---------------------------------------------------------------------------
# Taxonomy pin — the checker must match AGENT_ORIENTATION's badge list
# ---------------------------------------------------------------------------


def test_allowed_badges_match_agent_orientation(cd):
    text = (_REPO_ROOT / "docs" / "AGENT_ORIENTATION.md").read_text(encoding="utf-8")
    # Badge bullets look like:  - **`binding`** — ...
    documented = set(re.findall(r"^- \*\*`([a-z-]+)`\*\*", text, re.MULTILINE))
    assert documented == set(cd.ALLOWED_BADGES), (
        "ALLOWED_BADGES in check_docs.py drifted from the badge list in "
        "docs/AGENT_ORIENTATION.md"
    )
