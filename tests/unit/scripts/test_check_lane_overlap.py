"""Tests for scripts/check_lane_overlap.py — the active-work.md claim-ledger scan.

The claim scan closes the gap that let a duplicate reaction-roles PR 2 get built:
the merged-commit scan structurally cannot see a claim that exists *before* any PR
or commit. These cover the pure parse + overlap logic (no git, no real file).
"""

from __future__ import annotations

import importlib.util
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
