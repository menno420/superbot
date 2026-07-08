"""Tests for scripts/check_supersede_integrity.py — the supersede-banner handshake guard.

Warn-first checker (Q-0105 posture: verify against ground truth before trusting).
These fixtures pin each drift class the checker exists to catch — phantom successor,
one-sided handshake, dead plan badge, unstamped disposition row — plus the scoping
rules that keep it low-FP (header-block only; -IN-PART keeps its ``plan`` badge;
prose "supersedes" doesn't mark a doc).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "scripts" / "check_supersede_integrity.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_supersede_integrity_ut", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load()


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    """Write a fake repo tree: keys are repo-relative paths under ``docs/``."""
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def _check(mod, tmp_path: Path) -> list[str]:
    return mod.check(docs_root=tmp_path / "docs", repo_root=tmp_path)


# --- the happy path ---------------------------------------------------------


def test_intact_handshake_is_clean(mod, tmp_path):
    root = _tree(
        tmp_path,
        {
            "docs/planning/old-plan.md": (
                "# Old plan\n\n"
                "> **⚠ SUPERSEDED (2026-07-06):** absorbed into\n"
                "> [`new-plan.md`](new-plan.md) §3.\n\n"
                "> **Status:** `historical` — kept for provenance.\n\n"
                "## Body\n"
            ),
            "docs/planning/new-plan.md": (
                "# New plan\n\n> **Status:** `plan`\n\n"
                "Replaces [`old-plan.md`](old-plan.md).\n"
            ),
        },
    )
    assert _check(mod, root) == []


def test_plain_text_path_counts_for_handshake(mod, tmp_path):
    # The ui-view-adoption-audit class: successor named as a bare path, not a link.
    root = _tree(
        tmp_path,
        {
            "docs/audits/old-audit.md": (
                "# Old audit\n\n"
                "> **Status:** `historical` — ⚠️ SUPERSEDED snapshot;\n"
                "> `docs/audits/new-audit.md` supersedes its open backlog.\n\n"
                "## Body\n"
            ),
            "docs/audits/new-audit.md": (
                "# New audit\n\nReconciles `old-audit.md` against current code.\n"
            ),
        },
    )
    assert _check(mod, root) == []


# --- drift class 1: phantom successor ---------------------------------------


def test_phantom_successor_link_is_flagged(mod, tmp_path):
    root = _tree(
        tmp_path,
        {
            "docs/planning/old-plan.md": (
                "# Old plan\n\n"
                "> **⚠ SUPERSEDED:** see [`gone.md`](gone.md).\n\n"
                "> **Status:** `historical`\n\n## Body\n"
            ),
        },
    )
    findings = _check(mod, root)
    assert len(findings) == 1
    assert "phantom successor" in findings[0]
    assert "gone.md" in findings[0]


def test_banner_naming_no_successor_is_flagged(mod, tmp_path):
    root = _tree(
        tmp_path,
        {
            "docs/planning/old-plan.md": (
                "# Old plan\n\n"
                "> **⚠ SUPERSEDED (2026-07-06):** do not act from this doc.\n\n"
                "> **Status:** `historical`\n\n## Body\n"
            ),
        },
    )
    findings = _check(mod, root)
    assert len(findings) == 1
    assert "names no successor" in findings[0]


# --- drift class 2: one-sided handshake --------------------------------------


def test_missing_backlink_is_flagged(mod, tmp_path):
    root = _tree(
        tmp_path,
        {
            "docs/planning/old-plan.md": (
                "# Old plan\n\n"
                "> **⚠ SUPERSEDED:** absorbed into [`new-plan.md`](new-plan.md).\n\n"
                "> **Status:** `historical`\n\n## Body\n"
            ),
            "docs/planning/new-plan.md": "# New plan\n\nNo mention of its predecessor.\n",
        },
    )
    findings = _check(mod, root)
    assert len(findings) == 1
    assert "one-sided handshake" in findings[0]
    assert "old-plan" in findings[0]


# --- drift class 3: dead plan badge ------------------------------------------


def test_full_supersede_with_plan_badge_is_flagged(mod, tmp_path):
    root = _tree(
        tmp_path,
        {
            "docs/planning/old-plan.md": (
                "# Old plan\n\n"
                "> **Status:** `plan` · **⚠ SUPERSEDED:** see\n"
                "> [`new-plan.md`](new-plan.md).\n\n## Body\n"
            ),
            "docs/planning/new-plan.md": "# New plan\n\nReplaces `old-plan.md`.\n",
        },
    )
    findings = _check(mod, root)
    assert len(findings) == 1
    assert "still badged `plan`" in findings[0]


def test_in_part_supersede_may_keep_plan_badge(mod, tmp_path):
    # The rebuild-design-spec class: partially superseded, plan badge stays live.
    root = _tree(
        tmp_path,
        {
            "docs/planning/spec.md": (
                "# Spec\n\n"
                "> **Status:** `plan` · **⚠ SUPERSEDED-IN-PART:** §9 superseded by\n"
                "> [`new-plan.md`](new-plan.md); the rest stays live.\n\n## Body\n"
            ),
            "docs/planning/new-plan.md": "# New plan\n\nAmends `spec.md` §9.\n",
        },
    )
    assert _check(mod, root) == []


# --- scoping rules ------------------------------------------------------------


def test_mid_doc_marker_is_out_of_scope(mod, tmp_path):
    # Section-level supersedes (the docs/btd6/ class) must not mark the whole doc.
    root = _tree(
        tmp_path,
        {
            "docs/btd6/status.md": (
                "# Status\n\n> **Status:** `living-ledger`\n\n"
                "## Old section\n\n"
                "> **⛔ SUPERSEDED 2026-06-10** — this list's end-goal moved.\n"
            ),
        },
    )
    assert _check(mod, root) == []


def test_lowercase_supersedes_prose_does_not_mark_doc(mod, tmp_path):
    # A doc describing what *it* replaces is not itself superseded.
    root = _tree(
        tmp_path,
        {
            "docs/audits/new-audit.md": (
                "# New audit\n\n"
                "> **Status:** `living-ledger` — supersedes the open backlogs in\n"
                "> older snapshots.\n\n## Body\n"
            ),
        },
    )
    assert _check(mod, root) == []


# --- reverse pass: disposition tables ----------------------------------------


def test_disposition_row_without_banner_is_flagged(mod, tmp_path):
    root = _tree(
        tmp_path,
        {
            "docs/planning/new-plan.md": (
                "# New plan\n\n> **Status:** `plan`\n\n"
                "## 9. Superseded / disposition of the scattered docs\n\n"
                "| Doc | Disposition |\n|---|---|\n"
                "| [`old-plan.md`](old-plan.md) | **Superseded by this plan** |\n"
                "| [`kept.md`](kept.md) | stays reference |\n"
            ),
            "docs/planning/old-plan.md": (
                "# Old plan\n\n> **Status:** `historical` — no banner here.\n\n## Body\n"
            ),
            "docs/planning/kept.md": "# Kept\n\nStill live, no banner needed.\n",
        },
    )
    findings = _check(mod, root)
    assert len(findings) == 1
    assert "has no SUPERSEDED banner" in findings[0]
    assert "old-plan.md" in findings[0]


def test_disposition_row_with_banner_is_clean(mod, tmp_path):
    root = _tree(
        tmp_path,
        {
            "docs/planning/new-plan.md": (
                "# New plan\n\n> **Status:** `plan`\n\n"
                "## Superseded docs\n\n"
                "| Doc | Disposition |\n|---|---|\n"
                "| [`old-plan.md`](old-plan.md) | **Superseded** |\n"
            ),
            "docs/planning/old-plan.md": (
                "# Old plan\n\n"
                "> **⚠ SUPERSEDED:** see [`new-plan.md`](new-plan.md).\n\n"
                "> **Status:** `historical`\n\n## Body\n"
            ),
        },
    )
    assert _check(mod, root) == []


def test_disposition_row_with_dead_link_is_flagged(mod, tmp_path):
    root = _tree(
        tmp_path,
        {
            "docs/planning/new-plan.md": (
                "# New plan\n\n> **Status:** `plan`\n\n"
                "## Superseded docs\n\n"
                "| Doc | Disposition |\n|---|---|\n"
                "| [`vanished.md`](vanished.md) | **Superseded** |\n"
            ),
        },
    )
    findings = _check(mod, root)
    assert len(findings) == 1
    assert "does not resolve" in findings[0]


def test_rows_outside_supersede_headings_are_skipped(mod, tmp_path):
    # A "Retirement map" table (the strand-1 K1 class) is not a disposition table.
    root = _tree(
        tmp_path,
        {
            "docs/planning/design.md": (
                "# Design\n\n> **Status:** `plan`\n\n"
                "## Retirement map\n\n"
                "| Item | How |\n|---|---|\n"
                "| [`gone.md`](gone.md) | **SUPERSEDED** — generalized |\n"
            ),
        },
    )
    assert _check(mod, root) == []


# --- check_docs soft-check wiring ---------------------------------------------


def test_check_docs_soft_report_never_raises(capsys):
    # The delegation seam in check_docs.py must stay failure-tolerant and quiet
    # on a clean tree (it prints only when there are findings, or a skip notice).
    spec = importlib.util.spec_from_file_location(
        "check_docs_ut_supersede", _REPO / "scripts" / "check_docs.py"
    )
    assert spec and spec.loader
    check_docs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check_docs)
    check_docs.print_supersede_integrity_report()  # must not raise
    out = capsys.readouterr().out
    assert "skipped" not in out  # the sibling script is present and loadable


# --- the real tree ------------------------------------------------------------


def test_real_docs_tree_runs_and_returns_list(mod):
    # Smoke only, deliberately non-blocking on findings: the checker is warn-first
    # (Q-0105 — unverified guards don't get to block merges). Ground truth at
    # implementation time (2026-07-08): 6 header-banner docs, 5 disposition rows,
    # zero findings. Once proven over a few sessions, promote by asserting
    # ``findings == []`` here (that IS the strict gate) — or delete the checker
    # per its header if it proved noisy.
    findings = mod.check()
    assert isinstance(findings, list)
    if findings:  # visible in -v / CI logs without failing the suite
        print("supersede-integrity findings (warn-only):\n" + "\n".join(findings))
