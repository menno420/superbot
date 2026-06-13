"""Tests for the generic, config-driven hygiene checkers (the 1b tail port).

Covers the doc checker (badge / link / reachable) and the session-log marker
checker, plus a render->check integration that proves the kit's own rendered
templates pass its own ``check_docs`` (the plan's verification goal d).
"""

from pathlib import Path

from engine.checks.check_docs import (
    Finding,
    check_badges,
    check_links,
    check_reachable,
    run_doc_checks,
)
from engine.checks.check_session_log import (
    check_log,
    latest_session_log,
    missing_markers,
)
from engine.interview.question_bank import QUESTIONS
from engine.lib.config import Config
from engine.render import build_context, find_placeholders, load_templates, render

_TOKENS = Config().badge_tokens
_READPATH = Config().readpath_docs
_MARKERS = Config().session_markers


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------


def test_badge_valid_passes(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "ok.md", "# Title\n\n> **Status:** `binding`\n\nbody\n")
    assert check_badges(docs, _TOKENS) == []


def test_badge_missing_flagged(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "bare.md", "# Title\n\nbody only, no badge\n")
    viol = check_badges(docs, _TOKENS)
    assert len(viol) == 1
    assert viol[0].kind == "badge" and "missing" in viol[0].message


def test_badge_invalid_token_flagged(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "weird.md", "# Title\n\n> **Status:** `bogus`\n")
    viol = check_badges(docs, _TOKENS)
    assert len(viol) == 1 and "invalid badge token" in viol[0].message


def test_badge_custom_taxonomy_respected(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "x.md", "# X\n\n> **Status:** `bespoke`\n")
    assert check_badges(docs, ["bespoke"]) == []
    assert len(check_badges(docs, ["binding"])) == 1


def test_adr_is_exempt_from_badge(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "decisions" / "001-no-redis.md", "# ADR-001\n\n**Status:** Accepted\n")
    assert check_badges(docs, _TOKENS) == []


def test_badges_empty_when_docs_root_absent(tmp_path):
    assert check_badges(tmp_path / "nope", _TOKENS) == []


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------


def test_links_dead_flagged_valid_and_external_ok(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "target.md", "# Target\n\n> **Status:** `reference`\n")
    _write(
        docs / "a.md",
        "# A\n\n> **Status:** `reference`\n\n"
        "[good](target.md) [dead](nope.md) "
        "[ext](https://example.com) [anchor](#x)\n",
    )
    viol = check_links(docs)
    assert len(viol) == 1
    assert viol[0].kind == "link" and "nope.md" in viol[0].message


# ---------------------------------------------------------------------------
# Reachability
# ---------------------------------------------------------------------------


def test_reachable_orphan_flagged_linked_ok(tmp_path):
    docs = tmp_path / "docs"
    # AGENT_ORIENTATION is a read-path root; it links good.md (markdown) and
    # sub.md (backtick `docs/...` ref). orphan.md is linked from nowhere.
    _write(
        docs / "AGENT_ORIENTATION.md",
        "# O\n\n> **Status:** `reference`\n\n[good](good.md) and `docs/sub.md`\n",
    )
    _write(docs / "good.md", "# Good\n\n> **Status:** `reference`\n")
    _write(docs / "sub.md", "# Sub\n\n> **Status:** `reference`\n")
    _write(docs / "orphan.md", "# Orphan\n\n> **Status:** `reference`\n")
    viol = check_reachable(docs, _READPATH)
    assert [v.path for v in viol] == ["orphan.md"]
    assert viol[0].kind == "reachable"


def test_reachable_exempt_badges_and_adr_ok(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "AGENT_ORIENTATION.md", "# O\n\n> **Status:** `reference`\n")
    # Retired badges need no inbound link; ADRs are exempt.
    _write(docs / "old.md", "# Old\n\n> **Status:** `historical`\n")
    _write(docs / "gone.md", "# Gone\n\n> **Status:** `archive`\n")
    _write(docs / "decisions" / "009-x.md", "# ADR\n\n**Status:** Accepted\n")
    assert check_reachable(docs, _READPATH) == []


def test_reachable_readme_is_a_root(tmp_path):
    docs = tmp_path / "docs"
    # No read-path docs exist, but a README links the doc -> reachable.
    _write(docs / "sub" / "README.md", "# R\n\n> **Status:** `reference`\n\n[x](child.md)\n")
    _write(docs / "sub" / "child.md", "# C\n\n> **Status:** `reference`\n")
    assert check_reachable(docs, _READPATH) == []


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


def test_run_doc_checks_combines_kinds(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "AGENT_ORIENTATION.md", "# O\n\n> **Status:** `reference`\n")
    _write(docs / "nobadge.md", "# N\n\nno badge, also an orphan\n")
    kinds = {f.kind for f in run_doc_checks(docs, _TOKENS, _READPATH)}
    assert kinds == {"badge", "reachable"}


def test_clean_tree_has_no_findings(tmp_path):
    docs = tmp_path / "docs"
    _write(
        docs / "AGENT_ORIENTATION.md",
        "# O\n\n> **Status:** `reference`\n\n[cs](current-state.md)\n",
    )
    _write(docs / "current-state.md", "# CS\n\n> **Status:** `living-ledger`\n")
    assert run_doc_checks(docs, _TOKENS, _READPATH) == []


# ---------------------------------------------------------------------------
# Session log
# ---------------------------------------------------------------------------


def test_missing_markers_complete_vs_incomplete():
    full = "> **Status:** `reference`\n\n💡 idea\n\nprevious-session review: ok\n"
    assert missing_markers(full, _MARKERS) == []
    bare = "nothing here\n"
    assert missing_markers(bare, _MARKERS) == [m["label"] for m in _MARKERS]


def test_missing_markers_custom_set():
    markers = [{"label": "Sign-off", "needle": "signed-off-by"}]
    assert missing_markers("Signed-off-by: me", markers) == []
    assert missing_markers("no trailer", markers) == ["Sign-off"]


def test_latest_session_log_picks_newest_skips_readme(tmp_path):
    sessions = tmp_path / ".sessions"
    sessions.mkdir()
    _write(sessions / "README.md", "convention doc\n")
    old = sessions / "2026-06-01-a.md"
    new = sessions / "2026-06-02-b.md"
    _write(old, "old\n")
    _write(new, "new\n")
    import os

    os.utime(old, (1000, 1000))
    os.utime(new, (2000, 2000))
    assert latest_session_log(sessions) == new


def test_latest_session_log_none_when_absent_or_empty(tmp_path):
    assert latest_session_log(tmp_path / "nope") is None
    empty = tmp_path / ".sessions"
    empty.mkdir()
    assert latest_session_log(empty) is None


def test_check_log_unreadable_returns_all_labels(tmp_path):
    missing = check_log(tmp_path / "does-not-exist.md", _MARKERS)
    assert missing == [m["label"] for m in _MARKERS]


# ---------------------------------------------------------------------------
# Integration — the kit's own rendered templates pass its own check_docs
# ---------------------------------------------------------------------------


def test_rendered_templates_are_badge_and_link_clean(tmp_path):
    """Verification goal (d): generated docs pass the engine's own check_docs.

    Render every template with a fully-filled context into a flat docs tree and
    assert zero badge + link findings. (Reachability is host-layout dependent —
    a host files CLAUDE.md under .claude/, the journal at the root — so it is
    exercised by the synthetic-tree tests above, not this flat render.)
    """
    docs = tmp_path / "docs"
    context = {q["slot"]: f"v-{q['slot']}" for q in QUESTIONS}
    for name, text in load_templates().items():
        rendered = render(text, context)
        assert find_placeholders(rendered) == set(), f"{name} left placeholders"
        out_name = name[:-5] if name.endswith(".tmpl") else name
        _write(docs / out_name, rendered)
    assert check_badges(docs, _TOKENS) == []
    assert check_links(docs) == []


def test_finding_is_a_named_triple():
    f = Finding("p.md", "badge", "msg")
    assert (f.path, f.kind, f.message) == ("p.md", "badge", "msg")
