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
    _write(
        docs / "decisions" / "001-no-redis.md", "# ADR-001\n\n**Status:** Accepted\n"
    )
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


# ---------------------------------------------------------------------------
# Reachability — every live doc must be reachable from a read-path root
# ---------------------------------------------------------------------------


def test_reachable_orphan_flagged_linked_ok(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    # AGENT_ORIENTATION is a read-path root; it links good.md (markdown) and
    # sub.md (backtick path). orphan.md is linked from nowhere.
    _write(
        docs / "AGENT_ORIENTATION.md",
        "# Orientation\n\n> **Status:** `binding`\n\n"
        "[good](good.md) and `docs/sub.md`\n",
    )
    _write(docs / "good.md", "# Good\n\n> **Status:** `reference`\n")
    _write(docs / "sub.md", "# Sub\n\n> **Status:** `reference`\n")
    _write(docs / "orphan.md", "# Orphan\n\n> **Status:** `reference`\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    viol = cd.check_reachable()
    assert [str(v[0]) for v in viol] == ["docs/orphan.md"]
    assert viol[0][1] == "reachable"


def test_reachable_exempt_badges_and_allowlist(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "AGENT_ORIENTATION.md", "# O\n\n> **Status:** `binding`\n")
    # Retired badges need no inbound link; ADRs are exempt; allowlist covers islands.
    _write(docs / "old.md", "# Old\n\n> **Status:** `historical`\n")
    _write(docs / "gone.md", "# Gone\n\n> **Status:** `archive`\n")
    _write(docs / "decisions" / "009-x.md", "# ADR\n\n**Status:** Accepted\n")
    _write(docs / "island.md", "# Island\n\n> **Status:** `reference`\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cd, "_REACHABILITY_ALLOWLIST", frozenset({"docs/island.md"}))
    assert cd.check_reachable() == []


def test_repo_has_no_doc_orphans(cd):
    """Pin the real tree to zero orphans (mirrors the --strict CI gate)."""
    orphans = cd.check_reachable()
    assert orphans == [], "orphaned docs: " + ", ".join(str(v[0]) for v in orphans)


# ---------------------------------------------------------------------------
# Freshness — current-state.md must not name the in-flight PR in prose
# ---------------------------------------------------------------------------


def test_freshness_flags_pending_markers(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(
        docs / "current-state.md",
        "# State\n\n> **Status:** `living-ledger`\n\n"
        "- **#100** merged — fine.\n"
        "- **PR10 fifth slice** (this PR, pending) — rots on merge.\n"
        "- old note (pending PR) — also rots.\n",
    )
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    viol = cd.check_freshness()
    assert len(viol) == 2
    assert all(v[1] == "freshness" for v in viol)


def test_freshness_passes_on_merged_only(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(
        docs / "current-state.md",
        "# State\n\n> **Status:** `living-ledger`\n\n"
        "> **▶ Next action:** finish X.\n\n"
        "- **#100** merged — this PR adds Y (no rotting marker).\n",
    )
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    assert cd.check_freshness() == []


def test_repo_current_state_has_no_stale_pending(cd):
    """Pin the real current-state.md to zero in-flight-PR-in-prose markers."""
    stale = cd.check_freshness()
    assert stale == [], "stale pending markers: " + "; ".join(
        f"{v[0]}: {v[2]}" for v in stale
    )


# ---------------------------------------------------------------------------
# Census (badge counts + top-level ratchet)
# ---------------------------------------------------------------------------


def test_census_counts_total_top_level_and_badges(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "a.md", "# A\n\n> **Status:** `binding`\n")
    _write(docs / "b.md", "# B\n\n> **Status:** `binding`\n")
    _write(docs / "c.md", "# C\n\n> **Status:** `plan`\n")
    _write(docs / "subsystems" / "s.md", "# S\n\n> **Status:** `living-ledger`\n")
    _write(docs / "decisions" / "001-x.md", "# ADR\n\nbody\n")  # ADR — no badge
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)

    total, top_level, by_badge = cd.census()
    assert total == 5
    assert top_level == 3  # a, b, c (subdir + ADR don't count toward top-level)
    assert by_badge["binding"] == 2
    assert by_badge["plan"] == 1
    assert by_badge["living-ledger"] == 1
    assert by_badge["decision (ADR)"] == 1


def test_census_flags_unbadged(cd, tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    _write(docs / "bare.md", "# Bare\n\nno badge here\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    _, _, by_badge = cd.census()
    assert by_badge["(unbadged)"] == 1


def test_print_census_warns_over_ratchet(cd, tmp_path, monkeypatch, capsys):
    docs = tmp_path / "docs"
    for i in range(3):
        _write(docs / f"d{i}.md", "# D\n\n> **Status:** `plan`\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cd, "_TOP_LEVEL_DOCS_BUDGET", 2)  # 3 top-level > budget 2
    cd.print_census()
    out = capsys.readouterr().out
    assert "census" in out
    assert "⚠" in out and "ratchet" in out


def test_print_census_silent_when_within_ratchet(cd, tmp_path, monkeypatch, capsys):
    docs = tmp_path / "docs"
    _write(docs / "only.md", "# Only\n\n> **Status:** `binding`\n")
    monkeypatch.setattr(cd, "DOCS_ROOT", docs)
    monkeypatch.setattr(cd, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cd, "_TOP_LEVEL_DOCS_BUDGET", 41)
    cd.print_census()
    out = capsys.readouterr().out
    assert "census" in out
    assert "⚠" not in out  # within ratchet → no warning


def test_repo_top_level_docs_within_ratchet(cd):
    """The real repo's top-level pile must not silently grow past the ratchet."""
    _, top_level, _ = cd.census()
    assert top_level <= cd._TOP_LEVEL_DOCS_BUDGET, (
        f"top-level docs/*.md = {top_level} > ratchet {cd._TOP_LEVEL_DOCS_BUDGET}; "
        "move plans/audits/historical into a subdir or lower the ratchet."
    )
