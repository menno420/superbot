"""Tests for scripts/check_lane_overlap.py — the active-work.md claim-ledger scan.

The claim scan closes the gap that let a duplicate reaction-roles PR 2 get built:
the merged-commit scan structurally cannot see a claim that exists *before* any PR
or commit. These cover the pure parse + overlap logic (no git, no real file).
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_lane_overlap",
    Path(__file__).resolve().parents[3] / "scripts" / "check_lane_overlap.py",
)
assert _SPEC and _SPEC.loader
clo = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(clo)


_LEDGER = """# Active work

## Active claims

- `claude/reaction-roles-pr1-foundation` · **Reaction-roles overhaul PR 1 — audited seam**
  (owner-directed) · `services/reaction_role_service.py` + `utils/db/role_menus.py` +
  migration `078_reaction_role_menus.sql` · 2026-06-21 · **auto-merge on green**.
  **Parallel session owns PR 2-5; do not recreate these.**

- `claude/design-system-site-pages` · **design-system: compose the rest of the site** ·
  `design-system/src/` (`PageHeader`/`SearchBar`) · 2026-06-20 · **auto-merge on green**

## Recently cleared

- `claude/old-branch` · something · `scripts/gone.py` · **PR #1 (merged)**
"""


def test_parse_claims_extracts_branch_paths_and_summary():
    claims = clo.parse_claims(_LEDGER)
    assert len(claims) == 2  # the "Recently cleared" entry is excluded
    first = claims[0]
    assert first["branch"] == "claude/reaction-roles-pr1-foundation"
    assert "Reaction-roles overhaul PR 1" in first["summary"]
    # Branch + non-path backtick tokens are excluded; real paths are kept.
    assert "services/reaction_role_service.py" in first["paths"]
    assert "utils/db/role_menus.py" in first["paths"]
    assert "078_reaction_role_menus.sql" in first["paths"]
    assert "claude/reaction-roles-pr1-foundation" not in first["paths"]


def test_component_names_are_not_treated_as_paths():
    claims = clo.parse_claims(_LEDGER)
    design = claims[1]
    assert "design-system/src/" in design["paths"]
    # Bare component names (no slash, no extension) are not paths.
    assert "PageHeader" not in design["paths"]
    assert "SearchBar" not in design["paths"]


def test_scan_claims_flags_overlapping_scope_ignoring_disbot_prefix():
    claims = clo.parse_claims(_LEDGER)
    # Scope uses the disbot/ prefix; the claim omits it — they must still match.
    hits = clo.scan_claims(["disbot/services/reaction_role_service.py"], claims)
    assert "disbot/services/reaction_role_service.py" in hits
    matched = hits["disbot/services/reaction_role_service.py"]
    assert matched[0]["branch"] == "claude/reaction-roles-pr1-foundation"


def test_scan_claims_dir_scope_nests_a_claimed_file():
    claims = clo.parse_claims(_LEDGER)
    hits = clo.scan_claims(["disbot/services/"], claims)
    assert "disbot/services/" in hits


def test_scan_claims_no_overlap_is_empty():
    claims = clo.parse_claims(_LEDGER)
    assert clo.scan_claims(["disbot/cogs/mining_cog.py"], claims) == {}


def test_paths_overlap_directionality():
    assert clo._paths_overlap("services/x.py", "disbot/services/x.py")
    assert clo._paths_overlap("disbot/services/", "services/x.py")
    assert clo._paths_overlap("services/x.py", "services/")
    assert not clo._paths_overlap("services/x.py", "services/y.py")
    assert not clo._paths_overlap("", "services/")


def test_recently_cleared_entries_are_not_claims():
    # A path under a "Recently cleared" line must not produce a claim hit.
    claims = clo.parse_claims(_LEDGER)
    assert clo.scan_claims(["scripts/gone.py"], claims) == {}


def test_parse_claims_handles_missing_section():
    assert clo.parse_claims("# Doc\n\nno claims section here\n") == []


# --- per-claim file layout (Q-0195) ---------------------------------------

_CLAIM_FILE = """- `claude/relaxed-euler-w4lrkh` · **state-file restructure** (owner-directed) —
  per-claim active-work · `scripts/check_lane_overlap.py` `docs/current-state/` · 2026-06-22 · PR
"""


def test_parse_claim_file_reads_a_single_bullet_without_a_header():
    claims = clo.parse_claim_file(_CLAIM_FILE)
    assert len(claims) == 1
    assert claims[0]["branch"] == "claude/relaxed-euler-w4lrkh"
    assert "state-file restructure" in claims[0]["summary"]
    assert "scripts/check_lane_overlap.py" in claims[0]["paths"]
    assert "docs/current-state/" in claims[0]["paths"]


def test_parse_claim_file_ignores_heading_and_prose_lines():
    text = "# heading\n\nsome prose\n\n" + _CLAIM_FILE
    assert len(clo.parse_claim_file(text)) == 1


def test_parse_claim_file_empty_is_no_claims():
    assert clo.parse_claim_file("# README\n\nno bullets here\n") == []


def test_load_claims_reads_directory_and_skips_readme(tmp_path, monkeypatch):
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir()
    (claims_dir / "README.md").write_text("- `claude/not-a-claim` · README example\n")
    (claims_dir / "claude__a.md").write_text(
        "- `claude/a` · **lane A** · `scripts/a.py` · 2026-06-22 · PR\n",
    )
    (claims_dir / "claude__b.md").write_text(
        "- `claude/b` · **lane B** · `disbot/services/b.py` · 2026-06-22 · PR\n",
    )
    monkeypatch.setattr(clo, "_CLAIMS_DIR", claims_dir)
    claims = clo._load_claims()
    branches = {c["branch"] for c in claims}
    assert branches == {"claude/a", "claude/b"}  # README excluded


def test_load_claims_missing_directory_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(clo, "_CLAIMS_DIR", tmp_path / "nope")
    assert clo._load_claims() == []


# --- remote-branch claim scan (--remote, 2026-07-10) ------------------------

_NOW = 1_800_000_000


def _freeze_now(monkeypatch):
    monkeypatch.setattr(
        clo,
        "time",
        type("_T", (), {"time": staticmethod(lambda: _NOW)}),
    )


def test_parse_ref_lines_filters_by_cutoff_and_tolerates_garbage():
    text = (
        f"{_NOW}\torigin/claude/fresh\n"
        f"{_NOW - 10 * 86400}\torigin/claude/stale\n"
        "not-a-number\torigin/claude/bad-stamp\n"
        "\n"
        f"{_NOW}\n"  # stamp without a ref
    )
    refs = clo.parse_ref_lines(text, _NOW - 4 * 86400)
    assert refs == ["origin/claude/fresh"]


def test_load_remote_claims_reads_sibling_claim_and_tags_ref(monkeypatch):
    ls_tree_outputs = iter(
        [
            "docs/owner/claims/README.md\n",  # origin/main baseline
            # sibling tip adds one claim file beyond the baseline
            "docs/owner/claims/README.md\ndocs/owner/claims/claude__sibling.md\n",
        ],
    )

    def fake_git(args, timeout=60):
        if args[0] == "fetch":
            return ""
        if args[0] == "rev-parse":
            return "main\n"
        if args[0] == "for-each-ref":
            return f"{_NOW}\torigin/claude/sibling\n"
        if args[0] == "ls-tree":
            return next(ls_tree_outputs)
        if args[0] == "show":
            assert args[1] == "origin/claude/sibling:docs/owner/claims/claude__sibling.md"
            return "- `claude/sibling` · **lane S** · `scripts/s.py` · 2026-07-10 · PR\n"
        raise AssertionError(f"unexpected git call: {args}")

    monkeypatch.setattr(clo, "_git", fake_git)
    _freeze_now(monkeypatch)
    claims, warnings = clo.load_remote_claims(days=4, fetch=True)
    assert warnings == []
    assert len(claims) == 1
    assert claims[0]["ref"] == "origin/claude/sibling"
    assert claims[0]["branch"] == "claude/sibling"
    assert "scripts/s.py" in claims[0]["paths"]
    # And it folds into the standard scope scan, ref intact.
    hits = clo.scan_claims(["scripts/s.py"], claims)
    assert hits["scripts/s.py"][0]["ref"] == "origin/claude/sibling"


def test_load_remote_claims_skips_own_branch(monkeypatch):
    def fake_git(args, timeout=60):
        if args[0] == "rev-parse":
            return "claude/me\n"
        if args[0] == "for-each-ref":
            return f"{_NOW}\torigin/claude/me\n"
        if args[0] == "ls-tree":  # origin/main baseline only — own ref never inspected
            return "docs/owner/claims/README.md\n"
        raise AssertionError(f"unexpected git call: {args}")

    monkeypatch.setattr(clo, "_git", fake_git)
    _freeze_now(monkeypatch)
    claims, warnings = clo.load_remote_claims(days=4, fetch=False)
    assert claims == []
    assert warnings == []


def test_load_remote_claims_degrades_when_git_unavailable(monkeypatch):
    def fake_git(args, timeout=60):
        raise subprocess.SubprocessError("no git / offline")

    monkeypatch.setattr(clo, "_git", fake_git)
    claims, warnings = clo.load_remote_claims(days=4, fetch=True)
    assert claims == []
    assert len(warnings) == 2  # fetch failed + ref scan unavailable
    assert "fetch failed" in warnings[0]
    assert "local-only" in warnings[1]


def test_load_remote_claims_aggregates_uninspectable_refs(monkeypatch):
    ls_tree_outputs = iter(["docs/owner/claims/README.md\n", None])

    def fake_git(args, timeout=60):
        if args[0] == "rev-parse":
            return "main\n"
        if args[0] == "for-each-ref":
            return f"{_NOW}\torigin/claude/broken\n"
        if args[0] == "ls-tree":
            out = next(ls_tree_outputs)
            if out is None:  # the broken ref (e.g. shallow-clone miss)
                raise subprocess.SubprocessError("bad object")
            return out
        raise AssertionError(f"unexpected git call: {args}")

    monkeypatch.setattr(clo, "_git", fake_git)
    _freeze_now(monkeypatch)
    claims, warnings = clo.load_remote_claims(days=4, fetch=False)
    assert claims == []
    assert len(warnings) == 1
    assert "could not inspect 1 ref(s)" in warnings[0]
    assert "origin/claude/broken" in warnings[0]
