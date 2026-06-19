"""Tests for ``scripts/check_plan_backlog.py`` — the Q-0164 PLAN-BACKLOG-THIN reporter.

Fixtures are synthetic band-plan markdown written into a tmp planning dir, so the tests never
depend on the live, mutable ``reconciliation-pass-*.md`` files.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_plan_backlog.py"

_spec = importlib.util.spec_from_file_location("check_plan_backlog", _MOD)
assert _spec and _spec.loader
cpb = importlib.util.module_from_spec(_spec)
sys.modules["check_plan_backlog"] = cpb
_spec.loader.exec_module(cpb)


# --- synthetic band-plan fixtures --------------------------------------------------------

_PLAN_RICH = """# Reconciliation pass — band-#1200

> **Status:** `plan`

## 1. Verified state

Prose with a stray `ready` mention that must NOT be counted (no slice row).

## 4. The next band — buildable, highest-value first

> Gate-state tags: `ready` · `creds` · `owner` · `plan-first` · `data`.

**Lane A — flagship (all `ready`):**

| # | Slice | Scope anchor |
|---|---|---|
| A1 | **Do the first thing** | anchor |
| A2 | **Do the second thing** | anchor |

**Lane B — gated work:**

| # | Slice | Gate | Scope anchor |
|---|---|---|---|
| B1 | **A creds thing** | `creds` | anchor |
| B2 | **An owner thing** | `owner` | anchor |
| B3 | **A ready thing despite the lane** | `ready` | anchor |

**Lane C — small guards (ungated, `plan-first` → then `ready`):**

| # | Slice | Scope anchor |
|---|---|---|
| C1 | **A plan-first thing** | anchor |

**Depth check (Q-0164):** Lanes A–C total **~18–22 genuine `ready`/`plan-first` slices** —
enough buildable work to reach #1230. **No `⚠️ PLAN BACKLOG THIN` flag this pass.**

## 5. Pruned / fixed

done.
"""

_PLAN_THIN = """# Reconciliation pass — band-#900

> **Status:** `plan`

## 4. The next band

**Lane A — what's left (mostly gated):**

| # | Slice | Gate | Scope anchor |
|---|---|---|---|
| A1 | **The one ungated thing** | `ready` | anchor |
| A2 | **A creds-blocked thing** | `creds` | anchor |
| A3 | **An owner-blocked thing** | `owner` | anchor |
| A4 | **A data-blocked thing** | `data` | anchor |

**Depth check (Q-0164):** only **3 genuine `ready` slices** — short of the band.

## 5. Done
"""

_PLAN_HISTORICAL = """# Old pass — band-#1500

> **Status:** `historical`

## 4. The next band

**Lane A — stuff (`ready`):**

| # | Slice | Scope anchor |
|---|---|---|
| A1 | **old** | anchor |
"""


def _write(planning_dir: Path, name: str, body: str) -> Path:
    path = planning_dir / name
    path.write_text(body, encoding="utf-8")
    return path


# --- find_live_band_plan -----------------------------------------------------------------


def test_find_live_band_plan_picks_highest_band_plan(tmp_path: Path) -> None:
    _write(tmp_path, "reconciliation-pass-2026-01-01-band900.md", _PLAN_THIN)
    newest = _write(tmp_path, "reconciliation-pass-2026-02-01-band1200.md", _PLAN_RICH)
    assert cpb.find_live_band_plan(tmp_path) == newest


def test_find_live_band_plan_skips_historical(tmp_path: Path) -> None:
    # A higher band number, but `historical` — must be ignored in favour of the live one.
    _write(tmp_path, "reconciliation-pass-2026-03-01-band1500.md", _PLAN_HISTORICAL)
    live = _write(tmp_path, "reconciliation-pass-2026-02-01-band1200.md", _PLAN_RICH)
    assert cpb.find_live_band_plan(tmp_path) == live


def test_find_live_band_plan_none_when_empty(tmp_path: Path) -> None:
    assert cpb.find_live_band_plan(tmp_path) is None


def test_find_live_band_plan_ignores_non_band_files(tmp_path: Path) -> None:
    _write(tmp_path, "reconciliation-pass-2026-02-01-q0107.md", _PLAN_RICH)
    assert cpb.find_live_band_plan(tmp_path) is None


# --- section + slice parsing -------------------------------------------------------------


def test_next_band_lines_bounded_by_section_4(tmp_path: Path) -> None:
    lines = cpb._next_band_lines(_PLAN_RICH)
    joined = "\n".join(lines)
    assert "Lane A — flagship" in joined
    assert "Depth check" in joined
    # Must stop at `## 5.` — the pruned section's content is excluded.
    assert "Pruned / fixed" not in joined
    # Must start after `## 4.` — the §1 prose `ready` mention is excluded.
    assert "stray `ready` mention" not in joined


def test_parse_slices_classifies_lane_and_row_tags() -> None:
    slices = cpb.parse_slices(cpb._next_band_lines(_PLAN_RICH))
    by_id = {s.slice_id: s for s in slices}
    # All six lane-slice rows are found; the §1 prose `ready` is not a row.
    assert set(by_id) == {"A1", "A2", "B1", "B2", "B3", "C1"}
    # Lane A inherits `ready` from its header.
    assert by_id["A1"].classification == "buildable"
    assert by_id["A2"].classification == "buildable"
    # Lane B rows carry their own gate column.
    assert by_id["B1"].classification == "gated"  # creds
    assert by_id["B2"].classification == "gated"  # owner
    assert by_id["B3"].classification == "buildable"  # row `ready` overrides the gated lane
    # Lane C header has both plan-first and ready → buildable.
    assert by_id["C1"].classification == "buildable"


def test_classify_untagged_defaults_buildable() -> None:
    # The §4 convention: "every slot is a real, ungated slice unless tagged".
    assert cpb._classify(set(), set()) == "buildable"


def test_classify_row_tag_overrides_lane_tag() -> None:
    assert cpb._classify({"ready"}, {"creds"}) == "buildable"
    assert cpb._classify({"data"}, {"ready"}) == "gated"


# --- stated-depth parsing (the anchored, lower-bound, noise-resistant read) ---------------


def test_parse_stated_depth_reads_range_lower_bound() -> None:
    depth = cpb.parse_stated_depth(cpb._next_band_lines(_PLAN_RICH))
    assert depth == 18  # the lower bound of "~18–22", not 22 and not a stray number


def test_parse_stated_depth_ignores_pr_and_q_numbers() -> None:
    # "#1230" and "Q-0164" share the depth-check window; only the slices-anchored count counts.
    depth = cpb.parse_stated_depth(cpb._next_band_lines(_PLAN_RICH))
    assert depth not in (1230, 164, 1164, 22)


def test_parse_stated_depth_single_count() -> None:
    depth = cpb.parse_stated_depth(cpb._next_band_lines(_PLAN_THIN))
    assert depth == 3


def test_parse_stated_depth_none_when_absent() -> None:
    body = "## 4. band\n\n| # | Slice |\n|---|---|\n| A1 | x |\n"
    assert cpb.parse_stated_depth(cpb._next_band_lines(body)) is None


# --- build_report end to end -------------------------------------------------------------


def test_build_report_rich_is_not_thin(tmp_path: Path) -> None:
    plan = _write(tmp_path, "reconciliation-pass-2026-02-01-band1200.md", _PLAN_RICH)
    report = cpb.build_report(plan_path=plan)
    assert report.band == 1200
    assert report.buildable_rows == 4  # A1, A2, B3, C1
    assert report.gated_rows == 2  # B1, B2
    assert report.total_rows == 6
    assert report.stated_depth == 18
    assert report.effective_depth == 18  # max(4 rows, 18 stated)
    assert report.thin is False  # 18 >= default threshold 15


def test_build_report_thin_when_buildable_short(tmp_path: Path) -> None:
    plan = _write(tmp_path, "reconciliation-pass-2026-01-01-band900.md", _PLAN_THIN)
    report = cpb.build_report(plan_path=plan)
    assert report.buildable_rows == 1  # only A1 is `ready`
    assert report.gated_rows == 3  # creds, owner, data
    assert report.stated_depth == 3
    assert report.effective_depth == 3  # max(1, 3)
    assert report.thin is True  # 3 < default threshold 15


def test_build_report_effective_depth_prefers_row_floor(tmp_path: Path) -> None:
    # When there is NO stated depth-check, the buildable row count carries the verdict.
    body = (
        "> **Status:** `plan`\n\n## 4. band\n\n"
        "**Lane A — work (`ready`):**\n\n| # | Slice |\n|---|---|\n"
        + "".join(f"| A{i} | thing {i} |\n" for i in range(1, 17))
        + "\n## 5. done\n"
    )
    plan = _write(tmp_path, "reconciliation-pass-2026-02-01-band1230.md", body)
    report = cpb.build_report(plan_path=plan)
    assert report.buildable_rows == 16
    assert report.stated_depth is None
    assert report.effective_depth == 16
    assert report.thin is False  # 16 >= 15


def test_build_report_custom_threshold(tmp_path: Path) -> None:
    plan = _write(tmp_path, "reconciliation-pass-2026-02-01-band1200.md", _PLAN_RICH)
    # Demand a full-cadence band: 18 < 30 → THIN.
    report = cpb.build_report(plan_path=plan, threshold=cpb.STEP)
    assert report.threshold == 30
    assert report.thin is True


def test_build_report_no_plan(tmp_path: Path) -> None:
    report = cpb.build_report(planning_dir=tmp_path)
    assert report.plan_path is None
    assert report.thin is False
    assert report.effective_depth == 0


# --- main / CLI --------------------------------------------------------------------------


def test_main_advisory_exit_zero_even_when_thin(monkeypatch) -> None:
    monkeypatch.setattr(
        cpb,
        "build_report",
        lambda threshold=cpb.MIN_BUILDABLE_DEFAULT: cpb.BacklogReport(
            plan_path=_MOD,  # any path; only used for display
            band=900,
            buildable_rows=1,
            gated_rows=3,
            total_rows=4,
            stated_depth=3,
            effective_depth=3,
            threshold=threshold,
            thin=True,
            slices=(),
        ),
    )
    assert cpb.main([]) == 0  # warn-only default never fails
    assert cpb.main(["--strict"]) == 1  # strict gates on THIN


def test_main_not_thin_exits_zero(monkeypatch) -> None:
    monkeypatch.setattr(
        cpb,
        "build_report",
        lambda threshold=cpb.MIN_BUILDABLE_DEFAULT: cpb.BacklogReport(
            plan_path=_MOD,
            band=1200,
            buildable_rows=4,
            gated_rows=2,
            total_rows=6,
            stated_depth=18,
            effective_depth=18,
            threshold=threshold,
            thin=False,
            slices=(),
        ),
    )
    assert cpb.main(["--strict"]) == 0


def test_main_no_plan_exits_zero(monkeypatch) -> None:
    monkeypatch.setattr(
        cpb,
        "build_report",
        lambda threshold=cpb.MIN_BUILDABLE_DEFAULT: cpb.BacklogReport(
            plan_path=None,
            band=None,
            buildable_rows=0,
            gated_rows=0,
            total_rows=0,
            stated_depth=None,
            effective_depth=0,
            threshold=threshold,
            thin=False,
            slices=(),
        ),
    )
    assert cpb.main(["--strict"]) == 0


def test_main_json_mode(monkeypatch, capsys) -> None:
    import json

    monkeypatch.setattr(
        cpb,
        "build_report",
        lambda threshold=cpb.MIN_BUILDABLE_DEFAULT: cpb.BacklogReport(
            plan_path=_MOD,
            band=1200,
            buildable_rows=4,
            gated_rows=2,
            total_rows=6,
            stated_depth=18,
            effective_depth=18,
            threshold=threshold,
            thin=False,
            slices=(),
        ),
    )
    assert cpb.main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["band"] == 1200
    assert payload["effective_depth"] == 18
    assert payload["thin"] is False
    assert payload["cadence"] == cpb.STEP


def test_min_buildable_default_below_cadence() -> None:
    # The default threshold demands a margin, not a full band (so it agrees with the planner's
    # own lived non-THIN judgment), and is still a positive depth.
    assert 0 < cpb.MIN_BUILDABLE_DEFAULT < cpb.STEP


def test_step_matches_reconciliation_cadence() -> None:
    # The cadence must stay identical to the reconciliation-due guard's band size.
    crd_mod = REPO_ROOT / "scripts" / "check_reconciliation_due.py"
    spec = importlib.util.spec_from_file_location("check_reconciliation_due_for_cpb", crd_mod)
    assert spec and spec.loader
    crd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(crd)
    assert cpb.STEP == crd.STEP


def test_live_repo_plan_runs_and_is_consistent() -> None:
    """Smoke test against the live repo: the script must run, find a plan, and its default
    verdict must NOT contradict that plan's own stated PLAN-BACKLOG-THIN judgment (Q-0120)."""
    report = cpb.build_report()
    if report.plan_path is None:
        return  # no live band plan in this checkout — nothing to assert
    text = report.plan_path.read_text(encoding="utf-8")
    if "No `⚠️ PLAN BACKLOG THIN`" in text or "No ⚠️ PLAN BACKLOG THIN" in text:
        # The live plan explicitly declared itself NOT thin — the tool must agree by default.
        assert report.thin is False, (
            "default verdict contradicts the live plan's own 'No PLAN BACKLOG THIN' "
            "declaration (Q-0120: a tool that fights the evidence is the tool's bug)"
        )
